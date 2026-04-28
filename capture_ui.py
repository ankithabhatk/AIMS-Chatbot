from playwright.sync_api import sync_playwright
import time

def capture_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        print("📸 Capturing homepage...")
        page.goto('http://localhost:3001', wait_until='networkidle', timeout=15000)
        page.screenshot(path='/tmp/proof/homepage.png', full_page=True)
        print("✅ Homepage captured")
        
        print("🤖 Opening chat...")
        page.click('.floating-robot-trigger')
        time.sleep(1)
        page.screenshot(path='/tmp/proof/chat_open.png', full_page=True)
        print("✅ Chat open captured")
        
        print("💬 Testing query...")
        page.fill('textarea[placeholder*="inquiry"], textarea[placeholder*="Type"]', 'What are the MBA fees?')
        time.sleep(0.5)
        page.click('button.send-btn')
        time.sleep(3)
        page.screenshot(path='/tmp/proof/fees_query.png', full_page=True)
        print("✅ Fees query captured")
        
        browser.close()
        print("🎉 All screenshots captured in /tmp/proof/")

if __name__ == '__main__':
    capture_screenshots()