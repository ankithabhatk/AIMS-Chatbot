#!/usr/bin/env python3
"""
Comprehensive Site Exploration

Find ALL pages on AIMS website to understand complete knowledge coverage.
No filtering - just discover what's there.
"""

import sys
import logging
from typing import Set, Dict, List
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from collections import deque

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class CompleteSiteCrawler:
    """Crawl entire site and categorize pages by content type"""
    
    def __init__(self, max_depth: int = 3, delay: float = 0.3):
        self.max_depth = max_depth
        self.delay = delay
        self.visited = set()
        self.pages_by_category = {
            'admissions': [],
            'programs': [],
            'placements': [],
            'facilities': [],
            'academics': [],
            'administration': [],
            'research': [],
            'student_life': [],
            'other': []
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Educational Research Bot)'
        })
    
    def _categorize_url(self, url: str) -> str:
        """Categorize URL by content"""
        url_lower = url.lower()
        
        if any(x in url_lower for x in ['admission', 'apply', 'enrollment', 'selection', 'eligibility']):
            return 'admissions'
        elif any(x in url_lower for x in ['program', 'course', 'bba', 'mba', 'phd', 'degree', 'curriculum']):
            return 'programs'
        elif any(x in url_lower for x in ['placement', 'recruit', 'companies', 'salary', 'career']):
            return 'placements'
        elif any(x in url_lower for x in ['hostel', 'facility', 'campus', 'infra', 'library', 'sports', 'gym']):
            return 'facilities'
        elif any(x in url_lower for x in ['academics', 'faculty', 'research', 'scholar', 'journal', 'publication']):
            return 'academics'
        elif any(x in url_lower for x in ['administration', 'admin', 'quality', 'accredit', 'iqac']):
            return 'administration'
        elif any(x in url_lower for x in ['research', 'patent', 'scholar', 'publication']):
            return 'research'
        elif any(x in url_lower for x in ['student', 'club', 'rotaract', 'grievance', 'conduct']):
            return 'student_life'
        else:
            return 'other'
    
    def _should_skip_url(self, url: str) -> bool:
        """Skip non-relevant URLs"""
        skip_patterns = [
            'privacy',
            'terms',
            'disclaimer',
            'refund',
            'cdn-cgi',
            'contact',  # Generic contact
            'enquiry',
            'newsletter',
            'gallery',
            'news',  # News items change daily
            'event',  # Event pages change
            'blog',
            '.pdf',
            'tel:',
            'mailto:',
            'facebook.com',
            'twitter.com',
            'linkedin.com',
            'instagram.com',
        ]
        
        url_lower = url.lower()
        for pattern in skip_patterns:
            if pattern in url_lower:
                return True
        return False
    
    def crawl(self, start_url: str) -> Dict[str, List[str]]:
        """Crawl entire site"""
        logger.info(f"\n{'='*80}")
        logger.info("COMPREHENSIVE SITE EXPLORATION")
        logger.info(f"{'='*80}\n")
        
        base_domain = urlparse(start_url).netloc
        queue = deque([(start_url, 0)])
        self.visited = set()
        all_urls = []
        
        while queue:
            current_url, depth = queue.popleft()
            
            if depth > self.max_depth:
                continue
            
            norm = current_url.rstrip('/').lower()
            if norm in self.visited:
                continue
            
            self.visited.add(norm)
            
            if self._should_skip_url(current_url):
                continue
            
            # Extract category
            category = self._categorize_url(current_url)
            
            try:
                logger.info(f"[D{depth}] [{category:15}] {current_url[:70]}")
                
                import time
                time.sleep(self.delay)
                
                response = self.session.get(current_url, timeout=10)
                response.raise_for_status()
                
                # Track this URL
                self.pages_by_category[category].append(current_url)
                all_urls.append((category, current_url))
                
                # Find more links
                if depth < self.max_depth:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link['href'].strip()
                        if not href or href.startswith(('#', 'javascript:')):
                            continue
                        
                        absolute_url = urljoin(current_url, href)
                        parsed = urlparse(absolute_url)
                        
                        # Only internal links
                        if base_domain in parsed.netloc:
                            norm_href = absolute_url.rstrip('/').lower()
                            if norm_href not in self.visited:
                                queue.append((absolute_url, depth + 1))
            
            except Exception as e:
                logger.debug(f"  Error: {str(e)[:50]}")
        
        return self.pages_by_category


def main():
    crawler = CompleteSiteCrawler(max_depth=2, delay=0.2)
    result = crawler.crawl("https://www.theaims.ac.in")
    
    # Print report
    logger.info(f"\n{'='*80}")
    logger.info("SITE COVERAGE REPORT")
    logger.info(f"{'='*80}\n")
    
    total_pages = 0
    for category in sorted(result.keys()):
        pages = result[category]
        total_pages += len(pages)
        
        logger.info(f"\n📚 {category.upper()} ({len(pages)} pages):")
        for url in pages[:5]:  # Show first 5
            logger.info(f"   • {url}")
        
        if len(pages) > 5:
            logger.info(f"   ... and {len(pages) - 5} more")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"TOTAL: {total_pages} unique pages discovered")
    logger.info(f"{'='*80}\n")
    
    # Coverage analysis
    logger.info("COVERAGE BY CATEGORY:")
    for category in sorted(result.keys()):
        count = len(result[category])
        status = "✅" if count > 0 else "❌"
        logger.info(f"  {status} {category:20} {count:3} pages")
    
    logger.info("\nKEY GAPS (low coverage):")
    for category in sorted(result.keys()):
        count = len(result[category])
        if count <= 1:
            logger.info(f"  🔴 {category}: MISSING ({count} pages)")
        elif count <= 2:
            logger.info(f"  🟡 {category}: LIMITED ({count} pages)")


if __name__ == "__main__":
    main()
