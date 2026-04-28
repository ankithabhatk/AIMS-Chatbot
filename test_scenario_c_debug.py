#!/usr/bin/env python3
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    page.on("console", lambda msg: print(f"[CONSOLE] {msg.text}"))
    
    print("[SCENARIO C] Refresh case")
    print("="*60)
    
    page.goto("http://localhost:3000", wait_until="networkidle")
    time.sleep(2)
    
    # Click robot
    robot = page.query_selector(".floating-robot-trigger")
    if robot:
        robot.click()
        time.sleep(2)
    
    # Fill and submit form
    inputs = page.query_selector_all("input[type='text'], input[type='email'], input[type='tel']")
    if len(inputs) >= 3:
        inputs[0].fill("Test User")
        inputs[1].fill("test@example.com")
        inputs[2].fill("9876543210")
    
    radio_cards = page.query_selector_all("div[class*='radio-card']")
    for card in radio_cards:
        if "BCA" in card.text_content():
            card.click()
            break
    
    buttons = page.query_selector_all("button")
    for btn in buttons:
        if "Submit" in btn.text_content():
            btn.click()
            time.sleep(3)
            break
    
    print("[TEST] Onboarding completed, now refreshing...")
    
    # REFRESH
    page.reload(wait_until="networkidle")
    time.sleep(3)
    
    print("[TEST] Page refreshed")
    
    # Check if chat is open
    chat_window = page.query_selector(".chat-main")
    if chat_window:
        print("[RESULT] ✅ Chat window visible after refresh")
    else:
        print("[RESULT] ❌ Chat window NOT visible after refresh")
    
    # Check if form is shown
    form = page.query_selector("input[placeholder*='Full Name']")
    if form:
        print("[RESULT] ❌ Form shown after refresh")
    else:
        print("[RESULT] ✅ Form hidden after refresh")
    
    # Try to send message
    print("\n[TEST] Sending 'Fees structure'...")
    
    inputs = page.query_selector_all("textarea")
    if inputs:
        chat_input = inputs[-1]
        chat_input.fill("Fees structure")
        print("[DEBUG] Filled chat input")
        
        buttons = page.query_selector_all("button")
        for btn in buttons:
            classes = btn.get_attribute("class") or ""
            if "send-btn" in classes:
                btn.click()
                print("[DEBUG] Clicked send button")
                time.sleep(4)
                break
    
    # Check response
    print("\n[RESULT] Checking response...")
    messages = page.query_selector_all(".message-bubble")
    print(f"[DEBUG] Found {len(messages)} message bubbles")
    
    if messages:
        for i, msg in enumerate(messages[-3:]):
            text = msg.text_content().strip()[:150]
            print(f"  Message {i}: {text}")
    
    browser.close()
