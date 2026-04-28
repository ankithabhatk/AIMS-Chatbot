#!/usr/bin/env python3
import time
from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    screenshot_dir = "test_final_screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    page.goto("http://localhost:3000", wait_until="networkidle")
    time.sleep(2)
    
    # Click robot
    robot = page.query_selector(".floating-robot-trigger")
    if robot:
        robot.click()
        time.sleep(2)
    
    page.screenshot(path=f"{screenshot_dir}/01_chat_opened.png")
    
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
    
    page.screenshot(path=f"{screenshot_dir}/02_after_onboarding.png")
    
    # Send fees query
    chat_input = page.query_selector("textarea")
    if chat_input:
        chat_input.fill("Fees structure")
    
    buttons = page.query_selector_all("button")
    for btn in buttons:
        classes = btn.get_attribute("class") or ""
        if "send-btn" in classes:
            btn.click()
            time.sleep(3)
            break
    
    page.screenshot(path=f"{screenshot_dir}/03_fees_response.png")
    
    # Extract bot response
    messages = page.query_selector_all(".message-bubble")
    if messages:
        last_msg = messages[-1]
        response_text = last_msg.text_content().strip()
        
        print("\n" + "="*60)
        print("UI RESULT:")
        print("="*60)
        print(f"\nBot Response:\n{response_text}\n")
        
        # Analyze
        has_bca = "BCA" in response_text
        has_multiple_courses = sum(1 for course in ['MBA', 'MCA', 'BBA', 'B.Com', 'M.Com', 'BHM'] if course in response_text) > 1
        has_annual_fee = "Annual fee" in response_text or "₹" in response_text
        has_fallback = "Try asking about" in response_text
        
        print("Analysis:")
        print(f"  ✅ Only BCA fees? {'YES' if has_bca and not has_multiple_courses else 'NO'}")
        print(f"  ✅ Multiple courses shown? {'YES' if has_multiple_courses else 'NO'}")
        print(f"  ✅ Has fee information? {'YES' if has_annual_fee else 'NO'}")
        print(f"  ✅ Fallback message? {'YES' if has_fallback else 'NO'}")
        
        if has_bca and not has_multiple_courses and has_annual_fee and not has_fallback:
            print("\n🎉 UI TEST PASSED - System working correctly!")
        else:
            print("\n❌ UI TEST FAILED")
        
        # Save response
        with open(f"{screenshot_dir}/response.txt", "w") as f:
            f.write(response_text)
        
        print(f"\nScreenshots saved to {screenshot_dir}/")
    
    browser.close()
