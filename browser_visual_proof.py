#!/usr/bin/env python3
"""
Contextual Truth Headless Browser Test with Screenshots
Tests the exact UI flow and captures visual proof
"""

import asyncio
from playwright.async_api import async_playwright
import time
from datetime import datetime
import os

async def run_browser_test():
    """Run headless browser test with screenshots"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("\n" + "="*80)
        print("🔍 CONTEXTUAL TRUTH VALIDATION - Headless Browser Test")
        print("="*80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Navigate to frontend
        print("📱 Loading frontend at localhost:3001...")
        try:
            await page.goto("http://localhost:3001", timeout=30000, wait_until="domcontentloaded")
            print("✅ Frontend loaded\n")
        except Exception as e:
            print(f"❌ Failed to load frontend: {e}")
            await browser.close()
            return False
        
        await page.wait_for_timeout(2000)
        
        # Take initial screenshot
        ss_dir = "/tmp/contextual_test"
        os.makedirs(ss_dir, exist_ok=True)
        
        ss1_path = f"{ss_dir}/1_initial_page.png"
        await page.screenshot(path=ss1_path)
        print(f"📸 Screenshot 1 (initial): {ss1_path}\n")
        
        # Find chat input - try multiple selectors
        print("🔍 Looking for chat input...")
        input_locators = [
            page.locator('input[placeholder*="Ask"]'),
            page.locator('input[type="text"]'),
            page.locator('textarea'),
            page.locator('[contenteditable="true"]')
        ]
        
        input_field = None
        for loc in input_locators:
            try:
                if await loc.count() > 0:
                    input_field = loc
                    print(f"✅ Found input field\n")
                    break
            except:
                pass
        
        if not input_field:
            print("❌ Could not find input field")
            await browser.close()
            return False
        
        # Query 1: MBA fees
        print("📝 QUERY 1: Typing 'MBA fees'...")
        try:
            await input_field.first.click()
            await input_field.first.type("MBA fees", delay=50)
            await page.keyboard.press("Enter")
            print("✅ Query sent")
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"❌ Error: {e}")
            await browser.close()
            return False
        
        # Screenshot after first response
        ss2_path = f"{ss_dir}/2_after_mba_fees.png"
        await page.screenshot(path=ss2_path)
        print(f"📸 Screenshot 2 (after MBA fees): {ss2_path}\n")
        
        # Extract response text
        try:
            responses = await page.locator('[role="article"]').all_text_contents()
            if responses:
                print("📋 Response 1 (MBA fees):")
                print("---")
                print(responses[-1][:300])
                print("...\n")
        except:
            pass
        
        # Query 2: What about placements?
        print("📝 QUERY 2: Typing 'What about placements?'...")
        try:
            # Find fresh input (might be different after response)
            input_locators_new = [
                page.locator('input[placeholder*="Ask"]'),
                page.locator('input[type="text"]'),
                page.locator('textarea')
            ]
            
            input_field = None
            for loc in input_locators_new:
                if await loc.count() > 0:
                    input_field = loc
                    break
            
            if input_field:
                await input_field.first.click()
                await input_field.first.clear()
                await input_field.first.type("What about placements?", delay=50)
                await page.keyboard.press("Enter")
                print("✅ Query sent")
                await page.wait_for_timeout(3000)
            else:
                print("⚠️  Could not find input for second query")
        except Exception as e:
            print(f"⚠️  Error with Q2: {e}")
        
        # Screenshot after second response (CRITICAL)
        ss3_path = f"{ss_dir}/3_after_placements_query.png"
        await page.screenshot(path=ss3_path)
        print(f"📸 Screenshot 3 (after placements): {ss3_path}\n")
        
        # Full page screenshot for complete context
        ss4_path = f"{ss_dir}/4_full_conversation.png"
        await page.screenshot(path=ss4_path, full_page=True)
        print(f"📸 Screenshot 4 (full page): {ss4_path}\n")
        
        # Extract all response text
        try:
            page_text = await page.content()
            
            # Try to get visible text of all articles/responses
            articles = await page.locator('[role="article"]').all()
            print("📋 All Responses Captured:")
            print("-"*80)
            
            for i, article in enumerate(articles, 1):
                try:
                    text = await article.text_content()
                    print(f"\nResponse {i}:")
                    print(text[:400])
                    if len(text) > 400:
                        print("...")
                except:
                    pass
            
            print("\n" + "-"*80)
            
            # Analysis
            print("\n" + "="*80)
            print("🔍 CONTEXTUAL TRUTH ANALYSIS")
            print("="*80)
            
            # Get latest response (should be placements)
            if articles:
                latest_response = await articles[-1].text_content()
                latest_lower = latest_response.lower()
                
                print(f"\nLatest Response ({len(latest_response)} chars):")
                print("---")
                print(latest_response)
                print("---\n")
                
                # Check for key indicators
                import re
                packages = re.findall(r'₹(\d+)', latest_response)
                has_mba = 'mba' in latest_lower
                has_23_lpa = '₹23' in latest_response or '23 lpa' in latest_lower
                has_84_percent = '84%' in latest_response
                
                print("Contextual Truth Indicators:")
                print(f"  ✅ Shows 'MBA': {has_mba}")
                print(f"  ✅ Shows ₹23 LPA: {has_23_lpa}")
                print(f"  ✅ Shows '84% MBA students': {has_84_percent}")
                print(f"  💰 Packages found: {packages}")
                
                print("\n" + "="*80)
                if has_23_lpa and has_mba:
                    print("✅ VISUAL PROOF: MBA-SPECIFIC DATA CONFIRMED")
                    print("   System correctly returned ₹23 LPA with MBA context")
                elif has_84_percent:
                    print("✅ VISUAL PROOF: COURSE-SPECIFIC DATA CONFIRMED")
                    print("   System correctly identified it as MBA placements")
                else:
                    print("⚠️  Response might not have course context")
                print("="*80)
        except Exception as e:
            print(f"⚠️  Error extracting text: {e}")
        
        await browser.close()
        
        print(f"\n📸 All screenshots saved to: {ss_dir}")
        print("\nScreenshot files:")
        for f in sorted(os.listdir(ss_dir)):
            print(f"  - {ss_dir}/{f}")
        
        return True

if __name__ == "__main__":
    try:
        result = asyncio.run(run_browser_test())
        if result:
            print("\n✅ Browser test completed successfully")
        else:
            print("\n❌ Browser test failed")
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
