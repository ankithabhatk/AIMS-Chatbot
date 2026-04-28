#!/usr/bin/env python3
"""
Browser screenshot validation - Take snapshots at key points
No interaction - just visual inspection of the system
"""

from playwright.sync_api import sync_playwright
import time
import os
from datetime import datetime

SCREENSHOTS_DIR = "/Users/maneeth/Desktop/Chat-Bot/validation_screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def take_screenshot(page, name: str):
    """Take and save a screenshot"""
    filename = f"{SCREENSHOTS_DIR}/{datetime.now().strftime('%H%M%S')}_{name}.png"
    page.screenshot(path=filename, full_page=True)
    print(f"  📸 Screenshot: {name}")
    return filename

def run_browser_test():
    """Simple browser screenshot test"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1024, "height": 768})
        
        print("\n" + "="*70)
        print("🌐 BROWSER VALIDATION - Visual Inspection")
        print("="*70)
        
        # Load frontend
        print("\n📍 Loading chatbot interface...")
        try:
            page.goto("http://localhost:3001", timeout=30000, wait_until="networkidle")
            time.sleep(3)
            take_screenshot(page, "01_homepage")
            print("  ✅ Homepage loaded")
        except Exception as e:
            print(f"  ❌ Failed to load: {e}")
            browser.close()
            return
        
        # Inspect page structure
        print("\n🔍 Analyzing page structure...")
        title = page.title()
        print(f"  Page title: {title}")
        
        # Try to find input elements
        inputs = page.query_selector_all("input, textarea, [contenteditable=true]")
        print(f"  Found {len(inputs)} input elements")
        
        if len(inputs) > 0:
            for i, elem in enumerate(inputs[:3]):
                try:
                    placeholder = page.evaluate(f"el => el.placeholder || el.getAttribute('aria-label') || el.getAttribute('data-testid')", elem)
                    tag = page.evaluate("el => el.tagName", elem)
                    print(f"    [{i}] <{tag}> placeholder='{placeholder}'")
                except:
                    pass
        
        # Try to find all buttons
        buttons = page.query_selector_all("button")
        print(f"  Found {len(buttons)} buttons")
        
        if len(buttons) > 0:
            for i, btn in enumerate(buttons[:5]):
                try:
                    text = page.evaluate("el => el.textContent || el.getAttribute('aria-label') || el.getAttribute('title')", btn)
                    print(f"    [{i}] Button: '{text.strip()}'")
                except:
                    pass
        
        browser.close()
        
        print("\n" + "="*70)
        print(f"✅ Screenshot saved to: {SCREENSHOTS_DIR}")
        print("="*70)

if __name__ == "__main__":
    run_browser_test()
