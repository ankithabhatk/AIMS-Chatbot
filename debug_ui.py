from playwright.sync_api import sync_playwright

def debug_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        page.goto('http://localhost:3001', wait_until='networkidle', timeout=20000)
        
        page.click('.floating-robot-trigger')
        page.wait_for_timeout(2000)
        
        page.fill('input[name="name"]', 'Test User')
        page.fill('input[name="email"]', 'test@example.com')
        page.fill('input[name="mobile"]', '9876543210')
        page.click('.radio-card:has-text("MBA")')
        page.click('button[type="submit"]')
        page.wait_for_timeout(4000)
        
        page.screenshot(path='/tmp/proof/debug_onboard.png')
        print("Screenshot saved")
        
        all_inputs = page.query_selector_all('input, textarea, select')
        print("Inputs found:", len(all_inputs))
        for inp in all_inputs:
            cls = inp.get_attribute('class') or ''
            print("  -", inp.get_attribute('name'), cls[:50])
        
        browser.close()
        print("Done")

if __name__ == '__main__':
    debug_ui()