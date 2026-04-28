#!/usr/bin/env python3
import time
from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    page.on("console", lambda msg: print(f"[CONSOLE] {msg.text}"))
    
    screenshot_dir = "test_screenshots_full"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    print("[TEST] Opening app...")
    page.goto("http://localhost:3000", wait_until="networkidle")
    time.sleep(2)
    
    # Click robot
    robot = page.query_selector(".floating-robot-trigger")
    if robot:
        robot.click()
        time.sleep(2)
    
    # Fill form
    inputs = page.query_selector_all("input[type='text'], input[type='email'], input[type='tel']")
    if len(inputs) >= 3:
        inputs[0].fill("Test User")
        inputs[1].fill("test@example.com")
        inputs[2].fill("9876543210")
    
    # Select BCA
    radio_cards = page.query_selector_all("div[class*='radio-card']")
    for card in radio_cards:
        if "BCA" in card.text_content():
            card.click()
            time.sleep(0.5)
            break
    
    # Click Submit
    buttons = page.query_selector_all("button")
    for btn in buttons:
        if "Submit" in btn.text_content():
            btn.click()
            time.sleep(3)
            break
    
    page.screenshot(path=f"{screenshot_dir}/01_after_onboarding.png")
    print("[SCREENSHOT] 01_after_onboarding.png")
    
    # Now ask for fees
    print("\n[TEST] Asking for fees...")
    inputs = page.query_selector_all("input[type='text'], textarea")
    if inputs:
        chat_input = inputs[-1]
        chat_input.fill("Fees structure")
        time.sleep(0.5)
    
    # Click send
    buttons = page.query_selector_all("button")
    for btn in buttons:
        text = btn.text_content().strip()
        if "Send" in text or "→" in text:
            btn.click()
            print("[TEST] Clicked send")
            time.sleep(3)
            break
    
    page.screenshot(path=f"{screenshot_dir}/02_after_fees_query.png")
    print("[SCREENSHOT] 02_after_fees_query.png")
    
    # Extract the bot response
    print("\n[EXTRACTING BOT RESPONSE]...")
    messages = page.query_selector_all(".message-bubble")
    
    if messages:
        # Get the last message (should be bot response)
        last_msg = messages[-1]
        text = last_msg.text_content().strip()
        print(f"\n[BOT RESPONSE]:\n{text}\n")
        
        # Analyze
        print("[ANALYSIS]:")
        has_bca = "BCA" in text
        has_multiple_courses = sum(1 for course in ['MBA', 'MCA', 'BBA', 'B.Com', 'M.Com', 'BHM'] if course in text) > 1
        has_annual_fee = "Annual fee" in text or "₹" in text
        
        print(f"- Has BCA? {'YES' if has_bca else 'NO'}")
        print(f"- Multiple courses? {'YES' if has_multiple_courses else 'NO'}")
        print(f"- Has fee info? {'YES' if has_annual_fee else 'NO'}")
        
        if has_bca and not has_multiple_courses and has_annual_fee:
            print("\n✅ UI TEST PASSED - Shows only BCA fees!")
        else:
            print("\n❌ UI TEST FAILED")
        
        # Save
        with open(f"{screenshot_dir}/response.txt", "w") as f:
            f.write(text)
    
    browser.close()
