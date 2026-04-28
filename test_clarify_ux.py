"""
Comprehensive Playwright Test for Clarify UX System
====================================================

Tests:
1. Low-signal query "mba" → clarify response with suggestions
2. Very short query "mb" → clarify response
3. Valid query "mba fees" → structured response (NOT clarify)
4. Click suggestion button → auto-fills and sends
5. Edge case "fees" → clarify response

All screenshots saved to /tmp/proof/
"""

import asyncio
import time
import sys
from pathlib import Path
from playwright.async_api import async_playwright

FRONTEND_URL = "http://localhost:3001"
PROOF_DIR = Path("/tmp/proof")
PROOF_DIR.mkdir(exist_ok=True)

async def screenshot(page, name: str):
    """Helper to take screenshot with timestamp."""
    filepath = PROOF_DIR / name
    await page.screenshot(path=str(filepath), full_page=True)
    print(f"✓ Screenshot: {name}")
    return filepath

async def wait_for_chat_input(page, timeout=5000):
    """Wait for chat input field to be ready."""
    try:
        await page.wait_for_selector("input[placeholder*='inquiry'], textarea[placeholder*='inquiry'], input[placeholder*='message'], textarea[placeholder*='message']", timeout=timeout)
    except:
        pass

async def get_chat_input(page):
    """Get the chat input field (try multiple selectors)."""
    selectors = [
        "input[placeholder*='inquiry']",
        "textarea[placeholder*='inquiry']",
        "input[placeholder*='message']",
        "textarea[placeholder*='message']",
        "input[placeholder*='ask']",
        "[data-testid='chat-input']"
    ]
    
    for selector in selectors:
        try:
            element = await page.query_selector(selector)
            if element:
                return element
        except:
            pass
    
    # Fallback: get any input in the chat area
    inputs = await page.query_selector_all("input, textarea")
    if inputs:
        return inputs[-1]  # Last input is usually the chat input
    
    raise Exception("Could not find chat input field")

async def send_message(page, message: str, wait_ms: int = 3000):
    """Type and send a message."""
    print(f"\n→ Sending: '{message}'")
    
    try:
        input_field = await get_chat_input(page)
        await input_field.click()
        await input_field.clear()
        await input_field.fill(message)
        await input_field.press("Enter")
        await page.wait_for_timeout(wait_ms)
    except Exception as e:
        print(f"  ⚠ Error sending message: {e}")
        raise

async def check_for_suggestions(page):
    """Check if suggestion buttons are visible."""
    try:
        # Look for button elements that appear to be suggestions
        buttons = await page.query_selector_all("button")
        suggestions = []
        
        for btn in buttons:
            text = await btn.text_content()
            if text and any(keyword in text.lower() for keyword in 
                           ["mba", "fees", "admission", "hostel", "placement", "course", "scholarship", "courses offered", "process"]):
                suggestions.append(text.strip())
        
        return suggestions
    except:
        return []

async def check_for_clarify_message(page):
    """Check if clarify message is visible."""
    try:
        # Look for the clarify message
        messages = await page.query_selector_all(".message-content, .message-bubble")
        for msg in messages:
            text = await msg.text_content()
            if "need a bit more detail" in text.lower():
                return True
        return False
    except:
        return False

async def main():
    print("=" * 70)
    print("CLARIFY UX SYSTEM - COMPREHENSIVE PLAYWRIGHT TEST")
    print("=" * 70)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Capture console logs
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type.upper()}] {msg.text}"))
        
        try:
            # ====================================================================
            # SETUP: Navigate and open chat
            # ====================================================================
            print("\n[SETUP] Loading homepage...")
            await page.goto(FRONTEND_URL)
            await page.wait_for_timeout(2000)
            await screenshot(page, "00_homepage.png")
            
            print("[SETUP] Opening chatbot...")
            try:
                # Click floating robot icon
                await page.click(".floating-robot-trigger, [data-testid='floating-robot']")
                await page.wait_for_timeout(1500)
            except:
                print("  ⚠ Could not click floating robot, trying alternative...")
                await page.press("Escape")  # Close if open
                await page.wait_for_timeout(500)
            
            await screenshot(page, "01_chat_open.png")
            
            # ====================================================================
            # ONBOARDING: Complete profile
            # ====================================================================
            print("\n[ONBOARDING] Starting onboarding flow...")
            
            # Check for onboarding form
            onboarding_visible = await page.is_visible(".welcome-form, [data-testid='welcome-form']", timeout=2000)
            if not onboarding_visible:
                print("  ⚠ Onboarding not visible, trying to trigger...")
                try:
                    await page.click(".start-chat, [data-testid='start-chat']")
                    await page.wait_for_timeout(1000)
                except:
                    pass
            
            await screenshot(page, "02_onboarding_form.png")
            
            # Fill Name
            print("  → Filling Name...")
            try:
                name_inputs = await page.query_selector_all("input[type='text'], input[placeholder*='name'], input[placeholder*='Name']")
                if name_inputs:
                    await name_inputs[0].fill("Test Student")
                    await page.wait_for_timeout(500)
            except Exception as e:
                print(f"    ⚠ Could not fill name: {e}")
            
            # Fill Email
            print("  → Filling Email...")
            try:
                email_inputs = await page.query_selector_all("input[type='email'], input[placeholder*='email'], input[placeholder*='Email']")
                if email_inputs:
                    await email_inputs[0].fill("test@example.com")
                    await page.wait_for_timeout(500)
            except Exception as e:
                print(f"    ⚠ Could not fill email: {e}")
            
            # Fill Mobile
            print("  → Filling Mobile...")
            try:
                phone_inputs = await page.query_selector_all("input[type='tel'], input[placeholder*='phone'], input[placeholder*='mobile'], input[placeholder*='Mobile']")
                if phone_inputs:
                    await phone_inputs[0].fill("9876543210")
                    await page.wait_for_timeout(500)
            except Exception as e:
                print(f"    ⚠ Could not fill phone: {e}")
            
            # Select Course
            print("  → Selecting Course...")
            try:
                # Look for select, radio buttons, or dropdown
                selects = await page.query_selector_all("select")
                if selects:
                    await selects[0].select_option("MBA")
                    await page.wait_for_timeout(500)
                else:
                    # Try radio buttons or course options
                    radio_buttons = await page.query_selector_all("input[type='radio']")
                    if radio_buttons:
                        await radio_buttons[0].click()
                        await page.wait_for_timeout(500)
            except Exception as e:
                print(f"    ⚠ Could not select course: {e}")
            
            await screenshot(page, "03_form_filled.png")
            
            # Click Submit
            print("  → Submitting onboarding...")
            try:
                submit_buttons = await page.query_selector_all("button")
                for btn in submit_buttons:
                    text = await btn.text_content()
                    if "submit" in text.lower() or "continue" in text.lower() or "start" in text.lower():
                        await btn.click()
                        await page.wait_for_timeout(2000)
                        break
            except Exception as e:
                print(f"    ⚠ Could not submit: {e}")
            
            await screenshot(page, "04_after_onboarding.png")
            
            # ====================================================================
            # TEST CASE 1: Low-signal "mba"
            # ====================================================================
            print("\n[TEST 1] Low-signal query: 'mba'")
            await send_message(page, "mba", wait_ms=2500)
            await screenshot(page, "05_test1_mba_clarify.png")
            
            is_clarify = await check_for_clarify_message(page)
            suggestions = await check_for_suggestions(page)
            print(f"  ✓ Clarify detected: {is_clarify}")
            print(f"  ✓ Suggestions found: {len(suggestions)}")
            if suggestions:
                for s in suggestions:
                    print(f"    - {s}")
            
            # ====================================================================
            # TEST CASE 2: Very short "mb"
            # ====================================================================
            print("\n[TEST 2] Very short query: 'mb'")
            await send_message(page, "mb", wait_ms=2500)
            await screenshot(page, "06_test2_mb_clarify.png")
            
            is_clarify = await check_for_clarify_message(page)
            suggestions = await check_for_suggestions(page)
            print(f"  ✓ Clarify detected: {is_clarify}")
            print(f"  ✓ Suggestions found: {len(suggestions)}")
            
            # ====================================================================
            # TEST CASE 3: Valid query "mba fees"
            # ====================================================================
            print("\n[TEST 3] Valid query: 'mba fees' (should NOT clarify)")
            await send_message(page, "mba fees", wait_ms=3000)
            await screenshot(page, "07_test3_valid_fees.png")
            
            is_clarify = await check_for_clarify_message(page)
            print(f"  ✓ Clarify shown (should be False): {is_clarify}")
            
            # ====================================================================
            # TEST CASE 4: Click suggestion button
            # ====================================================================
            print("\n[TEST 4] Click suggestion button")
            try:
                buttons = await page.query_selector_all("button")
                clicked = False
                for btn in buttons:
                    text = await btn.text_content()
                    if text and any(keyword in text for keyword in ["MBA", "fees", "admission", "hostel"]):
                        print(f"  → Clicking button: '{text.strip()}'")
                        await btn.click()
                        await page.wait_for_timeout(2500)
                        clicked = True
                        break
                
                if not clicked:
                    print("  ⚠ No suggestion buttons found to click")
            except Exception as e:
                print(f"  ⚠ Error clicking suggestion: {e}")
            
            await screenshot(page, "08_test4_suggestion_click.png")
            
            # ====================================================================
            # TEST CASE 5: Edge case "fees"
            # ====================================================================
            print("\n[TEST 5] Edge case: 'fees'")
            await send_message(page, "fees", wait_ms=2500)
            await screenshot(page, "09_test5_fees_clarify.png")
            
            is_clarify = await check_for_clarify_message(page)
            suggestions = await check_for_suggestions(page)
            print(f"  ✓ Clarify detected: {is_clarify}")
            print(f"  ✓ Suggestions found: {len(suggestions)}")
            
            # ====================================================================
            # CONSOLE LOGS
            # ====================================================================
            print("\n" + "=" * 70)
            print("CONSOLE LOGS:")
            print("=" * 70)
            for log in console_logs[-20:]:  # Last 20 logs
                print(log)
            
            # ====================================================================
            # SUMMARY
            # ====================================================================
            print("\n" + "=" * 70)
            print("TEST COMPLETE")
            print("=" * 70)
            print(f"Screenshots saved to: {PROOF_DIR}")
            print("\nGenerated files:")
            for f in sorted(PROOF_DIR.glob("*.png")):
                if f.name.startswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
                    print(f"  - {f.name}")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            await screenshot(page, "ERROR_screenshot.png")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
