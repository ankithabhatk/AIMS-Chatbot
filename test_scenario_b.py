#!/usr/bin/env python3
"""
Scenario B: Edge case - DO NOT submit form properly, try typing message
"""
import time
from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    page.on("console", lambda msg: print(f"[CONSOLE] {msg.text}"))
    
    screenshot_dir = "test_scenario_b"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    print("[SCENARIO B] Edge case - Skip form submission")
    print("="*60)
    
    page.goto("http://localhost:3000", wait_until="networkidle")
    time.sleep(2)
    
    # Click robot
    robot = page.query_selector(".floating-robot-trigger")
    if robot:
        robot.click()
        time.sleep(2)
    
    page.screenshot(path=f"{screenshot_dir}/01_chat_opened.png")
    print("[SCREENSHOT] 01_chat_opened.png")
    
    # SKIP FORM SUBMISSION - just try to type in chat
    print("\n[TEST] Attempting to type without submitting form...")
    
    # Try to find chat input
    inputs = page.query_selector_all("input[type='text'], textarea")
    print(f"[DEBUG] Found {len(inputs)} input elements")
    
    for i, inp in enumerate(inputs):
        tag = inp.evaluate("el => el.tagName")
        placeholder = inp.get_attribute("placeholder")
        print(f"  Input {i}: tag={tag}, placeholder={placeholder}")
    
    # Try to fill the last input (should be chat input if form is not blocking)
    if inputs:
        chat_input = inputs[-1]
        print(f"\n[TEST] Trying to fill last input...")
        try:
            chat_input.fill("Fees structure")
            print(f"[TEST] Successfully filled input")
            
            # Try to send
            buttons = page.query_selector_all("button")
            for btn in buttons:
                classes = btn.get_attribute("class") or ""
                if "send-btn" in classes:
                    print(f"[TEST] Found send button, clicking...")
                    btn.click()
                    time.sleep(3)
                    break
            
            page.screenshot(path=f"{screenshot_dir}/02_after_send_attempt.png")
            print("[SCREENSHOT] 02_after_send_attempt.png")
            
        except Exception as e:
            print(f"[ERROR] Could not fill input: {e}")
    
    # Check what's displayed
    print("\n[RESULT] Checking what's shown...")
    messages = page.query_selector_all(".message-bubble")
    print(f"[DEBUG] Found {len(messages)} message bubbles")
    
    if messages:
        for i, msg in enumerate(messages[-3:]):
            text = msg.text_content().strip()[:100]
            print(f"  Message {i}: {text}")
    
    # Check if form is still visible
    form_visible = page.query_selector("input[placeholder*='Full Name']")
    if form_visible:
        print("\n[RESULT] ❌ Form still visible - user cannot send message without submitting")
    else:
        print("\n[RESULT] ✅ Form hidden - user can send message")
    
    browser.close()
