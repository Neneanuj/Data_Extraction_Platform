import os
import tempfile
import requests
import csv
import pandas as pd
import pdfplumber
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re

# Import existing docling and markitdown conversion tools
from standardization.docling_utils import docling_convert
from standardization.markitdown_utils import markitdown_convert

def is_valid_url(url):
    """Validate URL format and accessibility"""
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False, "Invalid URL format. Please include http:// or https://"
        response = requests.head(url, timeout=5)
        return (True, None) if response.status_code == 200 else (False, f"URL returned status code: {response.status_code}")
    except requests.RequestException as e:
        return False, f"URL is not accessible: {str(e)}"
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"

def parse_url(url):
    """Fetch and parse HTML content"""
    valid, error_message = is_valid_url(url)
    if not valid:
        return None, error_message
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup, None
    except Exception as e:
        return None, f"Failed to parse URL: {str(e)}"

def extract_clean_text(soup):
    """Extract and clean text"""
    try:
        return re.sub(r'\s+', ' ', soup.get_text()).strip(), None
    except Exception:
        return None, "Text extraction failed"

def extract_urls(soup, base_url):
    """Extract URLs with metadata from HTML"""
    try:
        urls = []
        for i, link in enumerate(soup.find_all('a')):
            href = link.get('href')
            if href:
                urls.append({
                    'position': i + 1,
                    'url': urljoin(base_url, href),
                    'text': link.text.strip(),
                    'title': link.get('title', 'N/A')
                })
        return urls, None
    except Exception:
        return None, "URL extraction failed"

def extract_images(soup, base_url):
    """Extract images with metadata (NOT the actual image files, just info)"""
    try:
        images = []
        for i, img in enumerate(soup.find_all('img')):
            src = img.get('src', '')
            if not src:
                continue
            abs_src = urljoin(base_url, src)
            images.append({
                'position': i + 1,
                'alt': img.get('alt', '').strip(),
                'src': abs_src,
                'width': img.get('width', 'N/A'),
                'height': img.get('height', 'N/A')
            })
        return images, None
    except Exception:
        return None, "Image extraction failed"

def extract_tables(soup):
    """Extract tables from HTML (as DataFrame list)"""
    try:
        tables = []
        for table in soup.find_all('table'):
            headers = [th.text.strip() for th in table.find_all('th')]
            if not headers and table.find('tr'):
                headers = [f'Column_{i}' for i in range(len(table.find('tr').find_all('td')))]
            
            rows = []
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if tds and len(tds) == len(headers):
                    row_data = [td.text.strip() for td in tds]
                    rows.append(row_data)
            
            if rows:
                df = pd.DataFrame(rows, columns=headers)
                tables.append(df)
        return tables, None
    except Exception:
        return None, "Table extraction failed"

def scrape_url_and_convert(url: str):
    """
    Publicly exposed scraping and conversion function:
    1) Parse URL -> Extract text, images, tables, and links
    2) Convert extracted text into docling.md and markitdown.md
    Returns:
    {
      "docling_markdown": str,
      "markitdown_markdown": str,
      "text_raw": str,    # Optionally, saves the original extracted text
      "images": [...],    # Metadata of images
      "tables": [DataFrame1, DataFrame2, ...],
      "urls": [...],      # Metadata of links
      "error": None or "xxxxx"
    }
    """
    soup, error = parse_url(url)
    if error:
        return {"error": error}

    # Extract text
    text_data, err_text = extract_clean_text(soup)
    if err_text:
        return {"error": err_text}

    # Extract URLs
    urls_data, err_urls = extract_urls(soup, url)
    if err_urls:
        urls_data = []

    # Extract images metadata
    images_data, err_imgs = extract_images(soup, url)
    if err_imgs:
        images_data = []

    # Extract tables
    tables_data, err_tables = extract_tables(soup)
    if err_tables:
        tables_data = []

    # Convert text_data to docling.md and markitdown.md
    with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as tmp_md:
        tmp_md.write(text_data.encode("utf-8"))
        tmp_md_path = tmp_md.name

    docling_md = ""
    markitdown_md = ""
    try:
        docling_md = docling_convert(tmp_md_path)
    except Exception as e:
        docling_md = f"Docling conversion failed: {e}"

    try:
        markitdown_md = markitdown_convert(tmp_md_path)
    except Exception as e:
        markitdown_md = f"Markitdown conversion failed: {e}"

    # Delete temporary file after use
    os.remove(tmp_md_path)

    return {
        "error": None,
        "docling_markdown": docling_md,
        "markitdown_markdown": markitdown_md,
        "text_raw": text_data,
        "images": images_data,
        "tables": tables_data,
        "urls": urls_data
    }
