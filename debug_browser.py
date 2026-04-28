from playwright.sync_api import sync_playwright

def test_browser_api():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        page.on("console", lambda msg: print(f"[BROWSER {msg.type.upper()}] {msg.text}"))
        page.on("request", lambda req: print(f"[REQUEST] {req.method} {req.url}"))
        page.on("response", lambda res: print(f"[RESPONSE] {res.status} {res.url}"))
        page.on("requestfailed", lambda req: print(f"[FAILED] {req.url} - {req.failure}"))
        
        page.goto('http://localhost:3001', wait_until='networkidle', timeout=15000)
        page.click('.floating-robot-trigger')
        page.wait_for_selector('textarea', timeout=5000)
        page.fill('textarea', 'What are MBA fees?')
        page.click('button.send-btn')
        page.wait_for_timeout(5000)
        
        browser.close()

if __name__ == '__main__':
    test_browser_api()