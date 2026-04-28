from playwright.sync_api import sync_playwright
import time

def quick_test():
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
        page.wait_for_timeout(3000)
        
        page.screenshot(path='/tmp/proof/06_after_onboard.png')
        print("Onboarding done")
        
        page.wait_for_timeout(1000)
        
        textarea = page.query_selector('textarea')
        if textarea and not textarea.is_disabled():
            page.fill('textarea', 'What courses are offered?')
            page.click('button.send-btn')
            page.wait_for_timeout(5000)
            page.screenshot(path='/tmp/proof/07_courses_markdown.png')
            print("Courses query done")
        else:
            print(f"Textarea issue: {textarea}")
        
        browser.close()

if __name__ == '__main__':
    quick_test()