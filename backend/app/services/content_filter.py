"""
Content Quality Filter

Removes low-quality pages before chunking:
- Legal/boilerplate pages (privacy, terms, etc)
- Pages with mostly repeated content
- Pages with heavy boilerplate
- Pages that are too short
"""

import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)


class ContentFilter:
    """Filter out low-quality documents before processing"""
    
    # URLs to completely skip
    BLOCKED_URL_PATTERNS = [
        r'privacy',
        r'terms',
        r'condition',
        r'disclaimer',
        r'grievance',
        r'refund',
        r'cdn-cgi',
        r'enquiry',
        r'newsletter',
        r'gallery',
        r'contact',  # Contact pages often have just forms
        r'pdf$',  # PDF files
    ]
    
    # Content patterns to skip or downweight
    BOILERPLATE_PATTERNS = [
        r'privacy policy',
        r'terms and condition',
        r'refund policy',
        r'grievance redressal',
        r'disclaimer',
        r'copyright',
        r'all rights reserved',
        r'apply now',  # Too generic
        r'deadline.*admission',  # Dates change, not useful
        r'newsletter',
        r'subscribe',
        r'facebook|twitter|linkedin|instagram',  # Social media
    ]
    
    # Patterns to prefer (mark as high quality)
    QUALITY_PATTERNS = [
        r'program|course|bba|mba|phd',
        r'eligibility|admission|apply',
        r'curriculum|course|structure',
        r'placements?|companies|salary|recruitment',
        r'faculty|professor|instructor',
        r'facilities?|library|hostel|campus',
        r'about.*aims|vision|mission',
    ]
    
    @staticmethod
    def should_skip_url(url: str) -> bool:
        """Check if URL should be skipped entirely"""
        url_lower = url.lower()
        for pattern in ContentFilter.BLOCKED_URL_PATTERNS:
            if re.search(pattern, url_lower):
                logger.info(f"Skipping URL (pattern '{pattern}'): {url}")
                return True
        return False
    
    @staticmethod
    def get_quality_score(text: str, url: str) -> float:
        """
        Score content quality (0-1)
        
        Higher = better. < 0.3 = skip
        """
        if not text or len(text) < 100:
            return 0.0  # Too short
        
        text_lower = text.lower()
        
        # Count boilerplate indicators
        boilerplate_matches = 0
        for pattern in ContentFilter.BOILERPLATE_PATTERNS:
            if re.search(pattern, text_lower):
                boilerplate_matches += 1
        
        # Count quality indicators
        quality_matches = 0
        for pattern in ContentFilter.QUALITY_PATTERNS:
            if re.search(pattern, text_lower):
                quality_matches += 1
        
        # Calculate score
        # Base: 0.5
        score = 0.5
        
        # Boilerplate reduces score heavily
        if boilerplate_matches > 0:
            score -= boilerplate_matches * 0.15  # Each boilerplate pattern: -0.15
        
        # Quality patterns increase score
        if quality_matches > 0:
            score += quality_matches * 0.08  # Each quality pattern: +0.08
        
        # Repeated content is bad (simple heuristic)
        # Check if text has repeated phrases (sign of menu/boilerplate)
        lines = text.split('\n')
        if len(lines) > 1:
            short_lines = [l.strip() for l in lines if 10 <= len(l) <= 50]
            if short_lines:
                # Count duplicates
                from collections import Counter
                counts = Counter(short_lines)
                max_count = max(counts.values()) if counts else 1
                if max_count > 3:  # More than 3 repeats of a short line
                    score -= 0.2
        
        # Penalize very long repeated patterns
        if len(text) > 1000:
            # Check for patterns like "DEADLINE FOR MBA ... DEADLINE FOR MBA ..."
            if text.count("DEADLINE FOR MBA") > 2:
                score -= 0.2
            if text.count("Newsletter") > 2:
                score -= 0.2
        
        # Ensure score is in [0, 1]
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def filter_documents(documents: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Filter documents, removing low-quality ones
        
        Args:
            documents: List of {title, content, url} dicts
        
        Returns:
            Filtered list with quality scores
        """
        filtered = []
        stats = {
            'total': len(documents),
            'skipped_url': 0,
            'low_quality': 0,
            'kept': 0
        }
        
        for doc in documents:
            url = doc.get('url', '')
            content = doc.get('content', '')
            title = doc.get('title', '')
            
            # Check URL patterns
            if ContentFilter.should_skip_url(url):
                stats['skipped_url'] += 1
                continue
            
            # Check content quality
            quality = ContentFilter.get_quality_score(content, url)
            
            if quality < 0.3:  # Threshold: < 0.3 is low quality
                logger.debug(f"Low quality (score={quality:.2f}): {title} ({url})")
                stats['low_quality'] += 1
                continue
            
            # Keep this document with quality score
            doc['quality_score'] = quality
            filtered.append(doc)
            stats['kept'] += 1
        
        logger.info(f"\n📊 Content Filtering Results:")
        logger.info(f"   Total: {stats['total']}")
        logger.info(f"   Skipped (URL pattern): {stats['skipped_url']}")
        logger.info(f"   Removed (low quality): {stats['low_quality']}")
        logger.info(f"   Kept: {stats['kept']}")
        logger.info(f"   Removal rate: {((stats['skipped_url'] + stats['low_quality']) / max(1, stats['total']) * 100):.1f}%\n")
        
        return filtered
