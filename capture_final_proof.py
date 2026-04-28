from playwright.sync_api import sync_playwright
import time

def capture_final_proof():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        print("📸 Step 1: Homepage...")
        page.goto('http://localhost:3001', wait_until='networkidle', timeout=15000)
        page.screenshot(path='/tmp/proof/01_homepage_v2.png')
        print("✅ Homepage captured")
        
        print("🤖 Step 2: Open chat...")
        page.click('.floating-robot-trigger')
        page.wait_for_timeout(1000)
        page.screenshot(path='/tmp/proof/02_chat_open.png')
        print("✅ Chat opened")
        
        print("📝 Step 3: Onboarding...")
        page.fill('input[name="name"]', 'Arun Kumar')
        page.fill('input[name="email"]', 'arun@example.com')
        page.fill('input[name="mobile"]', '9876543210')
        page.click('.radio-card:has-text("MBA")')
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)
        page.screenshot(path='/tmp/proof/03_after_onboarding.png')
        print("✅ Onboarding complete")
        
        print("💬 Step 4: Query MBA fees...")
        page.wait_for_selector('textarea', state='visible', timeout=10000)
        page.fill('textarea', 'What are the MBA fees?')
        page.click('button.send-btn')
        page.wait_for_timeout(5000)
        page.screenshot(path='/tmp/proof/04_mba_fees_query.png')
        print("✅ MBA fees response captured")
        
        print("📚 Step 5: Query courses...")
        page.wait_for_selector('textarea', state='visible', timeout=10000)
        page.fill('textarea', 'What courses are offered?')
        page.click('button.send-btn')
        page.wait_for_timeout(5000)
        page.screenshot(path='/tmp/proof/05_courses_query.png')
        print("✅ Courses response captured")
        
        print("\n=== VERIFICATION ===")
        messages = page.query_selector_all('.message-content, .message-bubble')
        print(f"Total messages: {len(messages)}")
        for i, msg in enumerate(messages):
            text = msg.inner_text()[:100]
            if text:
                print(f"  {i+1}. {text}")
        
        browser.close()
        print("\n🎉 All screenshots in /tmp/proof/")

if __name__ == '__main__':
    capture_final_proof()