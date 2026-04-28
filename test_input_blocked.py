from playwright.sync_api import sync_playwright

def test_input_blocked():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        page.goto('http://localhost:3001', wait_until='networkidle', timeout=15000)
        page.click('.floating-robot-trigger')
        page.wait_for_timeout(1000)
        
        textarea = page.wait_for_selector('textarea')
        is_disabled = textarea.is_disabled()
        placeholder = textarea.get_attribute('placeholder')
        
        print(f"Input disabled: {is_disabled}")
        print(f"Placeholder: {placeholder}")
        
        page.screenshot(path='/tmp/proof/input_blocked_before.png')
        print("✅ Input blocked state captured")
        
        if is_disabled:
            print("✅ FIXED: Input is blocked until onboarding")
        else:
            print("❌ Input still enabled")
        
        browser.close()

if __name__ == '__main__':
    test_input_blocked()