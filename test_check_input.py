#!/usr/bin/env python3
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
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
    
    # Check for chat input
    print("[DEBUG] Looking for chat input after onboarding...")
    inputs = page.query_selector_all("input[type='text'], textarea, [contenteditable]")
    print(f"[DEBUG] Found {len(inputs)} input elements")
    
    for i, inp in enumerate(inputs):
        tag = inp.evaluate("el => el.tagName")
        placeholder = inp.get_attribute("placeholder")
        value = inp.input_value() if tag == "INPUT" else ""
        print(f"  Input {i}: tag={tag}, placeholder={placeholder}, value={value}")
    
    # Try to find the chat input specifically
    chat_input = page.query_selector("input[placeholder*='Type'], input[placeholder*='message'], textarea")
    if chat_input:
        print(f"\n[DEBUG] Found chat input: {chat_input.get_attribute('placeholder')}")
        chat_input.fill("Fees structure")
        print(f"[DEBUG] Filled with 'Fees structure'")
        print(f"[DEBUG] Input value: {chat_input.input_value()}")
    else:
        print("[DEBUG] Chat input not found!")
    
    browser.close()
