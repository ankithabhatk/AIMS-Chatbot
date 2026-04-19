"""
Production-Grade Web Scraper for College Websites

Crawls websites while respecting:
- Link boundaries (no external domains)
- Crawl depth limits
- Content extraction rules
- Duplicate filtering
"""

import logging
from typing import List, Dict, Set
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import time
from collections import deque

logger = logging.getLogger(__name__)


class WebScraper:
    """Production scraper with depth limit, domain boundary, and dedup"""

    def __init__(self, max_depth: int = 2, delay: float = 1.0):
        """
        Initialize scraper
        
        Args:
            max_depth: Maximum crawl depth (0 = home only)
            delay: Delay between requests in seconds
        """
        self.max_depth = max_depth
        self.delay = delay
        self.visited_urls: Set[str] = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Educational Research Bot)'
        })
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison"""
        # Remove trailing slash and fragments
        return url.rstrip('/').split('#')[0].lower()
    
    def _is_internal_link(self, base_domain: str, target_url: str) -> bool:
        """Check if URL is internal (same domain)"""
        try:
            target_domain = urlparse(target_url).netloc.lower()
            return base_domain in target_domain or target_domain in base_domain
        except:
            return False
    
    def _extract_text_from_html(self, html: str, url: str) -> Dict[str, str]:
        """Extract clean text from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'meta', 'noscript']):
                tag.decompose()
            
            # Get title
            title = ""
            if soup.title:
                title = soup.title.string.strip()
            elif soup.h1:
                title = soup.h1.get_text(strip=True)
            
            # Get main content
            # Try to find main content area
            content_selector = soup.find('main') or soup.find('article') or soup.find(id='content') or soup.find(class_='content')
            
            if content_selector:
                content = content_selector.get_text(separator=' ', strip=True)
            else:
                # Fallback to body
                content = soup.body.get_text(separator=' ', strip=True) if soup.body else ""
            
            # Clean up whitespace
            content = ' '.join(content.split())
            
            if not content or len(content) < 50:
                return None
            
            return {
                'title': title or urlparse(url).path.split('/')[-1],
                'content': content,
                'url': url
            }
        
        except Exception as e:
            logger.error(f"Failed to extract text from {url}: {e}")
            return None
    
    def scrape_website(self, start_url: str) -> List[Dict[str, str]]:
        """
        Crawl website starting from URL
        
        Returns:
            List of {'title', 'content', 'url'} dicts
        """
        logger.info(f"Starting scrape of {start_url}")
        
        base_domain = urlparse(start_url).netloc
        results = []
        
        # BFS crawling
        queue = deque([(start_url, 0)])  # (url, depth)
        self.visited_urls = set()
        
        while queue:
            current_url, depth = queue.popleft()
            
            # Check limits
            if depth > self.max_depth:
                continue
            
            normalized = self._normalize_url(current_url)
            if normalized in self.visited_urls:
                continue
            
            self.visited_urls.add(normalized)
            
            try:
                logger.info(f"Scraping [{depth}]: {current_url}")
                
                # Respect crawl delay
                time.sleep(self.delay)
                
                # Fetch page
                response = self.session.get(current_url, timeout=10)
                response.raise_for_status()
                
                # Extract content
                extracted = self._extract_text_from_html(response.text, current_url)
                if extracted:
                    results.append(extracted)
                    logger.info(f"  ✓ Extracted: {len(extracted['content'])} chars")
                
                # Find internal links (only at depth < max_depth)
                if depth < self.max_depth:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link['href'].strip()
                        if not href or href.startswith(('#', 'javascript:', 'mailto:')):
                            continue
                        
                        # Convert relative URLs
                        absolute_url = urljoin(current_url, href)
                        
                        # Check if internal
                        if self._is_internal_link(base_domain, absolute_url):
                            normalized_href = self._normalize_url(absolute_url)
                            if normalized_href not in self.visited_urls:
                                queue.append((absolute_url, depth + 1))
            
            except requests.RequestException as e:
                logger.warning(f"Failed to fetch {current_url}: {e}")
            except Exception as e:
                logger.error(f"Error processing {current_url}: {e}")
        
        logger.info(f"Scrape complete. Extracted {len(results)} pages")
        return results


def scrape_aims_website() -> List[Dict[str, str]]:
    """Scrape AIMS college website"""
    scraper = WebScraper(max_depth=2, delay=0.5)
    return scraper.scrape_website("https://www.theaims.ac.in")
