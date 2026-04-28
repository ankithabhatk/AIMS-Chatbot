#!/usr/bin/env python3
"""
Inspect UI structure to find correct selectors
"""
import time
from playwright.sync_api import sync_playwright

def inspect_ui():
    """Inspect the UI structure"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("[TEST] Opening app...")
        page.goto("http://localhost:3000", wait_until="networkidle")
        time.sleep(3)
        
        # Get page content
        print("\n[HTML STRUCTURE]:")
        html = page.content()
        
        # Save HTML for inspection
        with open("page_structure.html", "w") as f:
            f.write(html)
        print("[SAVED] page_structure.html")
        
        # Look for specific elements
        print("\n[LOOKING FOR ELEMENTS]:")
        
        # All buttons
        buttons = page.query_selector_all("button")
        print(f"\nButtons ({len(buttons)}):")
        for i, btn in enumerate(buttons[:10]):
            text = btn.text_content().strip()[:50]
            classes = btn.get_attribute("class") or ""
            print(f"  {i}: {text} | class={classes}")
        
        # All inputs
        inputs = page.query_selector_all("input, textarea")
        print(f"\nInputs ({len(inputs)}):")
        for i, inp in enumerate(inputs[:10]):
            type_attr = inp.get_attribute("type") or "text"
            placeholder = inp.get_attribute("placeholder") or ""
            print(f"  {i}: type={type_attr} | placeholder={placeholder}")
        
        # All divs with text
        print(f"\nDivs with 'BCA' or 'course':")
        divs = page.query_selector_all("div")
        for div in divs[:50]:
            text = div.text_content().strip()
            if any(word in text.lower() for word in ['bca', 'course', 'select', 'choose']):
                print(f"  {text[:80]}")
        
        # Take screenshot
        page.screenshot(path="test_screenshots/inspect_state.png")
        print("\n[SCREENSHOT] inspect_state.png")
        
        browser.close()

if __name__ == "__main__":
    inspect_ui()
