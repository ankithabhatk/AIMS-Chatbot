#!/usr/bin/env python3
"""
Scenario C: Refresh case - Complete onboarding, refresh page, ask question
"""
import time
from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    page.on("console", lambda msg: print(f"[CONSOLE] {msg.text}"))
    
    screenshot_dir = "test_scenario_c"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    print("[SCENARIO C] Refresh case - Complete onboarding, refresh, ask question")
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
    
    page.screenshot(path=f"{screenshot_dir}/01_after_onboarding.png")
    print("[SCREENSHOT] 01_after_onboarding.png")
    print("[TEST] Onboarding completed")
    
    # NOW REFRESH THE PAGE
    print("\n[TEST] Refreshing page...")
    page.reload(wait_until="networkidle")
    time.sleep(2)
    
    page.screenshot(path=f"{screenshot_dir}/02_after_refresh.png")
    print("[SCREENSHOT] 02_after_refresh.png")
    
    # Check if form is shown again
    form_visible = page.query_selector("input[placeholder*='Full Name']")
    if form_visible:
        print("[RESULT] ❌ Form shown again after refresh - profile not persisted")
    else:
        print("[RESULT] ✅ Form hidden after refresh - profile persisted")
    
    # Try to send message
    print("\n[TEST] Trying to send 'Fees structure' after refresh...")
    
    inputs = page.query_selector_all("textarea")
    if inputs:
        chat_input = inputs[-1]
        chat_input.fill("Fees structure")
        
        buttons = page.query_selector_all("button")
        for btn in buttons:
            classes = btn.get_attribute("class") or ""
            if "send-btn" in classes:
                btn.click()
                time.sleep(3)
                break
    
    page.screenshot(path=f"{screenshot_dir}/03_after_fees_query.png")
    print("[SCREENSHOT] 03_after_fees_query.png")
    
    # Extract response
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
            print("\n✅ SCENARIO C PASSED - Course remembered after refresh")
        else:
            print("\n❌ SCENARIO C FAILED - Course not remembered after refresh")
    
    browser.close()
