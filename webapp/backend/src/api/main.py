import os
import sys
import tempfile
import zipfile
import io
import shutil
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import uvicorn
import tempfile
from typing import Dict, Any
from S3.s3_organization import upload_to_s3, generate_s3_key, generate_presigned_url
from extraction.pdf_parser_enterprise import extract_and_store_pdf
from extraction.pdf_parser_opensource import process_pdf_with_open_source
from extraction.web_scraper import scrape_url_and_convert

app = FastAPI()
print(os.path.abspath(__file__))

@app.post("/upload_pdf_enterprise")
async def process_pdf(
    file: UploadFile = File(...),
    bucket_name: str = Form(default="bigdata-project1-storage")
) -> Dict[str, Any]:
    try:
        # Temporarily save the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Upload to S3 raw storage
        s3_key = generate_s3_key(file_type="pdf", file_name=file.filename)
        upload_to_s3(bucket_name, s3_key, tmp_path)

        # Call the processing function (no need to pass base_key anymore)
        result = extract_and_store_pdf(pdf_path=s3_key, bucket_name=bucket_name)

        # Clean up temporary files
        os.remove(tmp_path)

        return {
            "status": "success",
            "download_url": result["download_url"],
            "message": "Data has been stored to S3 according to the rules, and can be downloaded via the link as a complete ZIP file"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/upload_pdf_opensource")
async def upload_pdf_opensource(
    file: UploadFile = File(...),
    bucket_name: str = Form(default="bigdata-project1-storage")
) -> Dict[str, Any]:

    # 1. Save the uploaded PDF to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        content = await file.read()
        tmp_pdf.write(content)
        pdf_path = tmp_pdf.name

    # 2. Call the parsing function -> Obtain two md texts + images_dir + tables_dir
    parsed = process_pdf_with_open_source(pdf_path)

    # 3. Create an in-memory ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Two Markdown files
        zf.writestr("docling.md", parsed["docling_markdown"])
        zf.writestr("markitdown.md", parsed["markitdown_markdown"])

        # Image directory
        if os.path.exists(parsed["images_dir"]):
            for root, _, files in os.walk(parsed["images_dir"]):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    zip_path = os.path.join("images", file_name)
                    zf.write(file_path, zip_path)

        # Table directory
        if os.path.exists(parsed["tables_dir"]):
            for root, _, files in os.walk(parsed["tables_dir"]):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    zip_path = os.path.join("tables", file_name)
                    zf.write(file_path, zip_path)

    # 4. Clean up temporary directories/files
    os.remove(pdf_path)
    shutil.rmtree(parsed["images_dir"], ignore_errors=True)
    shutil.rmtree(parsed["tables_dir"], ignore_errors=True)

    # 5. Upload the ZIP to S3
    zip_key = generate_s3_key("pdf/opensource", file.filename) + "_result.zip"
    zip_buffer.seek(0)
    upload_to_s3(bucket_name, zip_key, zip_buffer.getvalue())

    # 6. Return a presigned download link
    download_url = generate_presigned_url(bucket_name, zip_key)
    return {
        "status": "success",
        "download_url": download_url,
        "message": "ZIP contains two Markdown texts, as well as extracted images and tables."
    }
