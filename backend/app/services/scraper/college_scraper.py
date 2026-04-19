"""
Web Scraper for AIMS College Website

Scrapes www.theaims.ac.in and extracts educational content.
"""

import logging
import requests
from typing import List, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

# Base URL
BASE_URL = "https://www.theaims.ac.in"

# Pages to scrape (common college website sections)
ROUTES_TO_SCRAPE = [
    "/",
    "/about",
    "/academics",
    "/admissions",
    "/courses",
    "/faculty",
    "/campus",
    "/placements",
    "/contact"
]


class AIMSWebScraper:
    """Scrape AIMS college website"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Educational Bot)"
        })
        self.pages_scraped = []
    
    def scrape_all(self) -> List[Tuple[str, str, str]]:
        """
        Scrape multiple pages
        
        Returns:
            List of (url, title, content)
        """
        all_content = []
        
        for route in ROUTES_TO_SCRAPE:
            url = urljoin(self.base_url, route)
            try:
                content = self.scrape_page(url)
                if content:
                    all_content.append(content)
                time.sleep(0.5)  # Be respectful
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
        
        logger.info(f"Scraped {len(all_content)} pages from {self.base_url}")
        return all_content
    
    def scrape_page(self, url: str) -> Tuple[str, str, str]:
        """
        Scrape single page and extract content
        
        Args:
            url: Page URL
            
        Returns:
            (url, title, clean_text) or None if failed
        """
        try:
            logger.info(f"Scraping {url}...")
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.title.string if soup.title else ""
            
            # Remove script/style tags
            for tag in soup(['script', 'style', 'nav', 'footer']):
                tag.decompose()
            
            # Get text
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            text = ' '.join(text.split())
            
            if len(text) < 100:
                logger.warning(f"Page too short: {url}")
                return None
            
            return (url, title, text)
            
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Chunk long text into sentences/paragraphs
        
        Args:
            text: Text to chunk
            chunk_size: Target chars per chunk
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        # Split by sentences
        sentences = text.replace('. ', '.\n').split('\n')
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += " " + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [c for c in chunks if len(c) > 50]  # Filter short chunks


def scrape_aims_website() -> List[Tuple[str, str, str]]:
    """
    Convenience function to scrape AIMS website
    
    Returns:
        List of (url, title, content)
    """
    scraper = AIMSWebScraper(BASE_URL)
    return scraper.scrape_all()
