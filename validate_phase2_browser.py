#!/usr/bin/env python3
"""
PHASE 2 VALIDATION MODE - BROWSER BEHAVIOR TEST
Prove enriched dataset improves REAL system behavior in browser
NO CODE CHANGES - OBSERVATION ONLY
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

async def main():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Playwright not installed. Installing...")
        import subprocess
        subprocess.run(["pip", "install", "playwright"], check=True)
        from playwright.async_api import async_playwright

    screenshots_dir = Path("/Users/maneeth/Desktop/Chat-Bot/screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    
    print("=" * 90)
    print("PHASE 2 VALIDATION MODE - BROWSER BEHAVIOR TEST")
    print("=" * 90)
    print("\n🎬 Starting headless browser test with enriched data")
    print(f"📸 Screenshots will be saved to: {screenshots_dir}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("\n[1/6] Opening chatbot...")
        await page.goto("http://localhost:3000", timeout=10000)
        await page.wait_for_load_state("networkidle")
        print("✅ Page loaded")
        
        print("\n[2/6] Clicking robot button to open chat interface...")
        
        # Try to find and click the robot button
        buttons = await page.locator("button").all()
        print(f"  Found {len(buttons)} buttons")
        
        if len(buttons) > 1:
            try:
                # Click the second button (should be the robot widget, not the "-10 Issue" button)
                await buttons[1].click()
                print("  ✓ Clicked button 1 (robot widget)")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"  ⚠️  Error clicking button: {e}")
        
        # Take screenshot to see if chat opened
        await page.screenshot(path=str(screenshots_dir / "phase2_after_robot_click.png"))
        print("  📸 Screenshot: phase2_after_robot_click.png")
        
        print("\n[3/6] Looking for chat input element...")
        
        # Try multiple selectors for chat input
        chat_input = None
        selectors = [
            "input[type='text']",
            "textarea",
            "[contenteditable='true']",
            "[role='textbox']",
            "input"
        ]
        
        for selector in selectors:
            try:
                inputs = await page.locator(selector).all()
                if inputs:
                    chat_input = inputs[0]
                    print(f"  ✓ Found input: {selector} ({len(inputs)} elements)")
                    break
            except:
                pass
        
        if not chat_input:
            print("  ⚠️  Chat input not found")
            print("  Taking inspection screenshot...")
            await page.screenshot(path=str(screenshots_dir / "phase2_after_inspection.png"))
        
        # Print page structure for debugging
        print("\n[4/6] Page structure inspection...")
        page_content = await page.content()
        
        # Look for specific keywords indicating enriched responses
        has_word = {
            "career": "career" in page_content.lower(),
            "salary": "salary" in page_content.lower(),
            "difficulty": "difficulty" in page_content.lower(),
            "placement": "placement" in page_content.lower(),
            "fees": "fees" in page_content.lower()
        }
        
        print("  Keywords found on page:")
        for key, found in has_word.items():
            status = "✅" if found else "❌"
            print(f"    {status} {key}")
        
        if chat_input:
            print("\n[5/6] Testing message input...")
            
            try:
                # Try sending "I like coding"
                await chat_input.fill("I like coding")
                await chat_input.press("Enter")
                await asyncio.sleep(2)
                
                await page.screenshot(path=str(screenshots_dir / "phase2_step1_coding.png"))
                print("  ✓ Sent 'I like coding'")
                print("  📸 Screenshot: phase2_step1_coding.png")
            except Exception as e:
                print(f"  ❌ Error sending message: {e}")
        
        # Final screenshot
        print("\n[6/6] Taking final screenshot...")
        await page.screenshot(path=str(screenshots_dir / "phase2_final_state.png"))
        print("  📸 Screenshot: phase2_final_state.png")
        
        await browser.close()
        
        print("\n" + "=" * 90)
        print("VALIDATION COMPLETE")
        print("=" * 90)
        
        screenshots = sorted(screenshots_dir.glob("phase2_*.png"))
        print(f"\n📸 Screenshots saved ({len(screenshots)}):")
        for ss in screenshots:
            print(f"  • {ss.name}")
        
        print("\n⚠️  NEXT STEP: MANUAL INSPECTION")
        print("─" * 90)
        print("\nPlease open the screenshots to verify:")
        print("  1. Did robot widget click open a chat dialog?")
        print("  2. Can you see a message input field?")
        print("  3. Are enriched fields visible in responses?")
        print("     (career, salary, difficulty, placement, fees)")
        print("\nThen proceed with next action based on observations.")
        
        return True

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
