import os
import json
import zipfile
import boto3
import logging
from io import BytesIO
from datetime import datetime

# Correct import from Adobe PDF Services
from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.exception.exceptions import ServiceApiException, ServiceUsageException, SdkException
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
from adobe.pdfservices.operation.io.stream_asset import StreamAsset
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdfjobs.jobs.extract_pdf_job import ExtractPDFJob
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_element_type import ExtractElementType
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_renditions_element_type import ExtractRenditionsElementType
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_pdf_params import ExtractPDFParams
from adobe.pdfservices.operation.pdfjobs.result.extract_pdf_result import ExtractPDFResult

from dotenv import load_dotenv

if os.getenv("ENV_MODE") != "production":
    load_dotenv()
logging.basicConfig(level=logging.INFO)

def generate_s3_base_key(pdf_path: str) -> str:
    """Generate a base S3 path based on the PDF path"""
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    return f"pdf/enterprise/{pdf_name}/"

def upload_to_s3(bucket_name: str, s3_key: str, data: bytes):
    """Upload byte stream directly to S3"""
    s3_client = boto3.client("s3")
    s3_client.put_object(Bucket=bucket_name, Key=s3_key, Body=data)

def create_presigned_url(bucket_name: str, object_key: str, expiration=3600) -> str:
    """Generate a presigned download URL"""
    s3_client = boto3.client('s3')
    return s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': object_key},
        ExpiresIn=expiration
    )

def extract_and_store_pdf(pdf_path: str, bucket_name: str):
    """Core processing logic"""
    base_key = generate_s3_base_key(pdf_path)
    s3_client = boto3.client("s3")

    try:
        # Retrieve PDF content from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=pdf_path)
        pdf_byte_data = response["Body"].read()

        # Initialize Adobe services
        credentials = ServicePrincipalCredentials(
            client_id=os.getenv('PDF_SERVICES_CLIENT_ID'),
            client_secret=os.getenv('PDF_SERVICES_CLIENT_SECRET')
        )
        pdf_services = PDFServices(credentials=credentials)

        # Upload byte data directly (following the official example)
        input_asset = pdf_services.upload(input_stream=pdf_byte_data, mime_type=PDFServicesMediaType.PDF)

        # Configure extraction parameters
        extract_pdf_params = ExtractPDFParams(
            elements_to_extract=[ExtractElementType.TEXT, ExtractElementType.TABLES],
            elements_to_extract_renditions=[ExtractRenditionsElementType.TABLES, ExtractRenditionsElementType.FIGURES]
        )

        # Submit the job
        extract_pdf_job = ExtractPDFJob(input_asset=input_asset, extract_pdf_params=extract_pdf_params)
        location = pdf_services.submit(extract_pdf_job)
        result = pdf_services.get_job_result(location, ExtractPDFResult)

        # Process the result (key fixing point)
        result_asset: CloudAsset = result.get_result().get_resource()
        stream_asset: StreamAsset = pdf_services.get_content(result_asset)
        
        # Directly get byte data, no need to call read()
        zip_data = stream_asset.get_input_stream()  # Removed .read()

        # Store the original ZIP
        raw_zip_key = f"{base_key}extracted_data.zip"
        upload_to_s3(bucket_name, raw_zip_key, zip_data)

        # Parse and categorize storage
        with zipfile.ZipFile(BytesIO(zip_data)) as archive:
            # ... subsequent processing remains unchanged ...

            return {"download_url": create_presigned_url(bucket_name, raw_zip_key)}

    except (ServiceApiException, ServiceUsageException, SdkException) as e:
        logging.error(f"Adobe API error: {str(e)}")
        raise RuntimeError(f"Document processing failed: {str(e)}")
    except Exception as e:
        logging.error(f"System error: {str(e)}")
        raise RuntimeError(f"System processing exception: {str(e)}")
