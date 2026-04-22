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
        """Extract clean text from HTML using semantic tags and detect content type"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted elements (Junk Cleanup)
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'meta', 'noscript', 'iframe']):
                tag.decompose()
            
            # Get title - use separator=' ' to preserve spaces between nested elements
            title = ""
            if soup.title:
                title_text = soup.title.string
                if title_text:
                    title = ' '.join(title_text.strip().split())  # Clean up whitespace
            elif soup.h1:
                title = soup.h1.get_text(separator=' ', strip=True)
            
            # ================================================================
            # BROAD EXTRACTION STRATEGY
            # ================================================================
            content_parts = []
            
            # Prioritize semantic tags and headings/paragraphs in order
            # Use separator=' ' to preserve spaces between inline elements (like <br/>, <span>, etc)
            for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'section']):
                text = element.get_text(separator=' ', strip=True)
                if text and len(text) > 20:  # Skip noise/tiny fragments
                    # Clean multiple spaces
                    text = ' '.join(text.split())
                    content_parts.append(text)
            
            # Merge and clean
            content = ' '.join(content_parts)
            content = ' '.join(content.split())
            
            # Fallback to body if semantic extraction missed everything
            if not content or len(content) < 100:
                if soup.body:
                    content = ' '.join(soup.body.get_text(separator=' ', strip=True).split())
            
            if not content or len(content) < 50:
                return None
                
            # Content Type Detection
            is_faq = "faq" in url.lower() or content.count("?") > 5
            
            return {
                'title': title or urlparse(url).path.split('/')[-1],
                'content': content,
                'url': url,
                'type': 'faq' if is_faq else 'page'
            }
        
        except Exception as e:
            logger.error(f"Failed to extract text from {url}: {e}")
            return None
    
    def _extract_faq_from_html(self, html: str, url: str) -> List[Dict[str, str]]:
        """Extract FAQs from FAQ pages (if present)"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            faqs = []
            
            # Strategy 1: Look for accordion/collapsible patterns (common in FAQ pages)
            # Try multiple selectors that commonly contain FAQs
            faq_containers = []
            
            # Look for elements with 'faq', 'accordion', 'collapse' class/id
            faq_containers.extend(soup.find_all(['div', 'section'], class_=lambda x: x and any(kw in x.lower() for kw in ['faq', 'accordion', 'collapse', 'qa'])))
            
            # Strategy 2: Look for Q: ... A: ... patterns
            if not faq_containers:
                # Look for paragraphs that start with Q: or A:
                all_p = soup.find_all('p')
                for i, p in enumerate(all_p):
                    text = p.get_text(strip=True)
                    if text.lower().startswith('q:') or text.lower().startswith('question:'):
                        question = text.replace('Q:', '').replace('Question:', '').strip()
                        # Look for next paragraph starting with A:
                        if i + 1 < len(all_p):
                            next_text = all_p[i + 1].get_text(strip=True)
                            if next_text.lower().startswith('a:') or next_text.lower().startswith('answer:'):
                                answer = next_text.replace('A:', '').replace('Answer:', '').strip()
                                if question and answer:
                                    faqs.append({
                                        'type': 'faq',
                                        'question': question,
                                        'answer': answer,
                                        'content': f"FAQ Q: {question}\nA: {answer}",
                                        'url': url
                                    })
            
            # Strategy 3: Parse accordion structure (buttons + hidden content)
            if not faqs and faq_containers:
                for container in faq_containers:
                    buttons = container.find_all(['button', 'summary', 'div'], class_=lambda x: x and 'button' in x.lower())
                    
                    for button in buttons:
                        question = button.get_text(strip=True)
                        
                        # Look for next sibling that contains answer
                        next_elem = button.find_next(['div', 'p', 'section'])
                        if next_elem and next_elem != button:
                            answer = next_elem.get_text(strip=True)
                            if question and answer and len(answer) > 20:
                                faqs.append({
                                    'type': 'faq',
                                    'question': question,
                                    'answer': answer,
                                    'content': f"FAQ Q: {question}\nA: {answer}",
                                    'url': url
                                })
            
            if faqs:
                logger.info(f"  Extracted {len(faqs)} FAQs from {url}")
            
            return faqs
        
        except Exception as e:
            logger.debug(f"FAQ extraction failed for {url}: {e}")
            return []
    
    def scrape_website(self, start_url: str = None) -> List[Dict[str, str]]:
        """
        Comprehensive recursive crawl across AIMS domain
        """
        seed_urls = [
            # Core Pages
            "https://www.theaims.ac.in/",
            
            # Programs & Specializations
            "https://www.theaims.ac.in/programs",
            "https://www.theaims.ac.in/business-school",
            "https://www.theaims.ac.in/mba",
            "https://www.theaims.ac.in/bba",
            "https://www.theaims.ac.in/bca",
            "https://www.theaims.ac.in/bcom",
            "https://www.theaims.ac.in/mca",
            "https://www.theaims.ac.in/phd-doctoral-programs",
            
            # Admissions & Applications
            "https://www.theaims.ac.in/admission",
            "https://www.theaims.ac.in/admissions",
            
            # Placements & Career
            "https://www.theaims.ac.in/placement",
            "https://www.theaims.ac.in/placements",
            
            # Campus & Facilities
            "https://www.theaims.ac.in/hostel",
            "https://www.theaims.ac.in/campus-facilities",
            "https://www.theaims.ac.in/student-information-zone",
            
            # Information & Support
            "https://www.theaims.ac.in/faqs",
            "https://www.theaims.ac.in/faq",
            "https://www.theaims.ac.in/scholarships",
            "https://www.theaims.ac.in/contact-us",
            
            # Events & News
            "https://www.theaims.ac.in/articles-publications",
            "https://www.theaims.ac.in/news",
            "https://www.theaims.ac.in/events",
            
            # Additional Resources
            "https://www.theaims.ac.in/aims-alumni-association",
            "https://www.theaims.ac.in/rotaract-club",
            "https://www.theaims.ac.in/grievance-redressal",
            "https://www.theaims.ac.in/iqac-internal-quality-assurance-cell",
        ]
        
        # Override seeds if a specific start_url was provided
        if start_url:
            seed_urls = [start_url]
            
        logger.info(f"Starting comprehensive scrape using {len(seed_urls)} seeds (Max Depth={self.max_depth})")
        
        base_domain = "theaims.ac.in"
        results = []
        
        # BFS crawling initialization
        queue = deque([(url, 0) for url in seed_urls])
        self.visited_urls = set()
        
        while queue:
            current_url, depth = queue.popleft()
            
            # Normalize and check visited
            normalized = self._normalize_url(current_url)
            if normalized in self.visited_urls:
                continue
            
            self.visited_urls.add(normalized)
            
            # Limit depth
            if depth > self.max_depth:
                continue
                
            try:
                # Respect crawl delay if needed
                if self.delay > 0:
                    time.sleep(self.delay)
                
                logger.debug(f"Scraping [{depth}]: {current_url}")
                response = self.session.get(current_url, timeout=10)
                response.raise_for_status()
                
                # Extract content
                extracted = self._extract_text_from_html(response.text, current_url)
                if extracted:
                    results.append(extracted)
                    logger.info(f"  ✓ {current_url} ({extracted['type']})")
                
                # Find internal links for next depth
                if depth < self.max_depth:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link['href'].strip()
                        if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                            continue
                            
                        # Normalize relative URLs
                        absolute_url = urljoin(current_url, href)
                        
                        # Domain boundary check
                        if self._is_internal_link(base_domain, absolute_url):
                            queue.append((absolute_url, depth + 1))
            
            except Exception as e:
                logger.warning(f"Skipping {current_url} due to error: {e}")
        
        logger.info(f"Scrape complete. Extracted {len(results)} pages across {len(self.visited_urls)} URLs visited.")
        return results


def scrape_aims_website() -> List[Dict[str, str]]:
    """Scrape AIMS college website"""
    scraper = WebScraper(max_depth=3, delay=0.5)  # Increased to depth 3 for more comprehensive crawl
    return scraper.scrape_website()
