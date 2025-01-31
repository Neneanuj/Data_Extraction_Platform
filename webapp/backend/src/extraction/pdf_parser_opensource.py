import os
import tempfile
from typing import Dict, Any
import requests
import fitz  # PyMuPDF
import pdfplumber
import csv
import shutil

from standardization.docling_utils import docling_convert 
from standardization.markitdown_utils import markitdown_convert

def process_pdf_with_open_source(pdf_source: str) -> Dict[str, Any]:
    """
    Parse PDF and return:
      - "docling_markdown": the string after docling conversion
      - "markitdown_markdown": the string after markitdown conversion
      - "images_dir": the directory where images are extracted
      - "tables_dir": the directory where tables (CSV) are extracted
    """
    # If the input is a remote URL, download it to a local temporary file
    if pdf_source.lower().startswith("http"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            response = requests.get(pdf_source)
            tmp.write(response.content)
            pdf_path = tmp.name
    else:
        # If it is a local file, use it directly
        pdf_path = pdf_source

    # Extract images to a temporary folder
    images_dir = tempfile.mkdtemp()
    _extract_images(pdf_path, images_dir)

    # Extract tables to a temporary folder
    tables_dir = tempfile.mkdtemp()
    _extract_tables(pdf_path, tables_dir)

    # Extract pure text
    text_content = _extract_text_only(pdf_path)

    # Optionally, if you want to delete the temporary PDF, you can do it here
    # However, if the pdf_source was a local file, it may not need to be deleted. This depends on the scenario.
    if pdf_source.lower().startswith("http"):
        os.remove(pdf_path)

    # Write this text to a temporary .md file for docling/markitdown parsing
    with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as tmp_file:
        tmp_file.write(text_content.encode("utf-8"))
        tmp_file_path = tmp_file.name

    docling_md = docling_convert(tmp_file_path)
    os.remove(tmp_file_path)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file2:
        tmp_file2.write(text_content.encode("utf-8"))
        tmp_path_txt2 = tmp_file2.name

    markitdown_md = markitdown_convert(tmp_path_txt2)
    os.remove(tmp_path_txt2)

    # Return relevant information
    return {
        "docling_markdown": docling_md,
        "markitdown_markdown": markitdown_md,
        "images_dir": images_dir,
        "tables_dir": tables_dir
    }

def _extract_images(pdf_path: str, output_dir: str):
    """Extract all images using PyMuPDF to a specified directory"""
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_ext = base_image["ext"]
            image_filename = f"page{page_num+1}_img{img_index+1}.{image_ext}"
            image_path = os.path.join(output_dir, image_filename)
            with open(image_path, "wb") as f:
                f.write(base_image["image"])
    doc.close()

def _extract_tables(pdf_path: str, output_dir: str):
    """Extract tables using pdfplumber into CSV files"""
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            print(f"Page {page_num+1} - tables found: {len(tables)}")  # Displaying the number of tables found
            for t_idx, table in enumerate(tables):
                csv_filename = f"page{page_num+1}_table{t_idx+1}.csv"
                csv_path = os.path.join(output_dir, csv_filename)
                with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerows(table)

def _extract_text_only(pdf_path: str) -> str:
    """Extract text using pdfplumber and concatenate into a single string"""
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.append(text.strip())
    return "\n".join(lines)
