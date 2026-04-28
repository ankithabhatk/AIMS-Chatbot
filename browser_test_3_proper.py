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
        page.locator(".floating-robot-trigger").click()
        time.sleep(2)
        
        print("\n📝 FILLING FORM PROPERLY...")
        
        # Fill form fields
        print("   Filling Full Name...")
        page.fill("input[name='name']", "Test User")
        time.sleep(0.5)
        
        print("   Filling Email...")
        page.fill("input[name='email']", "test@example.com")
        time.sleep(0.5)
        
        print("   Filling Mobile...")
        page.fill("input[name='mobile']", "9876543210")
        time.sleep(0.5)
        
        print("   Selecting Course...")
        # Course is a button grid, not a select
        bca_button = page.locator("div.radio-card:has-text('BCA')")
        if bca_button.count() == 0:
            # Try finding by text differently
            all_cards = page.locator(".radio-card")
            for i in range(all_cards.count()):
                text = all_cards.nth(i).inner_text()
                if "BCA" in text:
                    print(f"   Found BCA card at index {i}")
                    all_cards.nth(i).click()
                    break
        else:
            bca_button.click()
        time.sleep(0.5)
        
        print("   Clicking Submit...")
        page.screenshot(path="before_submit.png")
        page.click("button[type='submit']")
        time.sleep(3)
        
        page.screenshot(path="after_submit.png")
        
        print("\n✅ Form submitted!")
        
        print("\n🧪 NOW TESTING CHAT (after form submission)...")
        
        def send_query(query, step):
            print(f"\n🧪 Step {step}: {query}")
            
            # Find chat input
            chat_input = page.locator("textarea")
            if chat_input.count() > 0:
                print(f"   ✓ Chat input found")
                chat_input.fill(query)
                chat_input.press("Enter")
                time.sleep(2)
                
                page.screenshot(path=f"chat_step{step}.png")
                print(f"   📸 Screenshot saved: chat_step{step}.png")
                
                # Try to get response
                try:
                    messages = page.locator(".message, [class*='message']")
                    if messages.count() > 0:
                        last = messages.last.inner_text()
                        if last:
                            print(f"   📝 Bot response (first 200 chars): {last[:200]}")
                except:
                    pass
            else:
                print(f"   ❌ Chat input not found!")
        
        # NOW TEST CHAT
        send_query("I like coding", 1)
        send_query("Tell me about BCA", 2)
        send_query("What about fees?", 3)
        
        browser.close()

if __name__ == "__main__":
    run_test()
