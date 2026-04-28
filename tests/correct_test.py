#!/usr/bin/env python3
"""
CORRECT Browser Test - Using CHAT input only (not onboarding fields)
"""

import asyncio
import subprocess
import time

def run():
    print("🚀 Running CORRECTED browser test...")
    
    test_script = '''
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        
        print("1. Loading page...")
        await page.goto("http://localhost:3000")
        await page.wait_for_timeout(1500)
        
        print("2. Clicking robot to open chat...")
        await page.click(".floating-robot-trigger")
        await page.wait_for_timeout(2000)
        
        print("3. Filling VALID onboarding data...")
        # Fill proper onboarding - NOT queries!
        await page.fill('input[name="name"]', 'John Doe')
        await page.fill('input[name="email"]', 'john@example.com')
        print("   Filled: John Doe, john@example.com")
        
        print("4. Submitting onboarding form...")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        print("   ✅ Onboarding complete")
        
        # NOW WAIT for chat input to appear
        print("5. Waiting for chat input to appear...")
        chat_input = await page.wait_for_selector(
            'input[placeholder*="Message"], input[placeholder*="Type"]', 
            timeout=10000
        )
        print("   ✅ Chat input ready!")
        
        # ==== CORRECT TEST: Send via CHAT INPUT ====
        
        print("\\n=== TEST 1: Core Routing ===")
        await chat_input.fill("what courses do you offer")
        await chat_input.press("Enter")
        await page.wait_for_timeout(8000)
        await page.screenshot(path="/tmp/proof_test_01_courses.png")
        
        print("\\n=== TEST 2: Curriculum RAG ===")
        await chat_input.fill("what subjects are in MCA")
        await chat_input.press("Enter")
        await page.wait_for_timeout(8000)
        await page.screenshot(path="/tmp/proof_test_02_mca.png")
        
        print("\\n=== TEST 3: Out-of-Scope Guard ===")
        await chat_input.fill("tell me about iit bombay")
        await chat_input.press("Enter")
        await page.wait_for_timeout(8000)
        await page.screenshot(path="/tmp/proof_test_03_outscope.png")
        
        print("\\n=== TEST 4: Fees ===")
        await chat_input.fill("mba fees please")
        await chat_input.press("Enter")
        await page.wait_for_timeout(8000)
        await page.screenshot(path="/tmp/proof_test_04_fees.png")
        
        print("\\n=== TEST 5: Hostel ===")
        await chat_input.fill("do you have hostel")
        await chat_input.press("Enter")
        await page.wait_for_timeout(8000)
        await page.screenshot(path="/tmp/proof_test_05_hostel.png")
        
        print("\\n=== TEST 6: Typo Handling ===")
        await chat_input.fill("wat corses do u hav")
        await chat_input.press("Enter")
        await page.wait_for_timeout(8000)
        await page.screenshot(path="/tmp/proof_test_06_typo.png")
        
        print("\\n✅ ALL 6 TESTS COMPLETE!")
        
        await browser.close()

asyncio.run(main())
'''
    
    result = subprocess.run(
        ["python3", "-c", test_script],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    print(result.stdout)
    if result.stderr:
        print("Warnings:", result.stderr[:200])
    
    # Verify screenshots
    import os
    proofs = sorted([f for f in os.listdir('/tmp') if f.startswith('proof_test_')])
    print(f"\n📸 Generated {len(proofs)} screenshots:")
    for p in proofs:
        print(f"  - {p}")

if __name__ == "__main__":
    run()