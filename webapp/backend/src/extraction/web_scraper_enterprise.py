import requests
import os
import json
from datetime import datetime
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_url_with_diffbot(url, output_file="scraped_data.md"):
    api_url = "https://api.diffbot.com/v3/analyze"
    token = os.environ.get("DIFFBOT_TOKEN")
    
    if not token:
        logger.error("DIFFBOT_TOKEN environment variable not set.")
        return {"error": "DIFFBOT_TOKEN environment variable not set."}
    
    params = {
        'token': token,
        'url': url
    }
    
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        
        markdown_content = f"# Scraped Data Report\n\n"
        markdown_content += f"## Source URL\n{url}\n\n"
        markdown_content += f"## Timestamp\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        markdown_content += "## Extracted Content\n"
        markdown_content += "```\n"  
        markdown_content += json.dumps(data, indent=2)
        markdown_content += "\n```\n"
        
    
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Data has been saved to {output_file}")
        return data
        
    except requests.RequestException as e:
        logger.error(f"Error during scraping: {e}")
        return {"error": str(e)}
