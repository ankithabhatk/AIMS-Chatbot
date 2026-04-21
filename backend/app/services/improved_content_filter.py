"""
Improved Ingestion with Targeted Coverage

Strategy:
- Prioritize high-value pages (placements, facilities, programs, admissions)
- Be less aggressive with filtering on these pages
- Better section extraction for multi-topic pages
"""

import logging
from typing import List, Dict
import re

logger = logging.getLogger(__name__)


class ImprovedContentFilter:
    """
    Improved content filter that preserves high-value knowledge
    while still removing noise.
    """
    
    # High-priority pages - keep even if they'd normally be filtered
    HIGH_VALUE_PATTERNS = [
        r'placement',
        r'facility|campus|infrastructure|hostel',
        r'program|course|curriculum|bba|mba|phd',
        r'admission|apply|enrollment|selection|eligibility',
    ]
    
    # Patterns to STILL skip (hard blocks)
    ALWAYS_SKIP_PATTERNS = [
        r'privacy',
        r'terms',
        r'disclaimer',
        r'refund',
        r'gallery',
    ]
    
    @staticmethod
    def is_high_value_page(url: str) -> bool:
        """Check if page is high-value (should be kept)"""
        url_lower = url.lower()
        for pattern in ImprovedContentFilter.HIGH_VALUE_PATTERNS:
            if re.search(pattern, url_lower):
                return True
        return False
    
    @staticmethod
    def should_skip_url(url: str) -> bool:
        """Hard-skip certain URLs"""
        url_lower = url.lower()
        for pattern in ImprovedContentFilter.ALWAYS_SKIP_PATTERNS:
            if re.search(pattern, url_lower):
                return True
        return False
    
    @staticmethod
    def filter_documents_v2(documents: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Improved filtering that preserves high-value pages
        
        Strategy:
        1. Hard skip (privacy, terms, disclaimer, refund, gallery)
        2. For high-value pages: only filter if purely boilerplate
        3. For other pages: normal filtering
        """
        filtered = []
        stats = {
            'total': len(documents),
            'skipped_hard': 0,
            'skipped_boilerplate': 0,
            'kept': 0,
            'high_value_kept': 0
        }
        
        for doc in documents:
            url = doc.get('url', '')
            content = doc.get('content', '')
            title = doc.get('title', '')
            
            # Hard skip
            if ImprovedContentFilter.should_skip_url(url):
                logger.debug(f"Hard skip: {url}")
                stats['skipped_hard'] += 1
                continue
            
            is_high_value = ImprovedContentFilter.is_high_value_page(url)
            
            # For high-value pages: be lenient (only skip if too short)
            if is_high_value:
                if len(content) < 50:
                    logger.debug(f"Too short (high-value): {title}")
                    stats['skipped_boilerplate'] += 1
                    continue
                
                doc['quality_score'] = 1.0  # Always high
                doc['is_high_value'] = True
                filtered.append(doc)
                stats['kept'] += 1
                stats['high_value_kept'] += 1
                logger.info(f"Keeping high-value: {title}")
            
            # For other pages: normal filtering
            else:
                # Quick quality check
                if len(content) < 100:
                    stats['skipped_boilerplate'] += 1
                    continue
                
                # Check for boilerplate
                boilerplate_markers = [
                    'privacy policy',
                    'terms and condition',
                    'apply now',
                    'deadline',
                    'newsletter',
                ]
                
                is_boilerplate = sum(1 for m in boilerplate_markers if m in content.lower()) > 2
                
                if is_boilerplate:
                    logger.debug(f"Boilerplate-heavy: {title}")
                    stats['skipped_boilerplate'] += 1
                    continue
                
                doc['quality_score'] = 0.8
                doc['is_high_value'] = False
                filtered.append(doc)
                stats['kept'] += 1
        
        logger.info(f"\n📊 IMPROVED FILTERING RESULTS:")
        logger.info(f"   Total: {stats['total']}")
        logger.info(f"   Hard skip: {stats['skipped_hard']}")
        logger.info(f"   Filtered (boilerplate): {stats['skipped_boilerplate']}")
        logger.info(f"   Kept: {stats['kept']} (high-value: {stats['high_value_kept']})")
        logger.info(f"   Retention rate: {(stats['kept'] / max(1, stats['total']) * 100):.1f}%\n")
        
        return filtered
