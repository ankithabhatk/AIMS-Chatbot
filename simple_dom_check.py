#!/usr/bin/env python3
"""
Simple DOM check: Load page, search for enrichment keywords in HTML
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def main():
    print("=" * 90)
    print("SIMPLE DOM CHECK: Enrichment content anywhere on page?")
    print("=" * 90)
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 960})
        
        try:
            # Load page
            print("Loading page...")
            await page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            print("✅ Loaded\n")
            
            # Get full HTML
            html_content = await page.content()
            body_text = await page.inner_text("body")
            
            print(f"HTML size: {len(html_content)} bytes")
            print(f"Body text size: {len(body_text)} bytes")
            print()
            
            # Search for enrichment keywords
            keywords_to_check = {
                "Career": ["Developer", "Analyst", "Engineer", "Manager", "Director"],
                "Salary": ["₹", "LPA", "salary", "Salary"],
                "Difficulty": ["Difficulty", "difficulty", "medium", "high", "low"],
            }
            
            print("=" * 90)
            print("KEYWORD SEARCH IN PAGE HTML+TEXT")
            print("=" * 90)
            print()
            
            for category, words in keywords_to_check.items():
                found_words = [w for w in words if w in html_content]
                if found_words:
                    print(f"✅ {category}: Found {len(found_words)} word(s)")
                    print(f"   {', '.join(found_words)}")
                else:
                    print(f"❌ {category}: Not found in HTML")
            
            print()
            
            # Try clicking the chat button that should be on the page
            print("=" * 90)
            print("ATTEMPTING TO INTERACT WITH CHAT")
            print("=" * 90)
            print()
            
            # Look for any button
            buttons = page.locator("button")
            button_count = await buttons.count()
            print(f"Found {button_count} buttons on page")
            
            # Try to find a button with chat/robot/assistant label
            for i in range(min(button_count, 5)):
                try:
                    btn = buttons.nth(i)
                    aria = await btn.get_attribute("aria-label")
                    data_test = await btn.get_attribute("data-testid")
                    content = await btn.inner_text()
                    print(f"  Button {i}: aria-label={aria}, data-testid={data_test}, text={content[:30]}")
                except:
                    pass
            
            print()
            print("=" * 90)
            print("PAGE STRUCTURE")
            print("=" * 90)
            print()
            
            # Get first 1000 chars of body text
            print("Body text (first 1500 chars):")
            print("-" * 90)
            print(body_text[:1500])
            print("-" * 90)
            print()
            
            # Take screenshot
            screenshot_path = Path("/Users/maneeth/Desktop/Chat-Bot/screenshots/dom_check.png")
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
