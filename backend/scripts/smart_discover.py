#!/usr/bin/env python3
"""
Smart Link Discovery + Coverage Tracker

Flow 1 (Discovery): Extract all links from sitemap, nav, footer
Flow 2 (Classification): Classify each URL by type
Output: Coverage report showing what's covered vs missing

Usage:
    python scripts/smart_discover.py --base-url https://www.theaims.ac.in --output data/links.json
"""

import argparse
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


BASE_URL = "https://www.theaims.ac.in"

# Classification rules: ordered by priority (checked in this order)
CLASSIFICATION_RULES = [
    ("admission", r"admission", 1, "high"),
    ("fee", r"fee|cost|charge|scholarship|loan|refund|payment", 1, "high"),
    ("placement", r"placement|recruit|career|job|salary|package|lpa", 1, "high"),
    ("course", r"program|course|mba|mca|bba|bca|bcom|mcom|specialization|degree", 2, "high"),
    ("facility", r"hostel|facility|campus|infrastructure|lab|library|cafeteria|transport|sports", 3, "medium"),
    ("faculty", r"faculty|professor|director|team|staff", 4, "low"),
    ("contact", r"contact|about|reach", 3, "medium"),
]

# Low-value patterns to SKIP (checked AFTER specific classifications)
LOW_VALUE_PATTERNS = [
    r"news",
    r"blog",
    r"event\.html",
    r"announcement",
    r"media",
    r"gallery",
    r"photo",
    r"video",
    r"testimonial",
    r"alumni",
    r"achiever",
    r"award",
    r"press",
]


def is_internal_url(url: str) -> bool:
    """Check if URL is internal (same domain)"""
    parsed = urlparse(url)
    base_parsed = urlparse(BASE_URL)
    return parsed.netloc == "" or parsed.netloc == base_parsed.netloc


def normalize_url(url: str) -> str:
    """Normalize URL: remove fragments, trailing slashes"""
    url = url.split("#")[0]
    url = url.rstrip("/")
    if not url.startswith("http"):
        url = urljoin(BASE_URL, url)
    return url


def classify_url(url: str) -> Dict:
    """Classify a URL by its path patterns (ordered rules)"""
    url_lower = url.lower()
    
    # Skip non-HTML files
    if any(url_lower.endswith(ext) for ext in [".pdf", ".jpg", ".png", ".jpeg", ".gif", ".mp4", ".zip"]):
        return {"type": "file", "priority": 99, "value": "low"}
    
    # Check specific classifications in priority order
    for category, pattern, priority, value in CLASSIFICATION_RULES:
        if re.search(pattern, url_lower):
            return {"type": category, "priority": priority, "value": value}
    
    # Check low-value
    for pattern in LOW_VALUE_PATTERNS:
        if re.search(pattern, url_lower):
            return {"type": "low_value", "priority": 99, "value": "low"}
    
    return {"type": "other", "priority": 99, "value": "low"}


def extract_links_from_html(html: str, base: str) -> Set[str]:
    """Extract all href links from HTML"""
    links = set()
    soup = BeautifulSoup(html, "html.parser")
    
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if href and not href.startswith(("javascript:", "mailto:", "tel:", "#")):
            normalized = normalize_url(urljoin(base, href))
            if is_internal_url(normalized):
                links.add(normalized)
    
    return links


def extract_from_sitemap(base_url: str) -> Set[str]:
    """Extract links from sitemap.xml"""
    links = set()
    sitemap_url = urljoin(base_url, "/sitemap.xml")
    
    try:
        resp = requests.get(sitemap_url, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "xml")
            for loc in soup.find_all("loc"):
                url = normalize_url(loc.text.strip())
                links.add(url)
            logger.info(f"Sitemap: found {len(links)} links")
    except Exception as e:
        logger.warning(f"Sitemap fetch failed: {e}")
    
    return links


def extract_from_nav(base_url: str) -> Set[str]:
    """Extract links from navbar and footer"""
    links = set()
    
    try:
        resp = requests.get(base_url, timeout=10)
        if resp.status_code == 200:
            links.update(extract_links_from_html(resp.text, base_url))
            logger.info(f"Nav/Footer: found {len(links)} links")
    except Exception as e:
        logger.warning(f"Nav fetch failed: {e}")
    
    return links


def discover_links(base_url: str) -> List[Dict]:
    """Discover and classify all links"""
    all_links = set()
    
    # Priority: sitemap > nav
    all_links.update(extract_from_sitemap(base_url))
    all_links.update(extract_from_nav(base_url))
    
    logger.info(f"Total unique links: {len(all_links)}")
    
    # Classify each link
    classified = []
    for url in sorted(all_links):
        classification = classify_url(url)
        classified.append({
            "url": url,
            **classification,
        })
    
    return classified


def generate_coverage_report(classified_links: List[Dict]) -> Dict:
    """Generate coverage report"""
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_urls": len(classified_links),
        "by_type": {},
        "high_value": [],
        "medium_value": [],
        "low_value": [],
        "missing_categories": [],
    }
    
    # Count by type
    for link in classified_links:
        link_type = link["type"]
        if link_type not in report["by_type"]:
            report["by_type"][link_type] = []
        report["by_type"][link_type].append(link["url"])
        
        value = link.get("value", "low")
        if value == "high":
            report["high_value"].append(link["url"])
        elif value == "medium":
            report["medium_value"].append(link["url"])
        else:
            report["low_value"].append(link["url"])
    
    # Check missing high-value categories
    required_categories = ["course", "admission", "fee", "placement"]
    for cat in required_categories:
        if cat not in report["by_type"]:
            report["missing_categories"].append(cat)
    
    return report


def print_report(report: Dict):
    """Pretty print coverage report"""
    print("\n" + "=" * 60)
    print("COVERAGE REPORT")
    print("=" * 60)
    
    print(f"\nGenerated: {report['generated_at']}")
    print(f"Total URLs: {report['total_urls']}")
    
    print("\n--- By Type ---")
    for link_type, urls in sorted(report["by_type"].items()):
        print(f"  {link_type}: {len(urls)} pages")
    
    print("\n--- Coverage ---")
    required = ["course", "admission", "fee", "placement"]
    for cat in required:
        count = len(report["by_type"].get(cat, []))
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {cat}: {count} pages")
    
    print("\n--- Missing ---")
    if report["missing_categories"]:
        for cat in report["missing_categories"]:
            print(f"  ❌ {cat}")
    else:
        print("  ✅ All required categories covered!")
    
    print("\n--- Value Distribution ---")
    print(f"  High value: {len(report['high_value'])} pages (for ingestion)")
    print(f"  Medium value: {len(report['medium_value'])} pages")
    print(f"  Low value (skip): {len(report['low_value'])} pages (excluded)")
    
    print("\n" + "=" * 60)


def save_output(classified_links: List[Dict], report: Dict, output_path: str):
    """Save to JSON"""
    output = {
        "report": report,
        "links": classified_links,
        "for_ingestion": report["high_value"],
    }
    
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Saved to {output_path}")
    logger.info(f"Pages for ingestion: {len(report['high_value'])}")


def main():
    parser = argparse.ArgumentParser(description="Smart Link Discovery + Coverage Tracker")
    parser.add_argument("--base-url", default=BASE_URL, help="Base URL to crawl")
    parser.add_argument("--output", default="data/discovered_links.json", help="Output JSON path")
    args = parser.parse_args()
    
    logger.info(f"Discovering links from {args.base_url}...")
    
    classified = discover_links(args.base_url)
    report = generate_coverage_report(classified)
    
    print_report(report)
    save_output(classified, report, args.output)
    
    return report


if __name__ == "__main__":
    main()