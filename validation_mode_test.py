#!/usr/bin/env python3
"""
VALIDATION MODE - Browser Observation Only
No code changes. Screenshot only. Report findings.

Test scenarios:
1. Onboarding (form visible)
2. Course query ("Tell me about BCA")
3. Typo query ("what is college located?")
4. Location query (test link clickability)
"""

from playwright.sync_api import sync_playwright
import time
import os

output_dir = "/tmp/validation_screenshots"
os.makedirs(output_dir, exist_ok=True)

def run_validation():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        
        print("\n" + "="*80)
        print("VALIDATION MODE - Browser Observation Only")
        print("="*80)
        
        try:
            # ========================================
            # STEP 1: Onboarding
            # ========================================
            print("\n[STEP 1] ONBOARDING")
            print("-" * 80)
            page.goto("http://localhost:3000", timeout=15000)
            page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(2)
            
            page.screenshot(path=f"{output_dir}/01_landing_page.png")
            print("✓ Screenshot: 01_landing_page.png")
            print("  Observation: Landing page with robot icon visible")
            
            # Click robot to open chat - find button by aria-label or direct click
            time.sleep(1)
            # Try to find and click the robot button (usually a button element)
            buttons = page.locator('button')
            robot_clicked = False
            for i in range(buttons.count()):
                try:
                    # Try clicking each button - the robot should respond
                    buttons.nth(i).click()
                    robot_clicked = True
                    time.sleep(2)
                    break
                except:
                    pass
            
            if robot_clicked:
                page.screenshot(path=f"{output_dir}/02_form_modal_open.png")
                print("✓ Screenshot: 02_form_modal_open.png")
                print("  Observation: Form modal appears (onboarding)")
            
            # ========================================
            # STEP 2: Fill form and submit
            # ========================================
            print("\n[STEP 2] FORM SUBMISSION")
            print("-" * 80)
            
            # Fill inputs
            inputs = page.locator('input')
            if inputs.count() >= 3:
                inputs.nth(0).fill("Test User")
                inputs.nth(1).fill("test@aims.com")
                inputs.nth(2).fill("9999999999")
                print("✓ Form fields filled")
            
            # Select BCA
            bca = page.locator('text=BCA').first
            if bca.count() > 0:
                bca.click()
                print("✓ BCA selected")
                time.sleep(1)
                page.screenshot(path=f"{output_dir}/03_form_filled_bca.png")
                print("✓ Screenshot: 03_form_filled_bca.png")
            
            # Submit
            submit = page.locator('button:has-text("Submit")')
            if submit.count() > 0:
                submit.click()
                time.sleep(3)
                page.screenshot(path=f"{output_dir}/04_chat_after_submit.png")
                print("✓ Screenshot: 04_chat_after_submit.png")
                print("  Observation: Chat window after form submission")
            
            # ========================================
            # STEP 3: Course Query (should be context-aware)
            # ========================================
            print("\n[STEP 3] COURSE QUERY - 'Tell me about BCA'")
            print("-" * 80)
            
            textarea = page.locator('textarea').first
            if textarea.count() > 0:
                textarea.fill("Tell me about BCA")
                # Find send button (usually near textarea)
                send_btn = page.locator('button').first
                send_btn.click()
                time.sleep(4)
                
                page.screenshot(path=f"{output_dir}/05_response_bca_course.png")
                print("✓ Screenshot: 05_response_bca_course.png")
                print("  Observation: Response to 'Tell me about BCA'")
                
                # Check if response mentions BCA
                response_text = page.inner_text('body')
                if 'bca' in response_text.lower():
                    print("  ✓ Response mentions BCA")
                else:
                    print("  ✗ Response does NOT mention BCA (context lost?)")
            
            # ========================================
            # STEP 4: Typo Query (intentionally wrong)
            # ========================================
            print("\n[STEP 4] TYPO/AMBIGUOUS QUERY - 'what is college located?'")
            print("-" * 80)
            
            textarea = page.locator('textarea').first
            if textarea.count() > 0:
                textarea.fill("what is college located?")
                send_btn = page.locator('button').first
                send_btn.click()
                time.sleep(4)
                
                page.screenshot(path=f"{output_dir}/06_response_typo_query.png")
                print("✓ Screenshot: 06_response_typo_query.png")
                print("  Observation: Response to nonsensical/typo query")
                
                response_text = page.inner_text('body')
                if 'please clarify' in response_text.lower() or 'not sure' in response_text.lower():
                    print("  ✓ System detected ambiguity and asked for clarification")
                else:
                    print("  ✗ System answered confidently despite unclear query (weak intent handling)")
            
            # ========================================
            # STEP 5: Location Query (test link)
            # ========================================
            print("\n[STEP 5] LOCATION QUERY - 'Where is the campus?'")
            print("-" * 80)
            
            textarea = page.locator('textarea').first
            if textarea.count() > 0:
                textarea.fill("Where is the campus?")
                send_btn = page.locator('button').first
                send_btn.click()
                time.sleep(4)
                
                page.screenshot(path=f"{output_dir}/07_response_location.png")
                print("✓ Screenshot: 07_response_location.png")
                print("  Observation: Response with location/link")
                
                # Check for links
                links = page.locator('a')
                if links.count() > 0:
                    print(f"  ✓ Found {links.count()} link(s)")
                    for i in range(min(2, links.count())):
                        href = links.nth(i).get_attribute('href')
                        print(f"    - Link {i+1}: {href}")
                else:
                    print("  ✗ No clickable links found")
            
            # ========================================
            # SUMMARY
            # ========================================
            print("\n" + "="*80)
            print("VALIDATION COMPLETE")
            print("="*80)
            print("\nScreenshots saved to:", output_dir)
            print("\nFiles:")
            print("  01_landing_page.png - Initial state")
            print("  02_form_modal_open.png - Form visible")
            print("  03_form_filled_bca.png - Form with BCA selected")
            print("  04_chat_after_submit.png - Chat after form submit")
            print("  05_response_bca_course.png - Response to course query")
            print("  06_response_typo_query.png - Response to typo/unclear query")
            print("  07_response_location.png - Response with potential link")
            
            print("\nNext: Review screenshots and compare with expected behavior")
            print("Do NOT fix yet - identify patterns first")
            
        finally:
            time.sleep(1)
            browser.close()

if __name__ == "__main__":
    run_validation()
