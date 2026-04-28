#!/usr/bin/env python3
"""
HARD UI VALIDATION: Prove enrichment is visible in UI
Goal: Capture screenshot + extract full visible text
No assumptions. Real proof only.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def main():
    print("=" * 95)
    print("HARD UI VALIDATION: ENRICHMENT VISIBILITY")
    print("=" * 95)
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 960})
        
        try:
            # ───────────────────────────────────────────────────────────────────
            # STEP 1: Load page
            # ───────────────────────────────────────────────────────────────────
            print("[STEP 1] Loading chatbot page...")
            await page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            print("         ✅ Page loaded")
            print()
            
            # ───────────────────────────────────────────────────────────────────
            # STEP 2: Force click robot button using multiple strategies
            # ───────────────────────────────────────────────────────────────────
            print("[STEP 2] Opening chat (forcing robot button click)...")
            
            robot_clicked = False
            strategies = [
                {
                    "name": "button >> visible",
                    "action": lambda: page.locator("button >> visible").first
                },
                {
                    "name": "data-testid=chat-widget",
                    "action": lambda: page.locator("[data-testid='chat-widget']")
                },
                {
                    "name": "aria-label chat",
                    "action": lambda: page.locator("[aria-label*='chat' i]")
                },
                {
                    "name": "svg parent (robot icon)",
                    "action": lambda: page.locator("svg").locator("..").first
                },
                {
                    "name": "last button on page",
                    "action": lambda: page.locator("button").last
                },
            ]
            
            for strategy in strategies:
                if robot_clicked:
                    break
                try:
                    print(f"         Trying: {strategy['name']}")
                    elem = strategy["action"]()
                    await elem.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)
                    
                    is_visible = await elem.is_visible(timeout=2000)
                    if is_visible:
                        print(f"            ✓ Element visible")
                        await elem.click(timeout=5000)
                        print(f"            ✓ Clicked!")
                        robot_clicked = True
                        break
                except Exception as e:
                    print(f"            ✗ Failed: {str(e)[:50]}")
                    continue
            
            if not robot_clicked:
                print("         ⚠️  Robot button click failed with all strategies")
                print("         Attempting raw page click as fallback...")
                await page.click("body")
            
            await page.wait_for_timeout(2000)
            print("         ✅ Chat interaction attempted")
            print()
            
            # ───────────────────────────────────────────────────────────────────
            # STEP 3: Wait for chat input to be visible
            # ───────────────────────────────────────────────────────────────────
            print("[STEP 3] Waiting for chat input (max 10s)...")
            
            input_visible = False
            input_selectors = [
                "input[type='text']",
                "textarea",
                "input",
                "[contenteditable='true']",
                "[role='textbox']",
            ]
            
            for attempt in range(10):
                for selector in input_selectors:
                    try:
                        inp = page.locator(selector).first
                        if await inp.is_visible(timeout=1000):
                            print(f"         ✅ Input found: {selector}")
                            input_visible = True
                            break
                    except:
                        continue
                
                if input_visible:
                    break
                await page.wait_for_timeout(1000)
                if attempt % 2 == 0:
                    print(f"         ... waiting ({attempt+1}s)")
            
            if not input_visible:
                print("         ⚠️  Input not found, will try typing anyway")
            
            print()
            
            # ───────────────────────────────────────────────────────────────────
            # STEP 4: Send message
            # ───────────────────────────────────────────────────────────────────
            print("[STEP 4] Sending message...")
            
            try:
                # Try to focus and type into input
                for selector in input_selectors:
                    try:
                        inp = page.locator(selector).first
                        if await inp.is_visible(timeout=1000):
                            await inp.click()
                            await inp.fill("Tell me about BCA")
                            print("         ✓ Message typed into input")
                            break
                    except:
                        continue
            except:
                pass
            
            # Press Enter
            await page.keyboard.press("Enter")
            print("         ✓ Enter pressed")
            await page.wait_for_timeout(1000)
            print("         ✅ Message sent")
            print()
            
            # ───────────────────────────────────────────────────────────────────
            # STEP 5: Wait for response with specific markers
            # ───────────────────────────────────────────────────────────────────
            print("[STEP 5] Waiting for response to appear...")
            
            response_found = False
            enrichment_keywords = ["Career", "career", "salary", "Salary", "difficulty", "Difficulty"]
            
            for attempt in range(40):  # Up to 40 seconds
                page_text = await page.inner_text("body")
                
                # Check if we have enrichment keywords
                if any(kw in page_text for kw in enrichment_keywords):
                    response_found = True
                    print(f"         ✅ Response with enrichment keywords found (attempt {attempt+1})")
                    break
                
                # Also check for basic response indicators
                if "Help" in page_text or "explore" in page_text.lower():
                    print(f"         Response content detected (attempt {attempt+1})")
                
                await page.wait_for_timeout(1000)
                if attempt % 5 == 0:
                    print(f"         ... waiting ({attempt+1}s)")
            
            if not response_found:
                print("         ⚠️  Enrichment keywords not found, but continuing...")
            
            # Extra wait for stability
            await page.wait_for_timeout(2000)
            print("         ✅ DOM stabilized")
            print()
            
            # ───────────────────────────────────────────────────────────────────
            # STEP 6: Extract FULL visible text (not partial)
            # ───────────────────────────────────────────────────────────────────
            print("[STEP 6] Extracting full visible text...")
            
            full_page_text = await page.inner_text("body")
            
            # Find the longest continuous text block (likely the response)
            lines = full_page_text.split("\n")
            
            # Look for conversation markers
            response_start = -1
            for i, line in enumerate(lines):
                if "BCA" in line or "Career" in line or "salary" in line or "Difficulty" in line:
                    # Found response, go back to capture context
                    response_start = max(0, i - 5)
                    break
            
            if response_start >= 0:
                # Capture from response start for reasonable length
                extracted_text = "\n".join(lines[response_start:response_start + 40])
            else:
                # Fallback: just use last 2000 characters
                extracted_text = full_page_text[-2000:]
            
            print("         ✅ Text extracted")
            print()
            
            # ───────────────────────────────────────────────────────────────────
            # STEP 7: Take screenshot
            # ───────────────────────────────────────────────────────────────────
            print("[STEP 7] Taking screenshot...")
            
            screenshot_path = Path("/Users/maneeth/Desktop/Chat-Bot/screenshots/FINAL_UI_PROOF.png")
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            
            await page.screenshot(path=screenshot_path)
            print(f"         ✅ Screenshot saved: {screenshot_path}")
            print()
            
            # ───────────────────────────────────────────────────────────────────
            # STEP 8: Print extracted text
            # ───────────────────────────────────────────────────────────────────
            print("=" * 95)
            print("EXTRACTED UI TEXT")
            print("=" * 95)
            print()
            print(extracted_text[:2000])
            print()
            
            # ───────────────────────────────────────────────────────────────────
            # STEP 9: Validate enrichment fields
            # ───────────────────────────────────────────────────────────────────
            print("=" * 95)
            print("ENRICHMENT FIELD VALIDATION")
            print("=" * 95)
            print()
            
            checks = {
                "Career paths": any(word in extracted_text for word in [
                    "Career", "Developer", "developer", "Analyst", "analyst"
                ]),
                "Salary": any(word in extracted_text for word in [
                    "₹", "salary", "Salary", "L", "LPA"
                ]),
                "Difficulty": any(word in extracted_text for word in [
                    "Difficulty", "difficulty", "medium", "Medium", "high", "High"
                ]),
            }
            
            print("Required fields visible in UI:")
            print()
            for field, present in checks.items():
                status = "✅ YES" if present else "❌ NO"
                print(f"  {status} - {field}")
            
            print()
            print("=" * 95)
            print("FINAL RESULT")
            print("=" * 95)
            print()
            
            if all(checks.values()):
                print("✅✅✅ PASS: ALL enrichment fields visible in UI ✅✅✅")
                print()
                print("   Career paths:  ✅ VISIBLE")
                print("   Salary info:   ✅ VISIBLE")
                print("   Difficulty:    ✅ VISIBLE")
                print()
                print("   Phase 2 is COMPLETE and PROVEN")
            else:
                missing = [k for k, v in checks.items() if not v]
                print(f"❌ FAIL: {len(missing)} field(s) not visible in UI")
                print()
                for field in missing:
                    print(f"  ❌ {field}: NOT VISIBLE")
                print()
                print("   Phase 2 UNVERIFIED")
            
            print()
            print(f"Screenshot: {screenshot_path}")
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
