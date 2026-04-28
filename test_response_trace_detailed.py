from playwright.sync_api import sync_playwright
import time
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Collect all console logs
    logs = []
    def handle_console(msg):
        log_text = msg.text
        logs.append({
            'type': msg.type,
            'text': log_text
        })
    
    page.on('console', handle_console)
    
    # Navigate
    page.goto('http://localhost:3000')
    time.sleep(2)
    
    # Click robot
    robot = page.query_selector('.floating-robot-trigger')
    if robot:
        robot.click()
        time.sleep(1)
    
    # Type message
    input_field = page.query_selector('textarea')
    if input_field:
        input_field.fill('Fees structure')
        time.sleep(0.5)
    
    # Click send
    send_btn = page.query_selector('button.send-btn')
    if send_btn:
        send_btn.click()
        time.sleep(4)
    
    # Print all logs
    print("\n" + "="*80)
    print("FULL CONSOLE OUTPUT")
    print("="*80 + "\n")
    
    for log in logs:
        print(f"[{log['type'].upper()}] {log['text'][:200]}")
    
    print("\n" + "="*80)
    print("RESPONSE TRACE ANALYSIS")
    print("="*80 + "\n")
    
    # Find response trace logs
    for log in logs:
        if 'RESPONSE TRACE' in log['text']:
            print(f"✅ {log['text'][:300]}")
    
    browser.close()
