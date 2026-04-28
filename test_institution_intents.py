#!/usr/bin/env python3
"""
Test new institution-level intents
"""
import time
from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    page.on("console", lambda msg: print(f"[CONSOLE] {msg.text}"))
    
    screenshot_dir = "test_institution_intents"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    print("[TEST] Institution-level intents")
    print("="*60)
    
    page.goto("http://localhost:3000", wait_until="networkidle")
    time.sleep(2)
    
    # Click robot
    robot = page.query_selector(".floating-robot-trigger")
    if robot:
        robot.click()
        time.sleep(2)
    
    # Select BCA to have context
    radio_cards = page.query_selector_all("div[class*='radio-card']")
    for card in radio_cards:
        if "BCA" in card.text_content():
            card.click()
            break
    
    # Test 1: "What is AIMS?"
    print("\n[TEST 1] Query: 'What is AIMS?'")
    inputs = page.query_selector_all("textarea")
    if inputs:
        chat_input = inputs[-1]
        chat_input.fill("What is AIMS?")
        
        buttons = page.query_selector_all("button")
        for btn in buttons:
            classes = btn.get_attribute("class") or ""
            if "send-btn" in classes:
                btn.click()
                time.sleep(3)
                break
    
    messages = page.query_selector_all(".message-bubble")
    if messages:
        last_msg = messages[-1]
        response = last_msg.text_content().strip()[:200]
        print(f"Response: {response}")
        if "premier educational institution" in response.lower() or "aims institutes" in response.lower():
            print("✅ TEST 1 PASSED")
        else:
            print("❌ TEST 1 FAILED")
    
    # Test 2: "Why choose AIMS?"
    print("\n[TEST 2] Query: 'Why choose AIMS?'")
    inputs = page.query_selector_all("textarea")
    if inputs:
        chat_input = inputs[-1]
        chat_input.fill("Why choose AIMS?")
        
        buttons = page.query_selector_all("button")
        for btn in buttons:
            classes = btn.get_attribute("class") or ""
            if "send-btn" in classes:
                btn.click()
                time.sleep(3)
                break
    
    messages = page.query_selector_all(".message-bubble")
    if messages:
        last_msg = messages[-1]
        response = last_msg.text_content().strip()[:200]
        print(f"Response: {response}")
        if "industry" in response.lower() or "placement" in response.lower():
            print("✅ TEST 2 PASSED")
        else:
            print("❌ TEST 2 FAILED")
    
    # Test 3: "What facilities does AIMS have?"
    print("\n[TEST 3] Query: 'What facilities does AIMS have?'")
    inputs = page.query_selector_all("textarea")
    if inputs:
        chat_input = inputs[-1]
        chat_input.fill("What facilities does AIMS have?")
        
        buttons = page.query_selector_all("button")
        for btn in buttons:
            classes = btn.get_attribute("class") or ""
            if "send-btn" in classes:
                btn.click()
                time.sleep(3)
                break
    
    messages = page.query_selector_all(".message-bubble")
    if messages:
        last_msg = messages[-1]
        response = last_msg.text_content().strip()[:200]
        print(f"Response: {response}")
        if "smart classroom" in response.lower() or "wi-fi" in response.lower() or "facilities" in response.lower():
            print("✅ TEST 3 PASSED")
        else:
            print("❌ TEST 3 FAILED")
    
    page.screenshot(path=f"{screenshot_dir}/final.png")
    print("\n[COMPLETE] Institution intents tested")
    
    browser.close()
