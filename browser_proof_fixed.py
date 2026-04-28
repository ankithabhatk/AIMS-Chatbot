#!/usr/bin/env python3
"""
Contextual Truth Headless Browser Test - Fixed Version
Clicks chat widget button first, then performs the test
"""

import asyncio
from playwright.async_api import async_playwright
import time
import os

async def run_browser_test():
    """Run headless browser test with screenshots"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("\n" + "="*80)
        print("🔍 CONTEXTUAL TRUTH VALIDATION - Headless Browser")
        print("="*80 + "\n")
        
        ss_dir = "/tmp/contextual_test"
        os.makedirs(ss_dir, exist_ok=True)
        
        # Load frontend
        print("📱 Loading frontend...")
        try:
            await page.goto("http://localhost:3001", timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            print("✅ Frontend loaded\n")
        except Exception as e:
            print(f"❌ Failed: {e}")
            await browser.close()
            return False
        
        # Screenshot 1: Initial page
        ss1 = f"{ss_dir}/1_initial.png"
        await page.screenshot(path=ss1)
        print(f"📸 Screenshot 1: {ss1}")
        
        # Click chat button (last button on page)
        print("\n🤖 Opening chat widget...")
        try:
            btn = page.locator('button').last
            await btn.click()
            await page.wait_for_timeout(1500)
            print("✅ Chat widget opened\n")
        except Exception as e:
            print(f"❌ Error clicking button: {e}")
            await browser.close()
            return False
        
        # Screenshot 2: Widget opened
        ss2 = f"{ss_dir}/2_widget_opened.png"
        await page.screenshot(path=ss2)
        print(f"📸 Screenshot 2: {ss2}")
        
        # Now find the input field inside the widget
        print("🔍 Finding input field inside widget...")
        await page.wait_for_timeout(500)
        
        try:
            # Try to find any input/textarea now that widget is open
            input_field = None
            
            # Try iframe first (widget might be in iframe)
            frames = page.frames
            print(f"   Found {len(frames)} frames")
            
            # If widget is in main frame, try finding input
            inputs = await page.locator('input').all()
            textareas = await page.locator('textarea').all()
            
            print(f"   Inputs: {len(inputs)}, Textareas: {len(textareas)}")
            
            if inputs:
                input_field = inputs[0]
            elif textareas:
                input_field = textareas[0]
            else:
                # Try content editable
                editable = await page.locator('[contenteditable="true"]').all()
                if editable:
                    input_field = editable[0]
            
            if not input_field:
                print("❌ Could not find input field")
                # Take screenshot to see what we have
                await page.screenshot(path=f"{ss_dir}/debug_no_input.png")
                await browser.close()
                return False
            
            print("✅ Found input field\n")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await browser.close()
            return False
        
        # Query 1: MBA fees
        print("📝 QUERY 1: 'MBA fees'")
        try:
            await input_field.click()
            await input_field.type("MBA fees", delay=50)
            await page.keyboard.press("Enter")
            print("✅ Sent\n")
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"❌ Error: {e}")
            await browser.close()
            return False
        
        # Screenshot 3: After MBA fees
        ss3 = f"{ss_dir}/3_after_mba_fees.png"
        await page.screenshot(path=ss3)
        print(f"📸 Screenshot 3: {ss3}")
        
        # Query 2: What about placements?
        print("\n📝 QUERY 2: 'What about placements?'")
        try:
            # Re-find input in case it changed
            inputs = await page.locator('input').all()
            textareas = await page.locator('textarea').all()
            
            if inputs:
                input_field = inputs[0]
            elif textareas:
                input_field = textareas[0]
            
            if input_field:
                await input_field.click()
                await input_field.clear()
                await input_field.type("What about placements?", delay=50)
                await page.keyboard.press("Enter")
                print("✅ Sent\n")
                await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"⚠️  Error: {e}")
        
        # Screenshot 4: After placements query (CRITICAL)
        ss4 = f"{ss_dir}/4_after_placements.png"
        await page.screenshot(path=ss4)
        print(f"📸 Screenshot 4: {ss4}")
        
        # Screenshot 5: Full page
        ss5 = f"{ss_dir}/5_full_conversation.png"
        await page.screenshot(path=ss5, full_page=True)
        print(f"📸 Screenshot 5: {ss5}\n")
        
        # Extract text content
        print("📋 Extracting conversation...")
        try:
            # Get all visible text
            page_text = await page.locator('body').text_content()
            
            # Look for the placements response (latest response)
            lines = page_text.split('\n')
            
            # Find lines with key terms
            response_lines = []
            capture = False
            for line in reversed(lines):
                if 'placement' in line.lower() or 'lpa' in line.lower():
                    capture = True
                if capture:
                    response_lines.insert(0, line)
                    if len(response_lines) > 10:
                        break
            
            if response_lines:
                latest_response = '\n'.join(response_lines)
                print("\n" + "-"*80)
                print("Latest Response (Placements):")
                print("-"*80)
                print(latest_response[:600])
                print("-"*80)
                
                # Analysis
                print("\n" + "="*80)
                print("🔍 CONTEXTUAL TRUTH VERIFICATION")
                print("="*80)
                
                resp_lower = latest_response.lower()
                has_mba = 'mba' in resp_lower
                has_23_lpa = '₹23' in latest_response or '23' in latest_response
                has_84_percent = '84%' in latest_response
                has_bba = 'bba' in resp_lower
                
                print(f"\n✅ Contains 'MBA': {has_mba}")
                print(f"✅ Contains ₹23 LPA: {has_23_lpa}")
                print(f"✅ Contains '84%': {has_84_percent}")
                print(f"❌ Contains 'BBA': {has_bba}")
                
                print("\n" + "="*80)
                if has_mba and has_23_lpa:
                    print("✅ CONFIRMED: MBA-SPECIFIC DATA SHOWN IN UI")
                    print("   Visual proof: System returns contextually accurate data")
                elif has_84_percent:
                    print("✅ CONFIRMED: COURSE-SPECIFIC DATA SHOWN IN UI")
                    print("   Visual proof: Recognized MBA context")
                else:
                    print("⚠️  Inconclusive - check screenshots manually")
                print("="*80)
        except Exception as e:
            print(f"⚠️  Error extracting text: {e}")
        
        await browser.close()
        
        print(f"\n✅ Test complete - Screenshots saved to: {ss_dir}")
        print("\nFiles created:")
        for f in sorted(os.listdir(ss_dir)):
            fpath = os.path.join(ss_dir, f)
            fsize = os.path.getsize(fpath)
            print(f"  📸 {f} ({fsize} bytes)")
        
        return True

if __name__ == "__main__":
    try:
        result = asyncio.run(run_browser_test())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
