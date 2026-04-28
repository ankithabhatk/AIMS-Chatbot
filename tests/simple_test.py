#!/usr/bin/env python3
"""
Simple Browser Test - Get actual screenshots proof
"""

import subprocess
import time
import os
from pathlib import Path

def run():
    output_dir = Path("/tmp/final_proof")
    output_dir.mkdir(exist_ok=True)
    
    # Kill any existing chrome instances
    subprocess.run("pkill -f chromium 2>/dev/null", shell=True)
    time.sleep(1)
    
    # Use chromium with remote debugging to capture network
    print("🚀 Starting browser test...")
    
    test_script = '''
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # NOT headless - show browser!
            args=['--disable-blink-features=Animation']
        )
        context = await browser.new_context(
            viewport={"width": 1400, "height": 900}
        )
        page = await context.new_page()
        
        # Navigate to chat
        print("Loading page...")
        await page.goto("http://localhost:3000", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await page.screenshot(full_page=True, path="/tmp/final_proof/01_home.png")
        
        # Click robot button to open chat
        print("Clicking robot...")
        
        try:
            # Try several ways to click
            for selector in [".floating-robot-trigger", "[class*='robot']", "button:has-text('🤖')"]:
                try:
                    await page.click(selector, timeout=2000)
                    print(f"Clicked: {selector}")
                    break
                except:
                    continue
            
            await page.wait_for_timeout(2000)
            await page.screenshot(full_page=True, path="/tmp/final_proof/02_opened.png")
        except Exception as e:
            print(f"Click error: {e}")
        
        # Wait for welcome/onboarding to appear
        print("Waiting for chat...")
        await page.wait_for_timeout(3000)
        
        # Try to find and fill input
        print("Looking for input...")
        
        # Type query directly
        await page.keyboard.type("what courses do you offer", delay=100)
        await page.wait_for_timeout(500)
        await page.keyboard.press("Enter")
        
        print("Waiting for response...")
        await page.wait_for_timeout(8000)
        
        # Check for response in page
        await page.screenshot(full_page=True, path="/tmp/final_proof/03_courses.png")
        
        # Print what we see
        content = await page.content()
        has_courses = "MBA" in content or "courses" in content
        print(f"Has courses content: {has_courses}")
        
        # Second query
        await page.keyboard.type("mba fees please", delay=100)
        await page.wait_for_timeout(500)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(5000)
        await page.screenshot(full_page=True, path="/tmp/final_proof/04_fees.png")
        
        # Third query - out of scope
        await page.keyboard.type("tell me about iit bombay", delay=100)
        await page.wait_for_timeout(500)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(5000)
        await page.screenshot(full_page=True, path="/tmp/final_proof/05_out_of_scope.png")
        
        # Fourth - hostel
        await page.keyboard.type("do you have hostel", delay=100)
        await page.wait_for_timeout(500)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(5000)
        await page.screenshot(full_page=True, path="/tmp/final_proof/06_hostel.png")
        
        await browser.close()
        print("Done!")

asyncio.run(main())
'''
    
    # Run the test
    result = subprocess.run(
        ["python3", "-c", test_script],
        capture_output=True,
        text=True,
        timeout=90
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr[:500])
    
    # Show the screenshots
    screenshots = sorted(output_dir.glob("*.png"))
    print(f"\n📸 Generated {len(screenshots)} screenshots:")
    for s in screenshots:
        print(f"  - {s.name}")

if __name__ == "__main__":
    run()