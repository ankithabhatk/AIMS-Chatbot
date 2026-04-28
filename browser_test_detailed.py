from playwright.sync_api import sync_playwright
import time
import json

URL = "http://localhost:3000"

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Enable network logging
        all_responses = []
        
        def handle_response(response):
            if "chat" in response.url and response.status == 200:
                all_responses.append({
                    "url": response.url,
                    "status": response.status,
                })
        
        page.on("response", handle_response)
        
        print("\n🚀 Opening chatbot...")
        page.goto(URL)
        time.sleep(3)
        
        print("🤖 Clicking robot trigger...")
        page.locator(".floating-robot-trigger").click()
        time.sleep(2)
        
        print("\n📝 FILLING FORM...")
        page.fill("input[name='name']", "Test User")
        time.sleep(0.3)
        page.fill("input[name='email']", "test@example.com")
        time.sleep(0.3)
        page.fill("input[name='mobile']", "9876543210")
        time.sleep(0.3)
        
        # Select BCA
        all_cards = page.locator(".radio-card")
        for i in range(all_cards.count()):
            text = all_cards.nth(i).inner_text()
            if "BCA" in text:
                all_cards.nth(i).click()
                break
        time.sleep(0.5)
        
        print("   Clicking Submit...")
        page.click("button[type='submit']")
        time.sleep(3)
        
        print("\n✅ Form submitted! Now testing queries...\n")
        
        def send_and_report(query, step):
            print(f"\n{'='*60}")
            print(f"STEP {step}: {query}")
            print(f"{'='*60}")
            
            chat_input = page.locator("textarea").first
            chat_input.fill(query)
            chat_input.press("Enter")
            
            # Wait for response
            time.sleep(3)
            
            # Capture response
            page.screenshot(path=f"detailed_step{step}.png")
            
            # Try to find bot response
            try:
                # Look for message elements - they should have timestamps
                all_messages = page.locator(".message")
                if all_messages.count() > 0:
                    last_msg = all_messages.last.inner_text()
                    print(f"\n📝 CAPTURED RESPONSE:\n{last_msg}")
                else:
                    print("⚠️  No messages found")
            except Exception as e:
                print(f"Error extracting: {e}")
        
        # Test queries
        send_and_report("Tell me about BCA", 1)
        send_and_report("What are the fees?", 2)
        send_and_report("admission process", 3)
        
        browser.close()
        
        print(f"\n\n📊 API CALLS CAPTURED: {len(all_responses)}")
        for resp in all_responses:
            print(f"   - {resp['url']}")

if __name__ == "__main__":
    run_test()
