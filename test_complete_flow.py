from playwright.sync_api import sync_playwright

def test_complete_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        page.goto('http://localhost:3001', wait_until='networkidle', timeout=15000)
        
        page.click('.floating-robot-trigger')
        page.wait_for_selector('input[name*="name"], input[placeholder*="Name"]', timeout=5000)
        
        page.fill('input[name="name"]', 'Test User')
        page.fill('input[name="email"]', 'test@example.com')
        page.fill('input[name="mobile"]', '9876543210')
        page.click('.radio-card:has-text("MBA")')
        page.click('button[type="submit"]')
        
        page.wait_for_timeout(2000)
        page.screenshot(path='/tmp/proof/after_onboarding.png')
        print("✅ Onboarding completed")
        
        page.fill('textarea', 'What are MBA fees?')
        page.click('button.send-btn')
        page.wait_for_timeout(5000)
        page.screenshot(path='/tmp/proof/fees_response_fixed.png')
        print("✅ Fees response captured")
        
        messages = page.query_selector_all('.message-bubble:not([class*="welcome"])')
        print("\n=== Chat Responses ===")
        for msg in messages:
            text = msg.inner_text()
            if text and len(text) > 10:
                print(f"  - {text[:300]}")
        
        browser.close()

if __name__ == '__main__':
    test_complete_flow()