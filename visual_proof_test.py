import asyncio
from playwright.async_api import async_playwright
import os
import time

async def run_test():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        print("1. Opening chatbot frontend at http://localhost:3000")
        try:
            await page.goto("http://localhost:3000", wait_until="networkidle")
        except Exception as e:
            print(f"Error loading page: {e}")
            await browser.close()
            return

        await page.wait_for_timeout(2000)
        
        # Start a new session
        print("2. Starting a new session...")
        trigger = await page.query_selector(".floating-robot-trigger")
        if trigger:
            print("Clicking floating robot trigger...")
            await trigger.click()
            await page.wait_for_timeout(1000)
        
        # Check if we need to click "New Chat"
        new_chat_btn = await page.query_selector(".new-chat-btn")
        if new_chat_btn:
            print("Clicking New Chat button...")
            await new_chat_btn.click()
            await page.wait_for_timeout(1000)
            
        messages = ["I like coding", "Tell me about BCA", "What about MCA?"]
        
        for i, msg in enumerate(messages, 1):
            print(f"\n--- Step {i}: '{msg}' ---")
            
            # Count current bot messages
            initial_bot_msgs = await page.query_selector_all(".message-row.bot")
            initial_count = len(initial_bot_msgs)
            
            print(f"Sending message: {msg}")
            await page.fill(".chat-textarea", msg)
            await page.click(".send-btn")
            
            # Wait for response to appear (count to increase)
            print("Waiting for response to render...")
            
            # Poll for new message
            timeout = 30 # seconds
            start_time = time.time()
            new_count = initial_count
            while new_count <= initial_count and time.time() - start_time < timeout:
                bot_msgs = await page.query_selector_all(".message-row.bot")
                new_count = len(bot_msgs)
                await asyncio.sleep(0.5)
            
            if new_count <= initial_count:
                print("Warning: Timed out waiting for new response.")
            
            # Wait for typing indicator to disappear if it exists
            typing = await page.query_selector(".typing-indicator")
            if typing:
                await page.wait_for_selector(".typing-indicator", state="hidden", timeout=10000)
            
            # Wait a bit more for full rendering/animation
            await page.wait_for_timeout(2000)
            
            # Get the last bot response text
            bot_msgs = await page.query_selector_all(".message-row.bot .message-content")
            if bot_msgs:
                last_response = await bot_msgs[-1].inner_text()
                print(f"RAW RESPONSE:\n{last_response}")
            else:
                print("No bot messages found.")
            
            # Save screenshot
            screenshot_name = f"step{i}.png"
            await page.screenshot(path=screenshot_name, full_page=False)
            print(f"Screenshot saved: {os.path.abspath(screenshot_name)}")
            
        print("\nTest execution complete.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())
