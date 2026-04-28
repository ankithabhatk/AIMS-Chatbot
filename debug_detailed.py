from playwright.sync_api import sync_playwright
import json

def debug_full_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type.upper()}] {msg.text}"))
        
        page.goto('http://localhost:3001', wait_until='networkidle', timeout=15000)
        
        page.click('.floating-robot-trigger')
        page.wait_for_selector('textarea', timeout=5000)
        
        page.fill('textarea', 'MBA fees')
        page.click('button.send-btn')
        
        page.wait_for_timeout(5000)
        
        messages = page.query_selector_all('.message-bubble, [class*="message"]')
        print("=== Messages in Chat ===")
        for msg in messages:
            text = msg.inner_text()
            if text:
                print(f"  - {text[:200]}")
        
        print("\n=== Browser Console ===")
        for log in console_logs:
            print(log)
        
        print("\n=== Chat Window HTML ===")
        html = page.inner_html('.chat-main', timeout=3000)
        if '<error' in html.lower() or 'error' in html.lower():
            print("⚠️ Error detected in chat HTML")
        
        browser.close()

if __name__ == '__main__':
    debug_full_flow()