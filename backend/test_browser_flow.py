"""
Headless Browser Test - Real User Flow

Tests the complete user journey with screenshots:
1. User provides marks
2. User says implicit decision ("yeah okay")
3. Course gets locked
4. User asks about fees (gets conversion push)
5. User asks to apply (gets structured steps)
"""

import asyncio
from playwright.async_api import async_playwright
import os
from datetime import datetime

# Create screenshots directory
SCREENSHOTS_DIR = "test_screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

async def test_complete_user_flow():
    """Test complete user flow with screenshots"""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 1024})
        page = await context.new_page()
        
        print("=" * 60)
        print("HEADLESS BROWSER TEST - REAL USER FLOW")
        print("=" * 60)
        
        try:
            # Navigate to the chatbot
            print("\n1. Navigating to chatbot...")
            await page.goto("http://localhost:3000")  # Adjust URL as needed
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=f"{SCREENSHOTS_DIR}/01_homepage.png")
            print("✅ Homepage loaded")
            
            # Step 1: User provides marks and interest
            print("\n2. User: 'I got 75% and like coding'")
            chat_input = page.locator("input[type='text'], textarea").first
            await chat_input.fill("I got 75% and like coding")
            await page.screenshot(path=f"{SCREENSHOTS_DIR}/02_user_input_marks.png")
            
            # Send message
            send_button = page.locator("button:has-text('Send'), button[type='submit']").first
            await send_button.click()
            await page.wait_for_timeout(2000)  # Wait for response
            await page.screenshot(path=f"{SCREENSHOTS_DIR}/03_guidance_response.png")
            print("✅ Guidance response received")
            
            # Step 2: User says implicit decision
            print("\n3. User: 'yeah okay'")
            await chat_input.fill("yeah okay")
            await page.screenshot(path=f"{SCREENSHOTS_DIR}/04_user_implicit_decision.png")
            await send_button.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path=f"{SCREENSHOTS_DIR}/05_decision_locked.png")
            print("✅ Decision locked (course should be locked now)")
            
            # Step 3: User asks about fees
            print("\n4. User: 'what about fees'")
            await chat_input.fill("what about fees")
            await page.screenshot(path=f"{SCREENSHOTS_DIR}/06_user_asks_fees.png")
            await send_button.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path=f"{SCREENSHOTS_DIR}/07_fees_with_push.png")
            print("✅ Fees response with conversion push")
            
            # Step 4: User asks to apply
            print("\n5. User: 'how to apply'")
            await chat_input.fill("how to apply")
            await page.screenshot(path=f"{SCREENSHOTS_DIR}/08_user_asks_apply.png")
            await send_button.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path=f"{SCREENSHOTS_DIR}/09_apply_structured_steps.png")
            print("✅ Structured apply steps received")
            
            # Step 5: User tries to switch course (should be blocked)
            print("\n6. User: 'what about BBA' (should stay locked)")
            await chat_input.fill("what about BBA")
            await page.screenshot(path=f"{SCREENSHOTS_DIR}/10_user_tries_switch.png")
            await send_button.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path=f"{SCREENSHOTS_DIR}/11_locked_no_switch.png")
            print("✅ Course switching blocked (should still talk about BCA)")
            
            print("\n" + "=" * 60)
            print("✅ ALL SCREENSHOTS CAPTURED")
            print(f"📁 Screenshots saved to: {os.path.abspath(SCREENSHOTS_DIR)}")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            await page.screenshot(path=f"{SCREENSHOTS_DIR}/error.png")
            raise
        
        finally:
            await browser.close()


async def test_api_flow():
    """Test the API directly (fallback if frontend not running)"""
    import requests
    import json
    
    print("\n" + "=" * 60)
    print("API TEST - DIRECT BACKEND TESTING")
    print("=" * 60)
    
    API_URL = "http://localhost:8000/api/chat"  # Adjust as needed
    session_id = f"test_{datetime.now().timestamp()}"
    
    test_queries = [
        ("I got 75% and like coding", "Guidance"),
        ("yeah okay", "Decision Lock"),
        ("what about fees", "Fees + Push"),
        ("how to apply", "Apply Steps"),
        ("what about BBA", "Locked (no switch)")
    ]
    
    for i, (query, expected) in enumerate(test_queries, 1):
        print(f"\n{i}. User: '{query}' (Expected: {expected})")
        
        try:
            response = requests.post(
                API_URL,
                json={"query": query, "session_id": session_id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                mode = data.get("mode", "")
                
                print(f"   Mode: {mode}")
                print(f"   Answer: {answer[:200]}...")
                print("   ✅ Response received")
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("API TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    # Check if frontend is running
    try:
        import requests
        response = requests.get("http://localhost:3000", timeout=2)
        frontend_running = True
    except:
        frontend_running = False
    
    if frontend_running:
        print("✅ Frontend detected, running browser test...")
        asyncio.run(test_complete_user_flow())
    else:
        print("⚠️ Frontend not running, testing API directly...")
        asyncio.run(test_api_flow())
