from playwright.sync_api import sync_playwright
import time

URL = "http://localhost:3000"

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("\n🚀 Opening chatbot...")
        page.goto(URL)
        time.sleep(3)
        
        print("🤖 Clicking robot trigger...")
        # Click the floating robot trigger
        page.locator(".floating-robot-trigger").click()
        time.sleep(2)
        
        def send_query(query, step):
            print(f"\n🧪 Step {step}: {query}")
            
            # Try different input selectors
            input_selectors = [
                "input[type='text']",
                "textarea",
                "[role='textbox']",
                "input",
                ".message-input input",
                ".chat-input input",
                "[placeholder*='Type']",
                "[placeholder*='type']",
                "[placeholder*='message']",
                "[placeholder*='Message']",
            ]
            
            input_found = False
            for selector in input_selectors:
                try:
                    inputs = page.locator(selector)
                    if inputs.count() > 0:
                        print(f"   Found input with selector: {selector}")
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
            page.screenshot(path=f"step{step}.png")
            print(f"   📸 Screenshot saved: step{step}.png")
            
            # Try to extract bot response
            try:
                # Look for message containers
                message_selectors = [
                    ".message",
                    "[data-testid='message']",
                    ".chat-message",
                    ".bot-message",
                    "div[class*='message']",
                ]
                
                for msg_selector in message_selectors:
                    messages = page.locator(msg_selector)
                    if messages.count() > 0:
                        last = messages.last.inner_text()
                        print(f"   🤖 Bot response: {last[:200]}")
                        break
            except:
                print("   (Could not extract response)")
        
        # FLOW
        send_query("I like coding", 1)
        send_query("Tell me about BCA", 2)
        send_query("What about MCA?", 3)
        
        browser.close()

if __name__ == "__main__":
    run_test()
