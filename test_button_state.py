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
    
    print("\n[DEBUG] Checking send button state...")
    
    # Fill chat input
    chat_input = page.query_selector("textarea")
    if chat_input:
        chat_input.fill("Fees structure")
        print("[DEBUG] Filled chat input with 'Fees structure'")
    
    # Find send button
    buttons = page.query_selector_all("button")
    for i, btn in enumerate(buttons):
        # Look for the send button (SVG with arrow)
        svg = btn.query_selector("svg")
        if svg:
            disabled = btn.get_attribute("disabled")
            classes = btn.get_attribute("class")
            print(f"[DEBUG] Button {i}: disabled={disabled}, classes={classes}")
            
            if "send-btn" in (classes or ""):
                print(f"[DEBUG] Found send button!")
                print(f"[DEBUG] Button disabled: {disabled}")
                print(f"[DEBUG] Button classes: {classes}")
                
                # Try clicking
                btn.click()
                print(f"[DEBUG] Clicked send button")
                time.sleep(3)
                break
    
    browser.close()
