from playwright.sync_api import sync_playwright
import time

URL = "http://localhost:3000"

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("\n🚀 Opening chatbot...")
        page.goto(URL)
        
        # Wait longer for React to render
        print("⏳ Waiting for React components to render...")
        time.sleep(5)
        
        print("✅ Page loaded")
        
        # Look for any message-like elements
        print("\n🔍 Looking for chat elements...")
        
        # Try different selectors commonly used in chat apps
        selectors_to_try = [
            ("input", "input"),
            ("textarea", "textarea"),
            ("[role='textbox']", "[role='textbox']"),
            ("[placeholder]", "[placeholder]"),
            ("div[contenteditable]", "contenteditable div"),
            (".input", ".input class"),
            (".message-input", ".message-input class"),
            (".chat-input", ".chat-input class"),
            ("*[data-testid='input']", "[data-testid='input']"),
        ]
        
        for selector, desc in selectors_to_try:
            try:
                count = page.locator(selector).count()
                if count > 0:
                    print(f"✅ Found {count} {desc} elements")
            except:
                pass
        
        # Print the actual HTML to see what's there
        print("\n📄 Full page HTML (showing structure):")
        content = page.content()
        
        # Find and print main body structure
        if "<body" in content:
            body_start = content.find("<body")
            body_section = content[body_start:body_start+2000]
            print(body_section)
        
        browser.close()

if __name__ == "__main__":
    run_test()
