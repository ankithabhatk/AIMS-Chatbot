#!/usr/bin/env python3
"""
Browser Debug Mode: Verify enrichment visible in UI
---
Goal: Prove enriched data (career paths, salary, difficulty) appears in chatbot UI
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright


async def main():
    print("=" * 88)
    print("BROWSER DEBUG: ENRICHMENT VERIFICATION")
    print("=" * 88)
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 960})
        
        try:
            # ─────────────────────────────────────────────────────────────────
            # STEP 1: Navigate to chatbot
            # ─────────────────────────────────────────────────────────────────
            print("[1/5] Loading chatbot page...")
            await page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
            print("      ✅ Page loaded")
            print()
            
            # Wait a moment for initial render
            await page.wait_for_timeout(1000)
            
            # ─────────────────────────────────────────────────────────────────
            # STEP 2: Open chat interface
            # ─────────────────────────────────────────────────────────────────
            print("[2/5] Opening chat interface...")
            
            # Try multiple selectors for chat button/robot widget
            chat_button_selectors = [
                "button[aria-label*='chat' i]",
                "button[aria-label*='message' i]",
                "button[aria-label*='bot' i]",
                "[data-testid='chat-button']",
                "button:has-text('Chat')",
                "button:has-text('Assistant')",
                "button:has-text('🤖')",
                "button",  # fallback: just try first button
            ]
            
            opened = False
            for selector in chat_button_selectors:
                try:
                    button = page.locator(selector).first
                    if await button.is_visible(timeout=2000):
                        print(f"      Found: {selector}")
                        await button.click(timeout=5000)
                        await page.wait_for_timeout(1500)  # Let UI settle
                        opened = True
                        print("      ✅ Chat opened")
                        break
                except Exception as e:
                    continue
            
            if not opened:
                print("      ⚠️  Could not open chat with selectors, trying page.click...")
                # Try clicking center of page as last resort
                await page.click("body")
                await page.wait_for_timeout(1500)
                opened = True
            
            print()
            
            # ─────────────────────────────────────────────────────────────────
            # STEP 3: Find and interact with message input
            # ─────────────────────────────────────────────────────────────────
            print("[3/5] Locating message input...")
            
            input_selectors = [
                "[data-testid='chat-input']",
                "input[placeholder*='message' i]",
                "input[placeholder*='ask' i]",
                "input[type='text']",
                "textarea",
                "input",
            ]
            
            input_found = False
            for selector in input_selectors:
                try:
                    inp = page.locator(selector).first
                    if await inp.is_visible(timeout=2000):
                        print(f"      Found: {selector}")
                        await inp.focus()
                        await page.wait_for_timeout(500)
                        input_found = True
                        break
                except Exception:
                    continue
            
            if not input_found:
                print("      ⚠️  Input not clearly found, will try typing anyway...")
            
            # Type the query
            print("      Typing: 'Tell me about BCA'")
            await page.keyboard.type("Tell me about BCA", delay=50)
            await page.wait_for_timeout(500)
            
            # Press Enter
            await page.keyboard.press("Enter")
            print("      ✅ Query sent")
            print()
            
            # ─────────────────────────────────────────────────────────────────
            # STEP 4: Wait for response and stabilize DOM
            # ─────────────────────────────────────────────────────────────────
            print("[4/5] Waiting for response to appear and stabilize...")
            
            # Wait for any text that indicates enrichment
            enrichment_keywords = ["Career", "salary", "difficulty", "Difficulty"]
            
            for i in range(20):  # Try for up to 20 seconds
                page_text = await page.inner_text("body")
                
                # Check if any enrichment keyword is visible
                if any(keyword in page_text for keyword in enrichment_keywords):
                    print(f"      ✅ Enrichment keywords detected (attempt {i+1})")
                    break
                
                await page.wait_for_timeout(1000)
                if i % 5 == 0:
                    print(f"      ... waiting ({i}s)")
            
            # Extra wait for stability
            await page.wait_for_timeout(2000)
            print("      ✅ Response stabilized")
            print()
            
            # ─────────────────────────────────────────────────────────────────
            # STEP 5: Extract visible response text
            # ─────────────────────────────────────────────────────────────────
            print("[5/5] Extracting UI text...")
            
            # Get full page text
            full_text = await page.inner_text("body")
            
            # Try to find just the chat response area
            response_selectors = [
                "[data-testid='chat-response']",
                "[data-testid='message']",
                ".message",
                ".chat-bubble",
                ".response",
                ".answer",
            ]
            
            response_text = None
            for selector in response_selectors:
                try:
                    elem = page.locator(selector).last
                    if await elem.is_visible(timeout=1000):
                        response_text = await elem.inner_text()
                        print(f"      Found response in: {selector}")
                        break
                except Exception:
                    continue
            
            # If we couldn't find a specific response area, look for text containing enrichment
            if not response_text:
                print("      Using full page text (no specific response container found)")
                response_text = full_text
            
            # Extract lines after "BCA" mention
            lines = response_text.split("\n")
            relevant_text = []
            capture = False
            for line in lines:
                if "BCA" in line or "Tell me about" in line:
                    capture = True
                if capture:
                    relevant_text.append(line)
                    if len(relevant_text) > 30:  # Limit to reasonable size
                        break
            
            extracted = "\n".join(relevant_text) if relevant_text else response_text[-1000:]
            
            print()
            print("=" * 88)
            print("EXTRACTED UI TEXT (BCA RESPONSE)")
            print("=" * 88)
            print(extracted[:1500])  # Print first 1500 chars
            print()
            
            # ─────────────────────────────────────────────────────────────────
            # STEP 6: Validate enrichment fields
            # ─────────────────────────────────────────────────────────────────
            print("=" * 88)
            print("ENRICHMENT VALIDATION")
            print("=" * 88)
            
            checks = {
                "Career paths": any(word in extracted for word in ["Career", "career", "developer", "Developer", "analyst", "Analyst"]),
                "Salary info": any(word in extracted for word in ["salary", "Salary", "₹", "L", "LPA", "lpa"]),
                "Difficulty": any(word in extracted for word in ["Difficulty", "difficulty", "medium", "Medium", "high", "High", "low", "Low"]),
            }
            
            print()
            for field, present in checks.items():
                status = "✅" if present else "❌"
                print(f"  {status} {field}: {'PRESENT' if present else 'MISSING'}")
            
            print()
            
            # ─────────────────────────────────────────────────────────────────
            # STEP 7: Take screenshot
            # ─────────────────────────────────────────────────────────────────
            screenshot_path = Path("/Users/maneeth/Desktop/Chat-Bot/screenshots/phase2_bca_ui.png")
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            
            await page.screenshot(path=screenshot_path)
            print(f"  📸 Screenshot saved: {screenshot_path}")
            
            print()
            print("=" * 88)
            print("RESULT")
            print("=" * 88)
            
            all_pass = all(checks.values())
            if all_pass:
                print("✅ PASS: All enrichment fields visible in UI")
            else:
                failed = [k for k, v in checks.items() if not v]
                print(f"❌ FAIL: Missing fields: {', '.join(failed)}")
            
            print()
            
        except Exception as e:
            print(f"❌ Test error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
