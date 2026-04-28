#!/usr/bin/env python3
"""
FINAL VALIDATION: Real browser screenshots showing actual responses
Only screenshots count as proof. No logs, no API results. Just UI.
"""

from playwright.sync_api import sync_playwright, expect
import time
import uuid
import os

def test_real_user_flow():
    """Capture actual user experience in screenshots"""
    
    output_dir = "/tmp/final_validation"
    os.makedirs(output_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=[
            "--disable-blink-features=AutomationControlled"
        ])
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        
        try:
            print("\n" + "="*80)
            print("FINAL VALIDATION TEST - REAL BROWSER PROOF")
            print("="*80)
            
            # STEP 0: Open page
            print("\n[STEP 0] Opening chat page...")
            page.goto("http://localhost:3000", wait_until="networkidle", timeout=10000)
            time.sleep(2)
            
            page.screenshot(path=f"{output_dir}/00_initial_page.png")
            print("✅ Screenshot: 00_initial_page.png (showing form)")
            
            # STEP 1: Fill form fields
            print("\n[STEP 1] Filling form with real data...")
            
            # Try multiple selectors for name field
            name_input = None
            for selector in ['input[placeholder*="Name"]', 'input[placeholder*="name"]', 'input[type="text"]']:
                try:
                    name_input = page.query_selector(selector)
                    if name_input:
                        break
                except:
                    pass
            
            if name_input:
                name_input.fill("Rajesh Kumar")
                print("  ✓ Name: Rajesh Kumar")
            
            # Email
            email_input = None
            for selector in ['input[placeholder*="Email"]', 'input[type="email"]']:
                try:
                    email_input = page.query_selector(selector)
                    if email_input:
                        break
                except:
                    pass
            
            if email_input:
                email_input.fill("rajesh@example.com")
                print("  ✓ Email: rajesh@example.com")
            
            # Phone
            phone_input = None
            for selector in ['input[placeholder*="Phone"]', 'input[placeholder*="phone"]', 'input[placeholder*="Mobile"]']:
                try:
                    phone_input = page.query_selector(selector)
                    if phone_input:
                        break
                except:
                    pass
            
            if phone_input:
                phone_input.fill("9999999999")
                print("  ✓ Phone: 9999999999")
            
            # Select BCA course
            print("  Selecting course...")
            bca_selectors = [
                'input[value="BCA"]',
                '[data-value="BCA"]',
                'label:has-text("BCA")',
                'button:has-text("BCA")'
            ]
            
            for selector in bca_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        element.click()
                        print("  ✓ Course: BCA (selected)")
                        break
                except:
                    pass
            
            time.sleep(1)
            page.screenshot(path=f"{output_dir}/01_form_filled.png")
            print("✅ Screenshot: 01_form_filled.png (showing completed form)")
            
            # STEP 2: Submit form
            print("\n[STEP 2] Submitting form...")
            
            submit_btn = None
            for selector in ['button:has-text("Submit")', 'button[type="submit"]', 'button:has-text("submit")']:
                try:
                    submit_btn = page.query_selector(selector)
                    if submit_btn:
                        submit_btn.click()
                        print("  ✓ Form submitted")
                        break
                except:
                    pass
            
            time.sleep(3)  # Wait for form to close and chat to appear
            
            page.screenshot(path=f"{output_dir}/02_after_form_submit.png")
            print("✅ Screenshot: 02_after_form_submit.png (form should be gone, chat active)")
            
            # STEP 3: First query - "I like coding"
            print("\n[STEP 3] Sending query: 'I like coding'...")
            
            input_field = None
            for selector in ['textarea', 'input[placeholder*="message"]', 'input[placeholder*="ask"]', 'input[placeholder*="type"]']:
                try:
                    el = page.query_selector(selector)
                    if el:
                        input_field = el
                        break
                except:
                    pass
            
            if input_field:
                input_field.fill("I like coding")
                print("  ✓ Query typed")
                
                # Send
                send_btn = None
                for selector in ['button[type="submit"]', 'button svg[viewBox*="send"]', 'button:has-text("Send")']:
                    try:
                        btn = page.query_selector(selector)
                        if btn:
                            send_btn = btn
                            break
                    except:
                        pass
                
                if send_btn:
                    send_btn.click()
                    print("  ✓ Sent")
                
                time.sleep(2)
                
                page.screenshot(path=f"{output_dir}/03_response_i_like_coding.png")
                print("✅ Screenshot: 03_response_i_like_coding.png (response to 'I like coding')")
            
            # STEP 4: Second query - "Tell me about BCA"
            print("\n[STEP 4] Sending query: 'Tell me about BCA'...")
            
            if input_field:
                input_field.fill("Tell me about BCA")
                print("  ✓ Query typed")
                
                send_btn = page.query_selector('button[type="submit"]') or page.query_selector('button')
                if send_btn:
                    send_btn.click()
                    print("  ✓ Sent")
                
                time.sleep(2)
                
                page.screenshot(path=f"{output_dir}/04_response_tell_me_about_bca.png")
                print("✅ Screenshot: 04_response_tell_me_about_bca.png (response to 'Tell me about BCA')")
            
            # STEP 5: Third query - "What about MCA?"
            print("\n[STEP 5] Sending query: 'What about MCA?'...")
            
            if input_field:
                input_field.fill("What about MCA?")
                print("  ✓ Query typed")
                
                send_btn = page.query_selector('button[type="submit"]') or page.query_selector('button')
                if send_btn:
                    send_btn.click()
                    print("  ✓ Sent")
                
                time.sleep(2)
                
                page.screenshot(path=f"{output_dir}/05_response_what_about_mca.png")
                print("✅ Screenshot: 05_response_what_about_mca.png (response to 'What about MCA?')")
            
            print("\n" + "="*80)
            print("TEST COMPLETE - SCREENSHOTS SAVED")
            print("="*80)
            print(f"\n📁 Output directory: {output_dir}/")
            print("\nScreenshots:")
            print("  1. 00_initial_page.png         → Form visible")
            print("  2. 01_form_filled.png         → Form with data entered")
            print("  3. 02_after_form_submit.png   → Chat unlocked, form gone")
            print("  4. 03_response_i_like_coding.png          → First response")
            print("  5. 04_response_tell_me_about_bca.png      → BCA-specific response")
            print("  6. 05_response_what_about_mca.png         → MCA response")
            print("\n🔍 VERIFICATION:")
            print("  ✓ If chat is active after form → Frontend fix working")
            print("  ✓ If responses mention courses → Backend fix working")
            print("  ✓ If BCA response is specific → Course context working")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            page.screenshot(path=f"{output_dir}/error.png")
            import traceback
            traceback.print_exc()
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    test_real_user_flow()
