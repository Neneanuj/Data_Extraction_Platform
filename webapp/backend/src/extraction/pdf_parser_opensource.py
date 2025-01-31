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
    解析PDF并返回：
      - "docling_markdown": docling 转换后的字符串
      - "markitdown_markdown": markitdown 转换后的字符串
      - "images_dir": 提取出的图片所在目录
      - "tables_dir": 提取出的表格(CSV)所在目录
    """
    # 0. 如果传入的是远程 URL，则下载到本地临时文件
    if pdf_source.lower().startswith("http"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            response = requests.get(pdf_source)
            tmp.write(response.content)
            pdf_path = tmp.name
    else:
        # 如果是本地文件，就直接使用
        pdf_path = pdf_source

    # 1. 提取图片到临时文件夹
    images_dir = tempfile.mkdtemp()
    _extract_images(pdf_path, images_dir)

    # 2. 提取表格到临时文件夹
    tables_dir = tempfile.mkdtemp()
    _extract_tables(pdf_path, tables_dir)

    # 3. 提取纯文本
    text_content = _extract_text_only(pdf_path)

    # (可选) 如果想删掉临时PDF，这里可以操作
    # 但如果pdf_source原本就是本地文件，可能不必删。视场景而定。
    if pdf_source.lower().startswith("http"):
        os.remove(pdf_path)

    # 4. 把这段文本写到临时 .txt 文件，方便 docling/markitdown 解析
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

    # 5. 返回相关信息
    return {
        "docling_markdown": docling_md,
        "markitdown_markdown": markitdown_md,
        "images_dir": images_dir,
        "tables_dir": tables_dir
    }

def _extract_images(pdf_path: str, output_dir: str):
    """使用 PyMuPDF 提取所有图片到指定目录"""
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
    """使用 pdfplumber 提取表格为 CSV 文件"""
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            print(f"Page {page_num+1} - tables found: {len(tables)}")
            for t_idx, table in enumerate(tables):
                csv_filename = f"page{page_num+1}_table{t_idx+1}.csv"
                csv_path = os.path.join(output_dir, csv_filename)
                with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerows(table)

def _extract_text_only(pdf_path: str) -> str:
    """使用 pdfplumber 仅提取文本，并拼成一个字符串"""
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.append(text.strip())
    return "\n".join(lines)
