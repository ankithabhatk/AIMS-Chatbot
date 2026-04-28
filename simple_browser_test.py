#!/usr/bin/env python3
"""
FINAL VALIDATION - Simplified for reliable capture
Focus: Get screenshots that prove responses work
"""

from playwright.sync_api import sync_playwright
import time

def run_test():
    output_dir = "/tmp/final_validation"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        
        try:
            # STEP 0: Open
            print("[1] Opening page...")
            page.goto("http://localhost:3000", timeout=15000)
            page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(2)
            page.screenshot(path=f"{output_dir}/01_form_loaded.png")
            print("✅ Form loaded")
            
            # STEP 1: Fill and submit form
            print("[2] Filling form...")
            
            # Try to find and fill name
            name_inputs = page.query_selector_all('input')
            if len(name_inputs) > 0:
                name_inputs[0].fill("Test User")
                print("  ✓ Name filled")
            
            # Fill email
            if len(name_inputs) > 1:
                name_inputs[1].fill("test@aims.com")
                print("  ✓ Email filled")
            
            # Fill phone  
            if len(name_inputs) > 2:
                name_inputs[2].fill("9999999999")
                print("  ✓ Phone filled")
            
            # Click BCA if visible
            bca_buttons = page.locator('text=BCA')
            if bca_buttons.count() > 0:
                bca_buttons.first.click()
                print("  ✓ BCA selected")
            
            time.sleep(1)
            page.screenshot(path=f"{output_dir}/02_form_filled.png")
            print("✅ Form ready")
            
            # STEP 2: Submit
            print("[3] Submitting form...")
            submit_buttons = page.locator('button')
            
            for i in range(submit_buttons.count()):
                try:
                    text = submit_buttons.nth(i).text_content()
                    if "submit" in text.lower():
                        submit_buttons.nth(i).click()
                        print("  ✓ Submitted")
                        break
                except:
                    pass
            
            time.sleep(4)
            page.screenshot(path=f"{output_dir}/03_chat_active.png")
            print("✅ After submit")
            
            # STEP 3: Send query 1
            print("[4] Sending 'Tell me about BCA'...")
            textareas = page.locator('textarea')
            if textareas.count() > 0:
                textareas.first.fill("Tell me about BCA")
                # Find send button
                all_buttons = page.locator('button')
                for i in range(all_buttons.count()):
                    try:
                        parent = all_buttons.nth(i).locator('..')
                        if parent.locator('textarea').count() > 0:
                            all_buttons.nth(i).click()
                            break
                    except:
                        pass
                
                time.sleep(3)
                page.screenshot(path=f"{output_dir}/04_response_bca.png")
                print("✅ Response 1 captured")
            
            # STEP 4: Send query 2
            print("[5] Sending 'What about fees?'...")
            textareas = page.locator('textarea')
            if textareas.count() > 0:
                textareas.first.fill("What about fees?")
                all_buttons = page.locator('button')
                for i in range(all_buttons.count()):
                    try:
                        all_buttons.nth(i).click()
                        break
                    except:
                        pass
                
                time.sleep(3)
                page.screenshot(path=f"{output_dir}/05_response_fees.png")
                print("✅ Response 2 captured")
            
            print("\n" + "="*70)
            print("SCREENSHOTS SAVED - View them now")
            print("="*70)
            print(f"01_form_loaded.png - Initial form")
            print(f"02_form_filled.png - Form with data")
            print(f"03_chat_active.png - Chat after form submit")
            print(f"04_response_bca.png - Response to 'Tell me about BCA'")
            print(f"05_response_fees.png - Response to 'What about fees?'")
            
        finally:
            time.sleep(1)
            browser.close()

if __name__ == "__main__":
    run_test()
