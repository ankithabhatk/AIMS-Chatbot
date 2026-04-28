#!/usr/bin/env python3
"""
JS-Aware Scraper using Playwright

Handles JavaScript-rendered pages that regular requests can't scrape

Usage:
    python scripts/scrape_js.py --limit 20
"""

import argparse
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional

from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

MAX_PAGES = 50


def clean_text(text: str) -> str:
    """Clean extracted text"""
    lines = []
    prev_empty = False
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            if prev_empty:
                continue
            prev_empty = True
            continue
        prev_empty = False
        line = re.sub(r"\s+", " ", line)
        lines.append(line)
    return "\n".join(lines)


def split_chunks(text: str, max_chars: int = 500) -> List[str]:
    """Split text into chunks"""
    if len(text) <= max_chars:
        return [text] if text.strip() else []
    
    chunks = []
    sentences = re.split(r"(?<=[.!?])\n", text)
    current = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(current) + len(sentence) <= max_chars:
            current += " " + sentence
        else:
            if current.strip():
                chunks.append(current.strip())
            current = sentence
    
    if current.strip():
        chunks.append(current.strip())
    
    return [c for c in chunks if len(c) > 30]


def scrape_page(url: str, page) -> Optional[Dict]:
    """Scrape a single page using Playwright"""
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        
        # Wait for content to load
        page.wait_for_timeout(2000)
        
        # Get page title
        title = page.title()
        
        # Get main content
        content = page.evaluate('''
            () => {
                const main = document.querySelector('main') || 
                           document.querySelector('article') ||
                           document.querySelector('.content') ||
                           document.querySelector('#content') ||
                           document.body;
                return main ? main.innerText : '';
            }
        ''')
        
        text = clean_text(content)
        
        if len(text.split()) < 30:
            return None
        
        # Get heading
        heading = page.evaluate('''
            () => {
                const h1 = document.querySelector('h1');
                return h1 ? h1.innerText : '';
            }
        ''')
        
        return {
            "url": url,
            "title": title,
            "heading": heading,
            "text": text,
            "chunks": split_chunks(text),
            "scraped_at": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.warning(f"Error: {url} → {str(e)[:50]}")
        return None


def main():
    parser = argparse.ArgumentParser(description="JS-Aware Scraper")
    parser.add_argument("--limit", type=int, default=10, help="Max pages to scrape")
    args = parser.parse_args()
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_path = os.path.join(project_root, "data", "discovered_links.json")
    output_path = os.path.join(project_root, "data", "scraped_js.json")
    
    if not os.path.exists(input_path):
        logger.error(f"Input not found: {input_path}")
        return
    
    with open(input_path) as f:
        data = json.load(f)
    
    urls = data.get("for_ingestion", [])[:args.limit]
    
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        for i, url in enumerate(urls):
            logger.info(f"[{i+1}/{len(urls)}] {url[:60]}...")
            result = scrape_page(url, page)
            
            if result:
                results.append(result)
                logger.info(f"    OK: {len(result['chunks'])} chunks")
            else:
                logger.info(f"    Skipped")
        
        browser.close()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    total_chunks = sum(len(p["chunks"]) for p in results)
    logger.info(f"Done! Scraped {len(results)} pages, {total_chunks} chunks")


if __name__ == "__main__":
    main()