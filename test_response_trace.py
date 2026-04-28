from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Collect all console logs
    logs = []
    def handle_console(msg):
        logs.append(f'{msg.type}: {msg.text}')
    
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
        time.sleep(3)
    
    # Print all logs
    print("\n" + "="*80)
    print("RESPONSE TRACE LOGS")
    print("="*80 + "\n")
    
    for log in logs:
        if '[RESPONSE TRACE]' in log or '[STEP' in log:
            print(log)
    
    browser.close()
