#!/usr/bin/env python3
"""
Scenario B (AFTER FIXES): Skip form, try typing message
Expected: Should still get BCA fees (from localStorage)
"""
import time
from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    page.on("console", lambda msg: print(f"[CONSOLE] {msg.text}"))
    
    screenshot_dir = "test_scenario_b_fixed"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    print("[SCENARIO B - FIXED] Skip form, try typing message")
    print("="*60)
    
    page.goto("http://localhost:3000", wait_until="networkidle")
    time.sleep(2)
    
    # Click robot
    robot = page.query_selector(".floating-robot-trigger")
    if robot:
        robot.click()
        time.sleep(2)
    
    # SELECT BCA (this saves to localStorage now)
    print("[TEST] Selecting BCA course...")
    radio_cards = page.query_selector_all("div[class*='radio-card']")
    for card in radio_cards:
        if "BCA" in card.text_content():
            card.click()
            print("[TEST] BCA selected (saved to localStorage)")
            time.sleep(0.5)
            break
    
    # SKIP FORM SUBMISSION - just try to type
    print("\n[TEST] Skipping form submission, typing directly...")
    
    inputs = page.query_selector_all("textarea")
    if inputs:
        chat_input = inputs[-1]
        chat_input.fill("Fees structure")
        print("[TEST] Typed 'Fees structure'")
        
        buttons = page.query_selector_all("button")
        for btn in buttons:
            classes = btn.get_attribute("class") or ""
            if "send-btn" in classes:
                btn.click()
                print("[TEST] Clicked send")
                time.sleep(3)
                break
    
    page.screenshot(path=f"{screenshot_dir}/01_after_send.png")
    print("[SCREENSHOT] 01_after_send.png")
    
    # Check response
    print("\n[RESULT] Checking response...")
    messages = page.query_selector_all(".message-bubble")
    
    if messages:
        last_msg = messages[-1]
        response_text = last_msg.text_content().strip()
        
        print(f"\nBot Response:\n{response_text[:200]}\n")
        
        # Analyze
        has_bca = "BCA" in response_text
        has_multiple_courses = sum(1 for course in ['MBA', 'MCA', 'BBA', 'B.Com', 'M.Com', 'BHM'] if course in response_text) > 1
        
        print("Analysis:")
        print(f"  - Only BCA fees? {'YES' if has_bca and not has_multiple_courses else 'NO'}")
        print(f"  - Multiple courses? {'YES' if has_multiple_courses else 'NO'}")
        
        if has_bca and not has_multiple_courses:
            print("\n✅ SCENARIO B FIXED - Course context preserved even without form submit")
        else:
            print("\n❌ SCENARIO B STILL BROKEN")
    
    browser.close()
