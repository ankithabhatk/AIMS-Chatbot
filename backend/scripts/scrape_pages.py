#!/usr/bin/env python3
"""
Selective Page Scraper

Scrapes ONLY high-value pages from discovered_links.json
Clean HTML -> text -> chunks for RAG

Usage:
    python scripts/scrape_pages.py --limit 50
"""

import argparse
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from bs4.element import Comment

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

MAX_RUNTIME = 30 * 60
REQUEST_TIMEOUT = 15


def should_stop() -> bool:
    if not hasattr(should_stop, 'start'):
        should_stop.start = time.time()
    return (time.time() - should_stop.start) > MAX_RUNTIME


def is_valid_content(text: str) -> bool:
    return len(text.split()) > 50


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", 
                    "iframe", "svg", "form", "button", "input"]):
        tag.decompose()
    
    for comment in soup.find_all(text=lambda t: isinstance(t, Comment)):
        comment.extract()
    
    for tag in soup.find_all(True):
        if not tag.get_text(strip=True):
            tag.decompose()
    
    main_content = None
    for selector in ["main", "article", ".content", "#content", ".main-content"]:
        main_content = soup.select_one(selector)
        if main_content and main_content.get_text(strip=True):
            break
    
    if main_content:
        soup = BeautifulSoup(main_content.decode(), "html.parser")
    
    text = soup.get_text(separator="\n").strip()
    
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


def split_into_chunks(text: str, max_chars: int = 500) -> List[str]:
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


def scrape_page(url: str) -> Optional[Dict]:
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AIMS-Chatbot/1.0)"
        })
        
        if resp.status_code != 200:
            return None
        
        text = clean_html(resp.text)
        
        if not is_valid_content(text):
            return None
        
        soup = BeautifulSoup(resp.text, "html.parser")
        title_tag = soup.find("title")
        title = title_tag.get_text().strip() if title_tag else ""
        
        heading = ""
        for h in soup.find_all(["h1", "h2"]):
            heading = h.get_text().strip()
            if heading:
                break
        
        return {
            "url": url,
            "title": title,
            "heading": heading,
            "text": text,
            "chunks": split_into_chunks(text),
            "scraped_at": datetime.now().isoformat(),
        }
        
    except Exception:
        return None


def scrape_pages(urls: List[str], limit: int = 50) -> List[Dict]:
    results = []
    should_stop.start = time.time()
    
    for i, url in enumerate(urls[:limit]):
        if should_stop():
            break
        
        logger.info(f"[{i+1}/{min(len(urls), limit)}] {url[:70]}...")
        page = scrape_page(url)
        
        if page:
            results.append(page)
            logger.info(f"    OK: {len(page['chunks'])} chunks")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Selective Page Scraper")
    parser.add_argument("--limit", type=int, default=10, help="Max pages to scrape")
    args = parser.parse_args()
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_path = os.path.join(project_root, "data", "discovered_links.json")
    output_path = os.path.join(project_root, "data", "scraped_pages.json")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return
    
    with open(input_path) as f:
        data = json.load(f)
    
    urls = data.get("for_ingestion", [])
    logger.info(f"Found {len(urls)} URLs to scrape (limit: {args.limit})")
    
    scraped = scrape_pages(urls, args.limit)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(scraped, f, indent=2)
    
    total_chunks = sum(len(p["chunks"]) for p in scraped)
    logger.info(f"Done! Scraped {len(scraped)} pages, {total_chunks} total chunks")


if __name__ == "__main__":
    main()
