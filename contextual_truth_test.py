#!/usr/bin/env python3
"""
Contextual Truth Validation - Headless Browser Test
Tests: Is the system returning course-SPECIFIC data or generic overall data?

Exact Flow:
1. User: "MBA fees"
2. User: "What about placements?"
3. Capture screenshot
4. Extract: What placement package is shown? MBA-specific or overall?
"""

import asyncio
from playwright.async_api import async_playwright, Page
import time
from datetime import datetime
import base64

async def capture_element(page: Page, selector: str) -> str:
    """Capture text from an element"""
    try:
        element = page.locator(selector)
        if await element.count() > 0:
            return await element.text_content()
    except:
        pass
    return None

async def run_test():
    """Run contextual truth validation"""
    print("\n" + "="*80)
    print("🔍 CONTEXTUAL TRUTH VALIDATION - Headless Browser Test")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Testing: Is placement data MBA-specific or overall?\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate to frontend
        print("📱 Starting browser session at localhost:3001...")
        try:
            await page.goto("http://localhost:3001", timeout=15000, wait_until="networkidle")
        except Exception as e:
            print(f"❌ Failed to load frontend: {e}")
            await browser.close()
            return False
        
        # Give time for page to fully load
        await page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Find and click chat button
        print("🤖 Looking for chat widget button...")
        chat_button = page.locator('button:has-text("Robot")') or page.locator('[aria-label*="chat"]') or page.locator('button:nth-child(1)')
        
        try:
            await chat_button.click(timeout=5000)
            print("✅ Chat opened")
            await page.wait_for_timeout(1000)
        except Exception as e:
            print(f"⚠️  Could not click button: {e}")
        
        # Query 1: MBA fees
        print("\n" + "-"*80)
        print("📝 QUERY 1: 'MBA fees'")
        print("-"*80)
        
        # Find input and send query
        input_field = page.locator('input[type="text"]') or page.locator('[placeholder*="Ask"]') or page.locator('textarea')
        
        try:
            await input_field.fill("MBA fees", timeout=5000)
            await page.keyboard.press("Enter")
            print("✅ Query sent")
            await page.wait_for_timeout(3000)  # Wait for response
        except Exception as e:
            print(f"❌ Error sending query: {e}")
        
        # Capture response 1
        response_area = page.locator('[role="article"]') or page.locator('.response') or page.locator('div:has-text("₹")')
        resp1_text = await capture_element(page, '[role="article"]')
        if not resp1_text:
            resp1_text = await capture_element(page, 'div')
        
        print(f"Response 1 captured ({len(resp1_text) if resp1_text else 0} chars)")
        if resp1_text:
            print(f"Content preview: {resp1_text[:200]}...")
        
        # Query 2: What about placements?
        print("\n" + "-"*80)
        print("📝 QUERY 2: 'What about placements?'")
        print("-"*80)
        
        try:
            await input_field.fill("What about placements?", timeout=5000)
            await page.keyboard.press("Enter")
            print("✅ Query sent")
            await page.wait_for_timeout(3000)  # Wait for response
        except Exception as e:
            print(f"❌ Error sending query: {e}")
        
        # Capture response 2 (the critical one)
        await page.wait_for_timeout(1000)
        
        # Get all text on page to find the latest response
        page_content = await page.content()
        
        # Try multiple selectors to find the response
        selectors = [
            'div:last-child:has-text("placement")',
            '[role="article"]:last-of-type',
            'div:has-text("LPA")',
            'div:has-text("₹")'
        ]
        
        resp2_text = None
        for selector in selectors:
            try:
                resp2_text = await page.locator(selector).last.text_content()
                if resp2_text and len(resp2_text) > 20:
                    break
            except:
                pass
        
        # Fallback: get all visible text and find placement response
        if not resp2_text:
            all_elements = await page.locator('div, p, span').all()
            for elem in reversed(all_elements[-20:]):  # Check last 20 elements
                try:
                    text = await elem.text_content()
                    if text and ("placement" in text.lower() or "lpa" in text.lower()):
                        resp2_text = text
                        break
                except:
                    pass
        
        print(f"Response 2 captured ({len(resp2_text) if resp2_text else 0} chars)")
        if resp2_text:
            print(f"\n📋 Placement Response Content:")
            print("-"*80)
            print(resp2_text)
            print("-"*80)
        
        # Screenshot
        print("\n📸 Taking screenshot...")
        screenshot_path = "/tmp/contextual_truth_test.png"
        await page.screenshot(path=screenshot_path)
        print(f"✅ Screenshot saved: {screenshot_path}")
        
        # Analysis
        print("\n" + "="*80)
        print("🔍 CONTEXTUAL TRUTH ANALYSIS")
        print("="*80)
        
        if resp2_text:
            resp2_lower = resp2_text.lower()
            
            # Check for course-specific indicators
            has_mba_specific = "mba" in resp2_lower or "highest: ₹23" in resp2_lower
            has_overall = "overall" in resp2_lower or "highest: ₹27" in resp2_lower
            has_lpa = "lpa" in resp2_lower
            has_salary = "salary" in resp2_lower or "₹" in resp2_text
            
            print(f"\n✅ Found 'LPA': {has_lpa}")
            print(f"✅ Found salary data: {has_salary}")
            print(f"✅ Found 'MBA' specific: {has_mba_specific}")
            print(f"⚠️  Found 'overall' (generic): {has_overall}")
            
            # Extract package value
            import re
            packages = re.findall(r'₹(\d+)\s*(?:lpa|lakhs?)?', resp2_text, re.IGNORECASE)
            if packages:
                print(f"\n💰 Package values found: {packages}")
                if "23" in packages or "23" in resp2_text.lower():
                    print("✅ CORRECT: Shows MBA-specific ₹23 LPA")
                    contextual_correct = True
                elif "27" in packages or "27" in resp2_text.lower():
                    print("❌ INCORRECT: Shows overall ₹27 LPA (not MBA-specific)")
                    contextual_correct = False
                else:
                    print(f"⚠️  Unknown value: {packages[0]}")
                    contextual_correct = None
            else:
                print("⚠️  No package value found")
                contextual_correct = None
            
            print("\n" + "="*80)
            if contextual_correct is True:
                print("🟢 CONTEXTUAL TRUTH VERIFIED - System returns course-specific data ✅")
            elif contextual_correct is False:
                print("🔴 CONTEXTUAL TRUTH FAILED - System returns generic overall data ❌")
            else:
                print("🟡 CONTEXTUAL TRUTH UNCLEAR - Need manual review")
            print("="*80)
        else:
            print("❌ Could not capture placement response")
        
        await browser.close()
        return resp2_text

async def main():
    result = await run_test()
    if result:
        print(f"\n✅ Test complete. Response:\n{result}")
    else:
        print("\n❌ Test failed")

if __name__ == "__main__":
    asyncio.run(main())
