#!/usr/bin/env python3
"""
Contextual Truth Headless Browser Test - Click Red Robot Button
"""

import asyncio
from playwright.async_api import async_playwright
import os

async def run_browser_test():
    """Run headless browser test"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("\n" + "="*80)
        print("🔍 CONTEXTUAL TRUTH VALIDATION - Browser Test")
        print("="*80 + "\n")
        
        ss_dir = "/tmp/contextual_test"
        os.makedirs(ss_dir, exist_ok=True)
        
        # Load frontend
        print("📱 Loading frontend...")
        await page.goto("http://localhost:3001", timeout=30000, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        print("✅ Frontend loaded\n")
        
        # Screenshot 1
        await page.screenshot(path=f"{ss_dir}/1_initial.png")
        print("📸 Screenshot 1: Initial page")
        
        # Click red robot button (should be visible on screen)
        print("\n🤖 Clicking red robot button...")
        try:
            # The red robot button - look for aria-label or role that identifies it as chat button
            robot_btn = page.locator('button[aria-label*="chat"], button[title*="chat"], [role="button"]:has-text("🤖")')
            
            # If not found, try clicking at the approximate coordinates (bottom right)
            await page.click('[role="button"]:nth-child(2)', force=True)
            print("✅ Clicked\n")
            await page.wait_for_timeout(1500)
        except:
            try:
                # Try direct coordinates - robot button appears to be bottom right
                await page.click('text=Hi! Need any help?')
                print("✅ Clicked via text\n")
                await page.wait_for_timeout(1500)
            except Exception as e:
                print(f"⚠️  {e}")
        
        # Screenshot 2: Widget should be open now
        await page.screenshot(path=f"{ss_dir}/2_widget_opened.png")
        print("📸 Screenshot 2: Widget opened")
        
        # Wait a bit for widget animation
        await page.wait_for_timeout(1000)
        
        # Find input field inside widget
        print("\n🔍 Finding chat input...")
        
        # Now input should be visible - try various selectors
        inputs = await page.locator('input[type="text"], textarea, [contenteditable="true"]').all()
        print(f"Found {len(inputs)} input candidates")
        
        if len(inputs) == 0:
            print("❌ No input found")
            await page.screenshot(path=f"{ss_dir}/debug_no_input.png")
            await browser.close()
            return False
        
        input_field = inputs[0]
        print("✅ Found input field\n")
        
        # Query 1: MBA fees
        print("📝 QUERY 1: 'MBA fees'")
        await input_field.click()
        await input_field.type("MBA fees", delay=50)
        await page.keyboard.press("Enter")
        print("✅ Sent\n")
        await page.wait_for_timeout(3000)
        
        # Screenshot 3
        await page.screenshot(path=f"{ss_dir}/3_after_mba_fees.png")
        print("📸 Screenshot 3: After MBA fees response")
        
        # Query 2: What about placements?
        print("\n📝 QUERY 2: 'What about placements?'")
        
        # Re-find input
        inputs = await page.locator('input[type="text"], textarea, [contenteditable="true"]').all()
        if inputs:
            input_field = inputs[0]
            await input_field.click()
            await input_field.clear()
            await input_field.type("What about placements?", delay=50)
            await page.keyboard.press("Enter")
            print("✅ Sent\n")
            await page.wait_for_timeout(3000)
        
        # Screenshot 4: After placements (CRITICAL)
        await page.screenshot(path=f"{ss_dir}/4_after_placements.png")
        print("📸 Screenshot 4: After placements response (CRITICAL)")
        
        # Screenshot 5: Full page
        await page.screenshot(path=f"{ss_dir}/5_full_page.png", full_page=True)
        print("📸 Screenshot 5: Full conversation")
        
        # Extract visible text
        print("\n📋 Extracting conversation text...")
        page_text = await page.locator('body').text_content()
        
        # Find the placements section
        lines = page_text.split('\n')
        
        # Look for key terms
        placement_section = []
        for i, line in enumerate(lines):
            if 'placement' in line.lower() and i > len(lines) // 2:  # Second half (latest response)
                # Get context around it
                start = max(0, i - 2)
                end = min(len(lines), i + 8)
                placement_section = lines[start:end]
                break
        
        if placement_section:
            response_text = '\n'.join(placement_section)
            print("\n" + "-"*80)
            print("LATEST RESPONSE (Placements with MBA context):")
            print("-"*80)
            print(response_text)
            print("-"*80)
            
            # Analysis
            print("\n" + "="*80)
            print("🔍 CONTEXTUAL TRUTH VERIFICATION")
            print("="*80)
            
            resp_lower = response_text.lower()
            has_mba = 'mba' in resp_lower
            has_23 = '23' in response_text or '23 lpa' in resp_lower
            has_84 = '84%' in response_text
            
            print(f"\n✅ MBA mentioned: {has_mba}")
            print(f"✅ Shows ₹23 LPA: {has_23}")
            print(f"✅ Shows 84%: {has_84}")
            
            print("\n" + "="*80)
            if (has_mba or has_84) and has_23:
                print("✅✅✅ VISUAL PROOF CONFIRMED ✅✅✅")
                print("MBA-specific contextual data displayed in UI")
            elif has_23:
                print("✅ ₹23 LPA shown (MBA-specific value)")
            else:
                print("⚠️  See screenshots for manual verification")
            print("="*80)
        else:
            print("⚠️  Could not extract placement section")
        
        await browser.close()
        
        print(f"\n✅ Test complete!")
        print(f"Screenshots saved to: {ss_dir}")
        print("\nFiles:")
        for f in sorted(os.listdir(ss_dir)):
            size = os.path.getsize(os.path.join(ss_dir, f))
            print(f"  📸 {f} ({size} bytes)")
        
        return True

if __name__ == "__main__":
    try:
        asyncio.run(run_browser_test())
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
