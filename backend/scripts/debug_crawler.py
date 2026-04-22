# backend/scripts/debug_crawler.py

import sys
import os
import logging

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scraper.web_scraper import WebScraper

# Enable verbose logging
logging.basicConfig(level=logging.INFO)

def debug_crawl():
    scraper = WebScraper(max_depth=3, delay=0.1)
    results = scraper.scrape_website()
    
    print("\n" + "="*80)
    print(f"DEBUG CRAWL SUMMARY: {len(results)} pages")
    print("="*80)
    
    found_critical = []
    keywords = ["placement", "admission", "hostel", "fees", "scholarship", "mba"]
    
    for res in results:
        url = res["url"].lower()
        if any(k in url for k in keywords):
            found_critical.append(res["url"])
            
    print(f"Critical URLs Found ({len(found_critical)}):")
    for url in found_critical:
        print(f"  • {url}")
        
    print("\nAll URLs visited:")
    for url in sorted(scraper.visited_urls):
        print(f"  - {url}")

if __name__ == "__main__":
    debug_crawl()
