import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import pandas as pd

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
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers)
        return BeautifulSoup(response.content, 'html.parser'), None
    except Exception as e:
        return None, f"Failed to parse URL: {str(e)}"

def extract_clean_text(soup):
    """Extract and clean text"""
    try:
        return re.sub(r'\s+', ' ', soup.get_text()).strip(), None
    except Exception:
        return None, "Text extraction failed"

def extract_images(soup, base_url):
    """Extract images with metadata"""
    try:
        images = [{
            'position': i + 1,
            'alt': img.get('alt', '').strip(),
            'src': urljoin(base_url, img.get('src', '')),
            'width': img.get('width', 'N/A'),
            'height': img.get('height', 'N/A')
        } for i, img in enumerate(soup.find_all('img'))]
        return images, None
    except Exception:
        return None, "Image extraction failed"

def extract_tables(soup):
    """Extract tables from HTML"""
    try:
        tables = []
        for table in soup.find_all('table'):
            headers = [th.text.strip() for th in table.find_all('th')]
            if not headers and table.find('tr'):
                headers = [f'Column_{i}' for i in range(len(table.find('tr').find_all('td')))]
            
            rows = [[td.text.strip() for td in tr.find_all('td')] 
                   for tr in table.find_all('tr')]
            rows = [row for row in rows if row and len(row) == len(headers)]
            
            if rows:
                tables.append(pd.DataFrame(rows, columns=headers))
        return tables, None
    except Exception:
        return None, "Table extraction failed"

if __name__ == "__main__":
    target_url = input("Enter URL to scrape: ")
    print(f"\nProcessing URL: {target_url}")
    
    # Parse URL
    parsed_html, error = parse_url(target_url)
    if error:
        print(f"Error: {error}")
        exit()
    print("URL processed successfully!")
    
    # Extract content
    results = {
        'text': extract_clean_text(parsed_html),
        'images': extract_images(parsed_html, target_url),
        'tables': extract_tables(parsed_html)
    }
    
    # Save and display results
    for content_type, (data, error) in results.items():
        print(f"\nProcessing {content_type}...")
        if data:
            if content_type == 'text':
                with open('content.txt', 'w', encoding='utf-8') as f:
                    f.write(data)
                print(f"✓ Text saved to content.txt")
            elif content_type == 'images':
                df = pd.DataFrame(data)
                filename = f'image_metadata_{len(data)}.csv'
                df.to_csv(filename, index=False)
                print(f"✓ {len(data)} images saved to {filename}")
            else:  # tables
                for i, table in enumerate(data, 1):
                    filename = f'table_{i}.csv'
                    table.to_csv(filename, index=False)
                    print(f"✓ Table {i} saved to {filename}")
        else:
            print(f"× {content_type.capitalize()}: {error}")
    
    print("\nScraping completed!")
