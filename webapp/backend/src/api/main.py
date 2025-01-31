import os
import sys
import tempfile
import zipfile
import io
import shutil
import pandas as pd

# Add the parent directory to sys.path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import FastAPI and necessary modules
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import uvicorn
from typing import Dict, Any

# Import custom modules for S3 operations and data extraction
from S3.s3_organization import upload_to_s3, generate_s3_key, generate_presigned_url
from extraction.pdf_parser_enterprise import extract_and_store_pdf
from extraction.pdf_parser_opensource import process_pdf_with_open_source
from extraction.web_scraper import scrape_url_and_convert

# Initialize FastAPI application
app = FastAPI()
print(os.path.abspath(__file__))

@app.post("/upload_pdf_enterprise")
async def process_pdf(
    file: UploadFile = File(...),
    bucket_name: str = Form(default="bigdata-project1-storage")
) -> Dict[str, Any]:
    """
    Endpoint to process an uploaded PDF using an enterprise parser.
    Steps:
    1. Save the uploaded PDF to a temporary file.
    2. Upload the original PDF to S3.
    3. Extract and store data from the PDF.
    4. Remove the temporary file.
    5. Return the download link for the processed data.
    """
    try:
        # Save uploaded PDF to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Generate S3 key and upload the original PDF
        s3_key = generate_s3_key(file_type="pdf", file_name=file.filename)
        upload_to_s3(bucket_name, s3_key, tmp_path)

        # Process the PDF and store results in S3
        result = extract_and_store_pdf(pdf_path=s3_key, bucket_name=bucket_name)

        # Remove the temporary file
        os.remove(tmp_path)

        return {
            "status": "success",
            "download_url": result["download_url"],
            "message": "Data has been stored in S3. You can download the complete ZIP file using the link."
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/upload_pdf_opensource")
async def upload_pdf_opensource(
    file: UploadFile = File(...),
    bucket_name: str = Form(default="bigdata-project1-storage")
) -> Dict[str, Any]:
    """
    Endpoint to process a PDF using an open-source parser.
    Steps:
    1. Save the uploaded PDF to a temporary file.
    2. Process the PDF to extract markdown files, images, and tables.
    3. Create a ZIP archive in memory with extracted content.
    4. Upload the ZIP archive to S3.
    5. Return the download link for the ZIP archive.
    """
    # Save uploaded PDF to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        content = await file.read()
        tmp_pdf.write(content)
        pdf_path = tmp_pdf.name

    # Process the PDF to extract content
    parsed = process_pdf_with_open_source(pdf_path)

    # Create an in-memory ZIP archive
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add extracted markdown files
        zf.writestr("docling.md", parsed["docling_markdown"])
        zf.writestr("markitdown.md", parsed["markitdown_markdown"])

        # Add extracted images
        if os.path.exists(parsed["images_dir"]):
            for root, _, files in os.walk(parsed["images_dir"]):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    zip_path = os.path.join("images", file_name)
                    zf.write(file_path, zip_path)

        # Add extracted tables
        if os.path.exists(parsed["tables_dir"]):
            for root, _, files in os.walk(parsed["tables_dir"]):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    zip_path = os.path.join("tables", file_name)
                    zf.write(file_path, zip_path)

    # Remove temporary files and directories
    os.remove(pdf_path)
    shutil.rmtree(parsed["images_dir"], ignore_errors=True)
    shutil.rmtree(parsed["tables_dir"], ignore_errors=True)

    # Upload the ZIP archive to S3
    zip_key = generate_s3_key("pdf/opensource", file.filename) + "_result.zip"
    zip_buffer.seek(0)
    upload_to_s3(bucket_name, zip_key, zip_buffer.getvalue())

    # Generate a presigned URL for downloading the ZIP archive
    download_url = generate_presigned_url(bucket_name, zip_key)
    return {
        "status": "success",
        "download_url": download_url,
        "message": "ZIP contains two Markdown files, extracted images, and tables."
    }

@app.post("/scrape_webpage")
async def scrape_webpage(
    url: str = Form(...),
    bucket_name: str = Form(default="bigdata-project1-storage")
) -> Dict[str, Any]:
    """
    Web scraping endpoint to:
    1. Scrape webpage content including text, images, tables, and links.
    2. Convert extracted content to Markdown files.
    3. Package extracted data into a ZIP archive.
    4. Upload the ZIP archive to S3.
    5. Return the download link for the ZIP archive.
    """
    # Perform web scraping and extract data
    result = scrape_url_and_convert(url)
    if result["error"]:
        return {"status": "error", "message": result["error"]}

    docling_md = result["docling_markdown"]
    markitdown_md = result["markitdown_markdown"]
    text_raw = result["text_raw"]
    images_data = result["images"]
    tables_data = result["tables"]
    urls_data = result["urls"]

    # Create an in-memory ZIP archive
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add extracted Markdown files
        zf.writestr("docling.md", docling_md)
        zf.writestr("markitdown.md", markitdown_md)

        # Add extracted raw text
        zf.writestr("content.txt", text_raw)

        # Add extracted tables as CSV files
        if tables_data:
            for i, df in enumerate(tables_data, start=1):
                csv_name = f"tables/table_{i}.csv"
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                zf.writestr(csv_name, csv_buffer.getvalue())
        else:
            zf.writestr("tables/.placeholder", "")

        # Add extracted images metadata
        if images_data:
            df_images = pd.DataFrame(images_data)
            csv_buf = io.StringIO()
            df_images.to_csv(csv_buf, index=False)
            zf.writestr("images/images_metadata.csv", csv_buf.getvalue())
        else:
            zf.writestr("images/.placeholder", "")

        # Add extracted URLs metadata
        if urls_data:
            df_urls = pd.DataFrame(urls_data)
            csv_buf = io.StringIO()
            df_urls.to_csv(csv_buf, index=False)
            zf.writestr("urls/urls_metadata.csv", csv_buf.getvalue())
        else:
            zf.writestr("urls/.placeholder", "")

    # Upload the ZIP archive to S3
    zip_key = generate_s3_key("web_scraper", "result") + ".zip"
    zip_buffer.seek(0)
    upload_to_s3(bucket_name, zip_key, zip_buffer.getvalue())

    # Generate a presigned URL for downloading the ZIP archive
    download_url = generate_presigned_url(bucket_name, zip_key)
    return {
        "status": "success",
        "download_url": download_url,
        "message": "ZIP contains Markdown files, extracted text, images, tables, and links metadata."
    }

# Run FastAPI server when script is executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
