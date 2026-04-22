"""
TEST 1: VISIBLE BROWSER TEST
Run like a human user - see what happens
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def test_visible_browser():
    async with async_playwright() as p:
        # Launch browser VISIBLY (not headless)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("\n" + "="*80)
        print("🧪 TEST 1: VISIBLE BROWSER TEST")
        print("="*80)
        
        try:
            # Step 1: Navigate to frontend
            print("\n📍 Step 1: Navigating to frontend...")
            await page.goto('http://localhost:8001/professional.html', wait_until='networkidle')
            print("✅ Page loaded successfully")
            
            # Step 2: Take initial screenshot
            print("\n📸 Taking initial screenshot...")
            await page.screenshot(path='/tmp/test_01_initial.png')
            print("✅ Screenshot saved to /tmp/test_01_initial.png")
            
            # Step 3: Find and fill chat input
            print("\n💬 Step 2: Entering query...")
            query = "What programs does AIMS offer?"
            
            # Wait for input field
            input_selector = 'input[placeholder*="Ask about"], input[type="text"], input#chat-input, textarea'
            await page.wait_for_selector(input_selector, timeout=5000)
            print(f"✅ Input field found")
            
            # Type the query
            await page.fill(input_selector, query)
            print(f"✅ Typed: '{query}'")
            
            # Step 4: Click send button
            print("\n🚀 Step 3: Clicking send...")
            send_button = 'button:has-text("Send"), button[type="submit"], button#send'
            await page.click(send_button)
            print("✅ Send button clicked")
            
            # Step 5: Wait for response
            print("\n⏳ Step 4: Waiting for response...")
            await asyncio.sleep(3)  # Wait for AI response
            
            # Step 6: Take screenshot with response
            print("\n📸 Taking screenshot with response...")
            await page.screenshot(path='/tmp/test_01_response.png')
            print("✅ Response screenshot saved to /tmp/test_01_response.png")
            
            # Step 7: Extract response text
            print("\n📝 Step 5: Extracting response...")
            
            # Try multiple selectors for response text
            response_text = ""
            try:
                # Look for message container with response
                messages = await page.query_selector_all('.message-content, .response, [class*="response"], [class*="message"]')
                if messages:
                    response_text = await messages[-1].text_content()
                    print(f"✅ Found response (last message): {response_text[:100]}...")
            except:
                print("⚠️  Could not extract response text programmatically")
            
            # Step 8: Check for errors
            print("\n🔍 Step 6: Checking for errors...")
            errors = await page.query_selector_all('.error, [class*="error"]')
            if errors:
                error_text = await errors[0].text_content()
                print(f"❌ ERROR FOUND: {error_text}")
            else:
                print("✅ No error messages visible")
            
            # Step 9: Check page console for errors
            print("\n📋 Checking browser console...")
            page_errors = []
            page.on('console', lambda msg: page_errors.append(f"[{msg.type}] {msg.text}"))
            
            await asyncio.sleep(1)
            
            if page_errors:
                print(f"⚠️  Console messages: {page_errors}")
            else:
                print("✅ No console errors detected")
            
            # Print final report
            print("\n" + "="*80)
            print("📊 TEST 1 SUMMARY")
            print("="*80)
            print(f"✅ Frontend URL:         http://localhost:8001/professional.html")
            print(f"✅ Query sent:           '{query}'")
            print(f"✅ Response visible:     {'Yes' if response_text else 'Check screenshot'}")
            print(f"✅ Initial screenshot:   /tmp/test_01_initial.png")
            print(f"✅ Response screenshot:  /tmp/test_01_response.png")
            print(f"✅ Status:               {'PASSED ✅' if not errors else 'FAILED ❌'}")
            print("="*80)
            
            # Keep browser open for inspection
            print("\n👀 Browser is open for inspection. Closing in 5 seconds...")
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_visible_browser())
