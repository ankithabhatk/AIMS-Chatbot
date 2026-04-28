from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Collect ALL console logs
    logs = []
    def handle_console(msg):
        logs.append(msg.text)
    
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
        time.sleep(5)
    
    # Print ALL logs
    print("\n" + "="*80)
    print("ALL CONSOLE LOGS (unfiltered)")
    print("="*80 + "\n")
    
    for i, log in enumerate(logs):
        print(f"{i}: {log[:300]}")
    
    browser.close()
