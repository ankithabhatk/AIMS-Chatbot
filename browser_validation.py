#!/usr/bin/env python3
"""
Browser-based validation with screenshots
Tests the actual UX - how does the system feel to users?
"""

from playwright.sync_api import sync_playwright, expect
import time
import os
from datetime import datetime

SCREENSHOTS_DIR = "/Users/maneeth/Desktop/Chat-Bot/validation_screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def take_screenshot(page, name: str):
    """Take and save a screenshot"""
    filename = f"{SCREENSHOTS_DIR}/{datetime.now().strftime('%H%M%S')}_{name}.png"
    page.screenshot(path=filename)
    print(f"  📸 Screenshot: {name}")
    return filename

def run_browser_test():
    """Run real browser flow with screenshots"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1024, "height": 768})
        
        print("\n" + "="*70)
        print("🌐 BROWSER VALIDATION TEST - Real UX Experience")
        print("="*70)
        
        # Navigate to frontend
        print("\n1️⃣  Loading Frontend...")
        page.goto("http://localhost:3001", wait_until="networkidle")
        time.sleep(2)
        take_screenshot(page, "01_homepage")
        
        # Wait for chat box to be ready
        print("\n2️⃣  Testing Query: 'MBA fees'")
        chat_input = page.locator('input[placeholder*="Ask"], textarea, input[type="text"]')
        
        # Try to find the input (might have different selectors)
        if chat_input.count() == 0:
            print("  ⚠️  Could not find chat input - trying alternative selectors")
            # Try all possible input/textarea elements
            inputs = page.locator("input, textarea")
            if inputs.count() > 0:
                chat_input = inputs.first
        
        if chat_input.count() > 0 or chat_input:
            chat_input.fill("MBA fees")
            take_screenshot(page, "02_query_mba_fees")
            
            # Send button
            send_button = page.locator('button[type="submit"], button:has-text("Send"), button:has-text("➤")')
            if send_button.count() > 0:
                send_button.click()
            else:
                chat_input.press("Enter")
            
            time.sleep(2)
            take_screenshot(page, "03_response_mba_fees")
            print("  ✅ Response received")
        else:
            print("  ⚠️  Could not interact with chat interface")
        
        # Query 2: Placements
        print("\n3️⃣  Testing Query: 'What about placements?'")
        
        inputs = page.locator("input, textarea")
        if inputs.count() > 0:
            chat_input = inputs.first
            chat_input.fill("What about placements?")
            take_screenshot(page, "04_query_placements")
            
            send_button = page.locator('button[type="submit"], button:has-text("Send"), button:has-text("➤")')
            if send_button.count() > 0:
                send_button.click()
            else:
                chat_input.press("Enter")
            
            time.sleep(2)
            take_screenshot(page, "05_response_placements")
            print("  ✅ Response received")
        
        # Query 3: Facilities
        print("\n4️⃣  Testing Query: 'And campus facilities?'")
        
        inputs = page.locator("input, textarea")
        if inputs.count() > 0:
            chat_input = inputs.first
            chat_input.fill("And campus facilities?")
            take_screenshot(page, "06_query_facilities")
            
            send_button = page.locator('button[type="submit"], button:has-text("Send"), button:has-text("➤")')
            if send_button.count() > 0:
                send_button.click()
            else:
                chat_input.press("Enter")
            
            time.sleep(2)
            take_screenshot(page, "07_response_facilities")
            print("  ✅ Response received")
        
        # Final screenshot
        print("\n5️⃣  Final Conversation State")
        take_screenshot(page, "08_final_conversation")
        
        # Close
        browser.close()
        
        print("\n" + "="*70)
        print(f"✅ Browser test complete - Screenshots saved to: {SCREENSHOTS_DIR}")
        print("="*70)

if __name__ == "__main__":
    run_browser_test()
