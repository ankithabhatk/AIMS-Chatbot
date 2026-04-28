#!/usr/bin/env python3
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    page.on("console", lambda msg: print(f"[CONSOLE] {msg.text}"))
    
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
    buttons = page.query_selector_all("div[class*='radio']")
    for btn in buttons:
        if "BCA" in btn.text_content():
            btn.click()
            time.sleep(0.5)
            break
    
    # Click Submit
    submit_buttons = page.query_selector_all("button")
    for btn in submit_buttons:
        if "Submit" in btn.text_content():
            print("[DEBUG] Clicking Submit button")
            btn.click()
            time.sleep(3)
            break
    
    # Check page content
    print("\n[PAGE CONTENT AFTER SUBMIT]:")
    content = page.content()
    
    # Look for specific markers
    if "Thank you" in content:
        print("✅ Found 'Thank you' message - form was submitted")
    if "Course Interested" in content:
        print("❌ Still showing 'Course Interested' - form NOT submitted")
    if "Fees structure" in content:
        print("✅ Found 'Fees structure' - message was sent")
    
    # Check for messages in DOM
    messages = page.query_selector_all(".message-bubble, [class*='message']")
    print(f"\n[MESSAGES FOUND]: {len(messages)}")
    for i, msg in enumerate(messages[-3:]):
        text = msg.text_content().strip()[:100]
        print(f"  Message {i}: {text}")
    
    browser.close()
