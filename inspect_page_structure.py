#!/usr/bin/env python3
"""
INSPECT PAGE STRUCTURE
Find actual form selectors before running validation
"""

import asyncio
from playwright.async_api import async_playwright

async def inspect():
    print("=" * 90)
    print("INSPECTING CHATBOT PAGE STRUCTURE")
    print("=" * 90)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("\n[1] Opening chatbot at http://localhost:3000...")
        try:
            await page.goto("http://localhost:3000", timeout=10000)
            await page.wait_for_load_state("networkidle")
            print("✅ Page loaded")
        except Exception as e:
            print(f"❌ Error loading page: {e}")
            await browser.close()
            return
        
        # Get all input fields
        print("\n[2] Finding input fields...")
        inputs = await page.locator("input").all()
        print(f"Found {len(inputs)} input elements")
        for i, inp in enumerate(inputs[:10]):
            try:
                inp_type = await inp.get_attribute("type")
                placeholder = await inp.get_attribute("placeholder")
                name = await inp.get_attribute("name")
                id_val = await inp.get_attribute("id")
                print(f"  Input {i}: type={inp_type}, placeholder={placeholder}, name={name}, id={id_val}")
            except:
                pass
        
        # Get all text areas
        print("\n[3] Finding textareas...")
        textareas = await page.locator("textarea").all()
        print(f"Found {len(textareas)} textarea elements")
        for i, ta in enumerate(textareas[:5]):
            try:
                placeholder = await ta.get_attribute("placeholder")
                name = await ta.get_attribute("name")
                print(f"  Textarea {i}: placeholder={placeholder}, name={name}")
            except:
                pass
        
        # Get all buttons
        print("\n[4] Finding buttons...")
        buttons = await page.locator("button").all()
        print(f"Found {len(buttons)} button elements")
        for i, btn in enumerate(buttons[:10]):
            try:
                text = await btn.text_content()
                print(f"  Button {i}: '{text.strip()}'")
            except:
                pass
        
        # Get all form elements
        print("\n[5] Finding form elements...")
        forms = await page.locator("form").all()
        print(f"Found {len(forms)} form elements")
        
        # Get page title and visible text
        print("\n[6] Page content preview...")
        title = await page.title()
        print(f"Page title: {title}")
        
        # Get text content of first 500 chars
        body_text = await page.locator("body").text_content()
        print(f"Visible text (first 300 chars): {body_text[:300]}")
        
        # Check for specific common patterns
        print("\n[7] Looking for common patterns...")
        
        # Check for select/combobox
        selects = await page.locator("select").all()
        print(f"Found {len(selects)} select elements")
        
        comboboxes = await page.locator("[role='combobox']").all()
        print(f"Found {len(comboboxes)} combobox elements")
        
        # Check for common class patterns
        chat_inputs = await page.locator("[class*='input'], [class*='chat']").all()
        print(f"Found {len(chat_inputs)} elements with 'input' or 'chat' in class")
        
        # Take a screenshot to see what's actually rendered
        print("\n[8] Taking screenshot of current state...")
        await page.screenshot(path="/Users/maneeth/Desktop/Chat-Bot/screenshots/inspect_page.png")
        print("✅ Screenshot saved: /Users/maneeth/Desktop/Chat-Bot/screenshots/inspect_page.png")
        
        # Print full HTML of first form (if exists)
        if forms:
            print("\n[9] First form HTML:")
            form_html = await forms[0].inner_html()
            print(form_html[:1000])
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
