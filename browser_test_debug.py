from playwright.sync_api import sync_playwright
import time

URL = "http://localhost:3000"

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("\n🚀 Opening chatbot...")
        try:
            page.goto(URL, timeout=10000)
            print("✅ Page loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load page: {e}")
            browser.close()
            return
        
        time.sleep(3)
        
        # Debug: print page content and available selectors
        print("\n🔍 Page content (first 500 chars):")
        content = page.content()
        print(content[:500])
        
        print("\n🔍 Looking for input elements...")
        inputs = page.locator("input")
        count = inputs.count()
        print(f"Found {count} input elements")
        
        if count > 0:
            print(f"Input selector works!")
        else:
            print("No input elements found. Looking for alternatives...")
            # Try to find textarea
            textareas = page.locator("textarea")
            print(f"Found {textareas.count()} textareas")
            
            # Try to find any input-like elements
            all_inputs = page.locator("[role='textbox']")
            print(f"Found {all_inputs.count()} elements with role='textbox'")
        
        browser.close()

if __name__ == "__main__":
    run_test()
