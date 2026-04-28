#!/usr/bin/env python3
"""
Visual Proof Capture - Headless browser test
Captures what USER actually sees (screenshots + responses)
NO analysis, NO fixes - ONLY observation
"""

from playwright.sync_api import sync_playwright
import time

def capture_conversation():
    """Run headless browser test and capture screenshots"""
    
    print("🎬 Starting headless browser test...")
    print("Capturing visual proof of user experience\n")
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("📱 Opening chatbot frontend...")
        page.goto("http://localhost:3000")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Test queries
        queries = [
            "I like coding",
            "Tell me about BCA",
            "What about MCA?"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n{'='*70}")
            print(f"STEP {i}: User types '{query}'")
            print(f"{'='*70}")
            
            # Find input field and type
            input_selector = "input[type='text'], textarea, input[placeholder*='message'], input[placeholder*='type']"
            page.fill(input_selector, query)
            page.keyboard.press("Enter")
            
            # Wait for response to render
            print("⏳ Waiting for response to render...")
            time.sleep(3)  # Give time for response to fully render
            
            # Take screenshot
            screenshot_path = f"step{i}.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot saved: {screenshot_path}")
            
            # Try to extract bot response from page
            try:
                # Common selectors for chat responses
                response_selectors = [
                    ".bot-message:last-child",
                    ".message.bot:last-child",
                    ".chat-message.bot:last-child",
                    "[class*='bot']:last-child",
                    "[class*='response']:last-child"
                ]
                
                bot_response = None
                for selector in response_selectors:
                    try:
                        element = page.locator(selector).last
                        if element.count() > 0:
                            bot_response = element.inner_text()
                            break
                    except:
                        continue
                
                if bot_response:
                    print(f"\n🤖 BOT RESPONSE:")
                    print(f"{bot_response[:300]}{'...' if len(bot_response) > 300 else ''}")
                else:
                    print("\n⚠️  Could not extract bot response from DOM")
                    print("   (Check screenshot for visual confirmation)")
                    
            except Exception as e:
                print(f"\n⚠️  Error extracting response: {e}")
                print("   (Check screenshot for visual confirmation)")
        
        print(f"\n{'='*70}")
        print("✅ All screenshots captured")
        print(f"{'='*70}\n")
        
        browser.close()
    
    print("📁 Screenshots saved:")
    print("   - step1.png (I like coding)")
    print("   - step2.png (Tell me about BCA)")
    print("   - step3.png (What about MCA?)")
    print("\n👉 Visual proof captured - ready for analysis\n")

if __name__ == "__main__":
    try:
        capture_conversation()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Is frontend running on http://localhost:3000?")
        print("2. Is Playwright installed? Run: pip install playwright && playwright install")
        print("3. Check if browser can access the frontend")
