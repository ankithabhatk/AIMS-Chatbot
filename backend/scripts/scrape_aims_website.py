#!/usr/bin/env python3
"""
AIMS Website Professional Web Scraper
Extracts comprehensive college information for chatbot knowledge base
"""

import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Optional
import logging
from urllib.parse import urljoin, urlparse
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIMMSWebScraper:
    """Professional scraper for AIMS website"""
    
    def __init__(self):
        self.base_url = "https://www.theaims.ac.in"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.data = []
        self.visited_urls = set()
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage"""
        try:
            if url in self.visited_urls:
                return None
            
            self.visited_urls.add(url)
            logger.info(f"Fetching: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.warning(f"Error fetching {url}: {e}")
            return None
    
    def extract_page_content(self, url: str, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract structured content from page"""
        try:
            # Get title
            title_tag = soup.find('h1') or soup.find('title')
            title = title_tag.text.strip() if title_tag else "Untitled"
            
            # Get description/heading
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ""
            
            # Get all text content
            # Remove scripts and styles
            for script in soup(['script', 'style', 'nav', 'footer']):
                script.decompose()
            
            # Get paragraphs and headings
            content_parts = []
            for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'li']):
                text = element.get_text(strip=True)
                if text and len(text) > 10:  # Skip very short text
                    content_parts.append(text)
            
            # Get all links on page
            links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').strip()
                if href and (href.startswith('/') or href.startswith(self.base_url)):
                    full_url = urljoin(self.base_url, href)
                    link_text = link.get_text(strip=True)
                    if link_text:
                        links.append({'text': link_text, 'url': full_url})
            
            full_text = ' '.join(content_parts)
            
            if not full_text or len(full_text) < 50:
                return None
            
            return {
                'url': url,
                'title': title,
                'description': description,
                'content': full_text[:2000],  # Limit to 2000 chars
                'full_text': full_text,
                'links': links[:10]  # Top 10 links
            }
        
        except Exception as e:
            logger.warning(f"Error extracting from {url}: {e}")
            return None
    
    def scrape_key_pages(self):
        """Scrape key pages from AIMS website"""
        
        key_urls = [
            # Main pages
            f"{self.base_url}/",
            f"{self.base_url}/about-aims",
            f"{self.base_url}/admission-process",
            f"{self.base_url}/admission-requirements",
            
            # Programs
            f"{self.base_url}/business-school",
            f"{self.base_url}/business-school/master-business-administration",
            f"{self.base_url}/business-school/bachelor-business-administration",
            f"{self.base_url}/business-school/bachelor-business-administration-aviation-management",
            f"{self.base_url}/phd-doctoral-programs",
            
            # Student Info
            f"{self.base_url}/placements",
            f"{self.base_url}/campus-facilities",
            f"{self.base_url}/admission-requirements",
            f"{self.base_url}/contact-us",
            
            # Additional
            f"{self.base_url}/fees",
            f"{self.base_url}/scholarships",
            f"{self.base_url}/hostel",
        ]
        
        logger.info(f"\n🚀 Starting AIMS website scraping ({len(key_urls)} pages)\n")
        
        for url in key_urls:
            soup = self.fetch_page(url)
            if soup:
                content = self.extract_page_content(url, soup)
                if content:
                    self.data.append(content)
                    logger.info(f"✅ Extracted: {content['title']} ({len(content['full_text'])} chars)")
            
            time.sleep(0.5)  # Be respectful to server
        
        logger.info(f"\n📊 Total pages scraped: {len(self.data)}\n")
    
    def save_to_json(self, filename: str = '/tmp/aims_scraped_data.json'):
        """Save scraped data to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Data saved to {filename}")
        return filename
    
    def print_summary(self):
        """Print scraping summary"""
        print(f"\n{'='*80}")
        print(f"AIMS WEBSITE SCRAPING SUMMARY")
        print(f"{'='*80}\n")
        
        print(f"📄 Pages Scraped: {len(self.data)}\n")
        
        for i, page in enumerate(self.data, 1):
            print(f"{i}. {page['title']}")
            print(f"   URL: {page['url']}")
            print(f"   Size: {len(page['full_text'])} characters")
            if page['links']:
                print(f"   Related links: {len(page['links'])} found")
            print()
        
        total_chars = sum(len(p['full_text']) for p in self.data)
        print(f"{'='*80}")
        print(f"✅ Total content: {total_chars} characters")
        print(f"📊 Average per page: {total_chars // len(self.data) if self.data else 0} characters")
        print(f"{'='*80}\n")


def main():
    """Main execution"""
    scraper = AIMMSWebScraper()
    
    # Scrape key pages
    scraper.scrape_key_pages()
    
    # Print summary
    scraper.print_summary()
    
    # Save data
    output_file = scraper.save_to_json()
    
    print(f"\n📍 Data saved to: {output_file}")
    print(f"\nNext steps:")
    print(f"1. Review the scraped data")
    print(f"2. Run: python backend/scripts/ingest.py /tmp/aims_scraped_data.json")
    print(f"3. Test chatbot with: python backend/scripts/fast_test.py\n")


if __name__ == "__main__":
    main()
