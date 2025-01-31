import boto3
from botocore.exceptions import ClientError
from typing import Union
from datetime import datetime

def generate_presigned_url(bucket: str, key: str, expiration=3600) -> str:
    """Generate a presigned URL for downloading from S3 with enterprise-level security configuration."""
    s3_client = boto3.client('s3', config=boto3.session.Config(signature_version='s3v4'))
    try:
        return s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiration
        )
    except ClientError as e:
        raise RuntimeError(f"Failed to generate presigned URL: {str(e)}")

def upload_to_s3(bucket_name: str, s3_key: str, data: Union[bytes, str]) -> None:
    """
    Upload a file or byte data to a specified S3 bucket.

    :param bucket_name: The name of the target S3 bucket
    :param s3_key: The target key (path) in S3
    :param data: Can be either a file path (str) or byte data (bytes)
    """
    try:
        s3 = boto3.client('s3')
        if isinstance(data, bytes):
            # Handle byte data
            s3.put_object(Bucket=bucket_name, Key=s3_key, Body=data)
        else:
            # Handle file path
            s3.upload_file(Filename=data, Bucket=bucket_name, Key=s3_key)
    except Exception as e:
        raise Exception(f"Failed to upload to S3: {str(e)}")

def generate_s3_key(file_type: str, file_name: str) -> str:
    """
    Generate an S3 key for storing files.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{file_type}/{timestamp}_{file_name}"

def download_from_s3(bucket_name: str, object_name: str, file_path: str) -> None:
    """
    Download a file from an S3 bucket.
    """
    s3_client = boto3.client('s3')
    try:
        s3_client.download_file(bucket_name, object_name, file_path)
    except Exception as e:
        raise Exception(f"Failed to download from S3: {str(e)}")
