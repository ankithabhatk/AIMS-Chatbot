#!/usr/bin/env python3
"""
Inspect frontend DOM to find chat widget elements
"""

import asyncio
from playwright.async_api import async_playwright

async def inspect_dom():
    """Inspect the frontend DOM structure"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("\n" + "="*80)
        print("🔍 Inspecting Frontend DOM Structure")
        print("="*80 + "\n")
        
        try:
            await page.goto("http://localhost:3001", timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            
            # Get page HTML to find widget
            content = await page.content()
            
            # Look for common chat widget patterns
            print("Looking for chat elements...")
            
            # Try to find all buttons
            buttons = await page.locator('button').all()
            print(f"\n✅ Found {len(buttons)} buttons:")
            for i, btn in enumerate(buttons[:10], 1):
                try:
                    text = await btn.text_content()
                    print(f"  [{i}] {text.strip()[:50]}")
                except:
                    pass
            
            # Look for inputs
            inputs = await page.locator('input').all()
            print(f"\n✅ Found {len(inputs)} input fields:")
            for i, inp in enumerate(inputs[:5], 1):
                try:
                    placeholder = await inp.get_attribute('placeholder')
                    type_attr = await inp.get_attribute('type')
                    print(f"  [{i}] type={type_attr}, placeholder={placeholder}")
                except:
                    pass
            
            # Look for textareas
            textareas = await page.locator('textarea').all()
            print(f"\n✅ Found {len(textareas)} textareas")
            
            # Look for specific data attributes
            print("\n🔍 Looking for chat-specific elements...")
            
            # Check for common chat widget attributes
            chat_elements = await page.locator('[class*="chat"]').all()
            print(f"Elements with 'chat' in class: {len(chat_elements)}")
            
            # Look for message/response containers
            messages = await page.locator('[role="article"]').all()
            print(f"Elements with role='article': {len(messages)}")
            
            # Try clicking a button that might open the widget
            print("\n🤖 Attempting to find and click widget button...")
            
            # Try different button selectors
            btn_selectors = [
                'button:has-text("Robot")',
                'button:has-text("Chat")',
                'button:has-text("Ask")',
                'button:last-of-type',
                'button[title*="Chat"]',
                'button[aria-label*="chat"]'
            ]
            
            for selector in btn_selectors:
                try:
                    btn = page.locator(selector)
                    if await btn.count() > 0:
                        print(f"✅ Found button with selector: {selector}")
                        break
                except:
                    pass
            
            # Get visible text on page
            page_text = await page.locator('body').text_content()
            if 'chat' in page_text.lower():
                print("✅ Page contains 'chat' text")
            if 'ask' in page_text.lower():
                print("✅ Page contains 'ask' text")
            
            # Take screenshot to see what's on page
            await page.screenshot(path="/tmp/dom_inspect.png")
            print("\n📸 Screenshot saved: /tmp/dom_inspect.png")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(inspect_dom())
    except Exception as e:
        print(f"❌ Failed: {e}")
