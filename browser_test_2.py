from playwright.sync_api import sync_playwright
import time

URL = "http://localhost:3000"

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("\n🚀 Opening chatbot (Test 2)...")
        page.goto(URL)
        time.sleep(3)
        
        print("🤖 Clicking robot trigger...")
        page.locator(".floating-robot-trigger").click()
        time.sleep(2)
        
        def send_query(query, step):
            print(f"\n🧪 Step {step}: {query}")
            
            # Find and fill input
            input_selectors = [
                "input[type='text']",
                "textarea",
                "[role='textbox']",
                "input",
            ]
            
            input_found = False
            for selector in input_selectors:
                try:
                    inputs = page.locator(selector)
                    if inputs.count() > 0:
                        print(f"   ✓ Found input, filling query...")
                        inputs.first.fill(query)
                        inputs.first.press("Enter")
                        time.sleep(2)
                        input_found = True
                        break
                except:
                    pass
            
            if not input_found:
                print(f"   ❌ Could not find input selector")
                return
            
            # Screenshot
            page.screenshot(path=f"test2_step{step}.png")
            print(f"   📸 Screenshot saved: test2_step{step}.png")
            
            # Check if form is visible
            form_indicators = [
                "input[placeholder*='Full Name']",
                "input[placeholder*='full name']",
                "input[placeholder*='name']",
                "[data-testid='name-field']",
                "div[class*='form']",
                "input[type='text'][placeholder]",
            ]
            
            form_visible = False
            for form_selector in form_indicators:
                try:
                    forms = page.locator(form_selector)
                    if forms.count() > 0:
                        form_visible = True
                        print(f"   🔒 Form elements VISIBLE")
                        break
                except:
                    pass
            
            if not form_visible:
                print(f"   ✅ No form visible - chat mode active")
            
            # Try to extract response
            try:
                messages = page.locator(".message, [class*='message'], div[class*='bot']")
                if messages.count() > 0:
                    last = messages.last.inner_text()
                    if last:
                        print(f"   📝 Response: {last[:150]}")
            except:
                pass
        
        # TEST 2 FLOW
        send_query("Tell me about BCA", 1)
        send_query("fees?", 2)
        send_query("how to apply?", 3)
        
        browser.close()

if __name__ == "__main__":
    run_test()
