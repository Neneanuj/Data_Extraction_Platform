import requests
import os
import json
from datetime import datetime

def scrape_url_with_diffbot(url, token, output_file="scraped_data.md"):
    api_url = "https://api.diffbot.com/v3/analyze"
    token = os.environ.get("a5b3a63d48ffbf84d9072b931fac1447")
    params = {
        'token': token,
        'url': url
    }
    
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Create markdown content
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"# Scraped Data Report\n\n")
            f.write(f"## Source URL\n{url}\n\n")
            f.write(f"## Timestamp\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Write data in a structured format
            f.write("## Extracted Content\n")
            f.write("```\n")  
            f.write(json.dumps(data, indent=2))
            f.write("\n```\n")
            
        print(f"Data has been saved to {output_file}")
        return data
        
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None


