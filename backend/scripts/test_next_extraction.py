# backend/scripts/test_next_extraction.py

import requests
from bs4 import BeautifulSoup
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_json(obj):
    texts = []
    if isinstance(obj, dict):
        for v in obj.values():
            texts.extend(extract_text_from_json(v))
    elif isinstance(obj, list):
        for item in obj:
            texts.extend(extract_text_from_json(item))
    elif isinstance(obj, str):
        clean_str = obj.strip()
        if len(clean_str) > 20: 
            texts.append(clean_str)
    return texts

def test_extraction(url):
    print(f"Testing extraction for: {url}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if not script:
        print("❌ __NEXT_DATA__ script NOT found!")
        return
    
    print("✅ __NEXT_DATA__ script found!")
    data = json.loads(script.string)
    page_props = data.get("props", {}).get("pageProps", {})
    
    extracted = extract_text_from_json(page_props)
    print(f"\nExtracted {len(extracted)} text fragments from JSON.")
    
    # Print sample
    print("\nSample fragments:")
    for t in extracted[:10]:
        print(f"  • {t[:100]}...")
        
    combined = " ".join(extracted)
    print(f"\nTotal characters from JSON: {len(combined)}")

if __name__ == "__main__":
    test_extraction("https://www.theaims.ac.in/placement")
