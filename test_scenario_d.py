#!/usr/bin/env python3
"""
Scenario D: No course selected at all
Expected: Guard should prevent sending, show guidance message
"""
import time
from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    page.on("console", lambda msg: print(f"[CONSOLE] {msg.text}"))
    
    screenshot_dir = "test_scenario_d"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    print("[SCENARIO D] No course selected - guard test")
    print("="*60)
    
    page.goto("http://localhost:3000", wait_until="networkidle")
    time.sleep(2)
    
    # Click robot
    robot = page.query_selector(".floating-robot-trigger")
    if robot:
        robot.click()
        time.sleep(2)
    
    # DO NOT select course, DO NOT submit form
    print("[TEST] Skipping course selection entirely...")
    
    # Try to type directly in chat input
    inputs = page.query_selector_all("textarea")
    if inputs:
        chat_input = inputs[-1]
        chat_input.fill("Fees structure")
        print("[TEST] Typed 'Fees structure' without selecting course")
        
        buttons = page.query_selector_all("button")
        for btn in buttons:
            classes = btn.get_attribute("class") or ""
            if "send-btn" in classes:
                btn.click()
                print("[TEST] Clicked send button")
                time.sleep(3)
                break
    
    page.screenshot(path=f"{screenshot_dir}/01_after_send_attempt.png")
    print("[SCREENSHOT] 01_after_send_attempt.png")
    
    # Check what's shown
    print("\n[RESULT] Checking response...")
    messages = page.query_selector_all(".message-bubble")
    print(f"[DEBUG] Found {len(messages)} message bubbles")
    
    if messages:
        for i, msg in enumerate(messages[-3:]):
            text = msg.text_content().strip()[:150]
            print(f"  Message {i}: {text}")
        
        # Check if guidance message is shown
        last_msg = messages[-1]
        response_text = last_msg.text_content().strip()
        
        if "select your course" in response_text.lower():
            print("\n✅ SCENARIO D PASSED - Guard working, guidance message shown")
        elif "fees" in response_text.lower():
            print("\n❌ SCENARIO D FAILED - Backend was called (guard not working)")
        else:
            print(f"\n⚠️ SCENARIO D UNCLEAR - Got: {response_text[:100]}")
    
    browser.close()
