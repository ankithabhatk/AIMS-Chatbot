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
    print(f"[DEBUG] Found {len(inputs)} inputs")
    
    if len(inputs) >= 3:
        inputs[0].fill("Test User")
        print(f"[DEBUG] Name value: {inputs[0].input_value()}")
        
        inputs[1].fill("test@example.com")
        print(f"[DEBUG] Email value: {inputs[1].input_value()}")
        
        inputs[2].fill("9876543210")
        print(f"[DEBUG] Phone value: {inputs[2].input_value()}")
    
    # Select BCA - look for the actual radio card div
    print("\n[DEBUG] Looking for BCA radio card...")
    radio_cards = page.query_selector_all("div[class*='radio-card']")
    print(f"[DEBUG] Found {len(radio_cards)} radio cards")
    
    for card in radio_cards:
        text = card.text_content().strip()
        print(f"  Card: {text}")
        if "BCA" in text:
            print(f"[DEBUG] Clicking BCA card")
            card.click()
            time.sleep(0.5)
            # Check if it's selected
            classes = card.get_attribute("class")
            print(f"[DEBUG] BCA card classes after click: {classes}")
            break
    
    # Find Submit button
    print("\n[DEBUG] Looking for Submit button...")
    buttons = page.query_selector_all("button")
    print(f"[DEBUG] Found {len(buttons)} buttons")
    
    for i, btn in enumerate(buttons):
        text = btn.text_content().strip()
        if text:
            print(f"  Button {i}: {text}")
        if "Submit" in text:
            print(f"[DEBUG] Found Submit button at index {i}")
            # Check if button is enabled
            disabled = btn.get_attribute("disabled")
            print(f"[DEBUG] Submit button disabled: {disabled}")
            
            # Try to click it
            print(f"[DEBUG] Clicking Submit button...")
            btn.click()
            time.sleep(3)
            
            # Check console for any errors
            break
    
    browser.close()
