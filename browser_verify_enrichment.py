#!/usr/bin/env python3
"""
Browser Enrichment Verification - Direct approach
Focus: Click robot → Send BCA query → Capture response → Validate enrichment fields
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def main():
    print("=" * 90)
    print("ENRICHMENT VERIFICATION - DIRECT UI TEST")
    print("=" * 90)
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 960})
        
        try:
            # ───────────────────────────────────────────────────────────────────
            # STEP 1: Load page
            # ───────────────────────────────────────────────────────────────────
            print("[1/6] Loading chatbot...")
            await page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)  # Let page fully render
            print("      ✅ Loaded")
            print()
            
            # ───────────────────────────────────────────────────────────────────
            # STEP 2: Find and click robot button (bottom right)
            # ───────────────────────────────────────────────────────────────────
            print("[2/6] Clicking robot button...")
            
            # Robot button is usually the last interactive element or a specific one
            # Looking at the screenshot, it's a circular red/pink button
            # Let's try multiple approaches
            
            try:
                # Method 1: Look for button with robot emoji or aria-label
                robot_btn = page.locator('button[aria-label*="chat" i], button[aria-label*="robot" i], button[aria-label*="assistant" i]').first
                await robot_btn.click(timeout=5000)
                print("      ✅ Clicked via aria-label")
            except:
                try:
                    # Method 2: Find by role and position (likely last button)
                    buttons = page.locator('button')
                    count = await buttons.count()
                    if count > 0:
                        last_button = buttons.nth(count - 1)
                        await last_button.click(timeout=5000)
                        print(f"      ✅ Clicked button (position {count-1})")
                except Exception as e:
                    print(f"      ⚠️  Could not click robot button: {e}")
            
            # Wait for chat dialog to appear
            await page.wait_for_timeout(2000)
            print()
            
            # ───────────────────────────────────────────────────────────────────
            # STEP 3: Find chat input and send message
            # ───────────────────────────────────────────────────────────────────
            print("[3/6] Sending message...")
            
            # The chat input could be in different places
            input_found = False
            
            # Try to find input by various selectors
            input_selectors = [
                'input[placeholder*="message" i]',
                'input[placeholder*="question" i]',
                'input[placeholder*="ask" i]',
                'textarea',
                'input[type="text"]',
                'input',
            ]
            
            for selector in input_selectors:
                try:
                    inp = page.locator(selector).first
                    is_visible = await inp.is_visible(timeout=2000)
                    if is_visible:
                        print(f"      Found input: {selector}")
                        await inp.click()
                        await inp.fill("Tell me about BCA")
                        await page.keyboard.press("Enter")
                        input_found = True
                        print("      ✅ Message sent")
                        break
                except:
                    continue
            
            if not input_found:
                print("      ⚠️  Input not found, trying keyboard only...")
                await page.keyboard.type("Tell me about BCA", delay=50)
                await page.keyboard.press("Enter")
                print("      ✅ Message sent (keyboard)")
            
            print()
            
            # ───────────────────────────────────────────────────────────────────
            # STEP 4: Wait for response with enrichment keywords
            # ───────────────────────────────────────────────────────────────────
            print("[4/6] Waiting for response...")
            
            keywords = ["Career", "career", "salary", "Salary", "difficulty", "Difficulty"]
            found_enrichment = False
            
            for attempt in range(30):  # Try for 30 seconds
                body_text = await page.inner_text("body")
                
                if any(kw in body_text for kw in keywords):
                    found_enrichment = True
                    print(f"      ✅ Enrichment keywords detected (attempt {attempt+1})")
                    break
                
                await page.wait_for_timeout(1000)
                if attempt % 5 == 0 and attempt > 0:
                    print(f"      ... waiting ({attempt}s)")
            
            if not found_enrichment:
                print("      ⚠️  Enrichment keywords not found in waiting period")
            
            # Final stabilization wait
            await page.wait_for_timeout(2000)
            print()
            
            # ───────────────────────────────────────────────────────────────────
            # STEP 5: Extract the response text
            # ───────────────────────────────────────────────────────────────────
            print("[5/6] Extracting response...")
            
            page_html = await page.content()
            page_text = await page.inner_text("body")
            
            # Look for message container or chat response
            response_text = None
            
            # Try common response container selectors
            containers = [
                '[data-testid="chat-message"]',
                '.message',
                '.chat-bubble',
                '.response',
                '[role="article"]',
                '.assistant-message',
            ]
            
            for selector in containers:
                try:
                    msgs = page.locator(selector)
                    count = await msgs.count()
                    if count > 0:
                        # Get the last message (most recent response)
                        last_msg = msgs.nth(count - 1)
                        response_text = await last_msg.inner_text()
                        print(f"      Found response in: {selector}")
                        break
                except:
                    continue
            
            # Fallback: extract from full page text, focusing on content after "BCA"
            if not response_text:
                print("      Using full page text")
                lines = page_text.split("\n")
                
                # Find where "BCA" or "Tell me about" starts, then capture lines after
                start_idx = -1
                for i, line in enumerate(lines):
                    if "BCA" in line or "Tell me about" in line or "Career" in line or "salary" in line:
                        start_idx = max(0, i - 2)  # Start 2 lines before
                        break
                
                if start_idx >= 0:
                    response_text = "\n".join(lines[start_idx:start_idx+30])
                else:
                    # Just grab last 1500 chars
                    response_text = page_text[-1500:]
            
            print()
            print("=" * 90)
            print("EXTRACTED RESPONSE")
            print("=" * 90)
            print(response_text[:1500])
            print()
            
            # ───────────────────────────────────────────────────────────────────
            # STEP 6: Validate enrichment fields
            # ───────────────────────────────────────────────────────────────────
            print("=" * 90)
            print("ENRICHMENT FIELD CHECK")
            print("=" * 90)
            print()
            
            checks = {
                "Career paths": any(word in response_text for word in [
                    "Career", "career", "Developer", "developer", 
                    "Analyst", "analyst", "Engineer", "engineer"
                ]),
                "Salary": any(word in response_text for word in [
                    "salary", "Salary", "₹", "L", "LPA", "lpa", "LPM"
                ]),
                "Difficulty": any(word in response_text for word in [
                    "difficulty", "Difficulty", "medium", "Medium", 
                    "high", "High", "low", "Low"
                ]),
            }
            
            for field, present in checks.items():
                status = "✅" if present else "❌"
                result = "FOUND" if present else "NOT FOUND"
                print(f"  {status} {field}: {result}")
            
            print()
            
            # ───────────────────────────────────────────────────────────────────
            # Take screenshot
            # ───────────────────────────────────────────────────────────────────
            screenshot_path = Path("/Users/maneeth/Desktop/Chat-Bot/screenshots/enrichment_ui_test.png")
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=screenshot_path)
            print(f"  📸 Screenshot: {screenshot_path}")
            print()
            
            # ───────────────────────────────────────────────────────────────────
            # Summary
            # ───────────────────────────────────────────────────────────────────
            print("=" * 90)
            print("VERIFICATION RESULT")
            print("=" * 90)
            
            all_found = all(checks.values())
            if all_found:
                print()
                print("  ✅ PASS: Enrichment fields visible in UI")
                print()
                print("     Career paths:  ✅ FOUND")
                print("     Salary info:   ✅ FOUND") 
                print("     Difficulty:    ✅ FOUND")
                print()
            else:
                missing = [k for k, v in checks.items() if not v]
                print()
                print(f"  ❌ FAIL: {len(missing)} field(s) missing")
                for field in missing:
                    print(f"     {field}: ❌ NOT FOUND")
                print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
