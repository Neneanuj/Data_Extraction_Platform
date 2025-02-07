import os
import sys
import tempfile
import zipfile
import io
import shutil
import pandas as pd

from datetime import datetime
import json
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
from extraction.web_scraper_enterprise import scrape_url_with_diffbot


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
    """
    pdf_path = None
    parsed = None
    try:
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

    except Exception as e:
        # Cleanup temporary resources in case of error
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)
        if parsed:
            images_dir = parsed.get("images_dir")
            if images_dir and os.path.exists(images_dir):
                shutil.rmtree(images_dir, ignore_errors=True)
            tables_dir = parsed.get("tables_dir")
            if tables_dir and os.path.exists(tables_dir):
                shutil.rmtree(tables_dir, ignore_errors=True)
        # Return JSON error response
        return {"status": "error", "message": str(e)}

@app.post("/scrape_webpage")
async def scrape_webpage(
    url: str = Form(...),
    bucket_name: str = Form(default="bigdata-project1-storage")
) -> Dict[str, Any]:
    """
    Web scraping API endpoint:
    1. Scrapes the webpage and extracts text, images, tables, and links.
    2. Converts extracted content to Markdown and other formats.
    3. Packages data into a ZIP file and uploads it to S3.
    4. Returns a downloadable S3 link.
    """
    try:
        # Step 1: Scrape the webpage
        result = scrape_url_and_convert(url)
        if not result or result.get("error"):
            return {"status": "error", "message": result.get("error", "Unknown error occurred")}

        # Step 2: Prepare data for ZIP file
        docling_md = result.get("docling_markdown", "")
        markitdown_md = result.get("markitdown_markdown", "")
        text_raw = result.get("text_raw", "")
        images_data = result.get("images", [])
        tables_data = result.get("tables", [])
        urls_data = result.get("urls", [])

        # Step 3: Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("docling.md", docling_md)
            zf.writestr("markitdown.md", markitdown_md)
            zf.writestr("content.txt", text_raw)

            if tables_data:
                for i, df in enumerate(tables_data, start=1):
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    zf.writestr(f"tables/table_{i}.csv", csv_buffer.getvalue())
            else:
                zf.writestr("tables/.placeholder", "")

            if images_data:
                df_images = pd.DataFrame(images_data)
                csv_buf = io.StringIO()
                df_images.to_csv(csv_buf, index=False)
                zf.writestr("images/images_metadata.csv", csv_buf.getvalue())
            else:
                zf.writestr("images/.placeholder", "")

            if urls_data:
                df_urls = pd.DataFrame(urls_data)
                csv_buf = io.StringIO()
                df_urls.to_csv(csv_buf, index=False)
                zf.writestr("urls/urls_metadata.csv", csv_buf.getvalue())
            else:
                zf.writestr("urls/.placeholder", "")

        # Step 4: Upload ZIP to S3
        file_type = "web_scraper/opensource"
        file_name = "result.zip"
        zip_key = generate_s3_key(file_type=file_type, file_name=file_name)
        zip_buffer.seek(0)
        upload_to_s3(bucket_name, zip_key, zip_buffer.getvalue())

        # Step 5: Generate presigned S3 URL
        download_url = generate_presigned_url(bucket_name, zip_key)

        return {
            "status": "success",
            "download_url": download_url,
            "message": "The ZIP archive has been stored in S3 and is available for download."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }





@app.post("/scrape_diffbot")
async def scrape_diffbot(
    url: str = Form(...),
    bucket_name: str = Form(default="bigdata-project1-storage")
) -> Dict[str, Any]:
    """
    Endpoint to scrape a webpage using the Diffbot API.

    Steps:
    1. Fetch webpage content using Diffbot API.
    2. Save the scraped content into a markdown file.
    3. Compress the markdown file into a ZIP archive.
    4. Upload the ZIP archive to S3 under 'web_scraper/enterprise/'.
    5. Return a downloadable S3 link for the ZIP file.

    Parameters:
    - url (str): The webpage URL to be scraped.
    - bucket_name (str): The S3 bucket where the output file will be stored.

    Returns:
    - JSON response with status, message, and a download link if successful.
    """
    try:
        # Step 1: Scrape the webpage using Diffbot API
        data = scrape_url_with_diffbot(url)

        # Handle potential errors from the scraping function
        if "error" in data:
            return {"status": "error", "message": data["error"]}

        # Step 2: Format scraped data into Markdown
        markdown_content = f"# Scraped Data Report\n\n"
        markdown_content += f"## Source URL\n{url}\n\n"
        markdown_content += f"## Timestamp\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        markdown_content += "## Extracted Content\n"
        markdown_content += "```\n"
        markdown_content += json.dumps(data, indent=2)
        markdown_content += "\n```\n"

        # Step 3: Create an in-memory ZIP archive
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add the Markdown file into the ZIP
            zf.writestr("scraped_data.md", markdown_content)

        # Step 4: Define S3 upload path
        s3_prefix = "web_scraper/enterprise"
        
        # Generate a unique S3 key for the ZIP file
        zip_filename = "scraped_data.zip"
        zip_key = generate_s3_key(file_type=s3_prefix, file_name=zip_filename)

        # Step 5: Upload ZIP file to S3
        zip_buffer.seek(0)
        upload_to_s3(bucket_name, zip_key, zip_buffer.getvalue())

        # Step 6: Generate a presigned URL for downloading the ZIP file
        download_url = generate_presigned_url(bucket_name, zip_key)

        return {
            "status": "success",
            "download_url": download_url,
            "message": "Scraped data has been stored in S3. You can download the markdown file using the provided link."
        }

    except Exception as e:
        # Handle unexpected errors
        return {"status": "error", "message": str(e)}

# Run FastAPI server when script is executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
