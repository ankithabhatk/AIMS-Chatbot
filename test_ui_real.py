#!/usr/bin/env python3
"""
Real UI test - captures actual browser behavior with screenshots
"""
import time
from playwright.sync_api import sync_playwright
import os
from datetime import datetime

def run_ui_test():
    """Run real UI test and capture screenshots"""
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to app
        print("[TEST] Opening app at http://localhost:3000")
        page.goto("http://localhost:3000", wait_until="networkidle")
        time.sleep(2)
        
        # Take screenshot of initial state
        screenshot_dir = "test_screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        
        page.screenshot(path=f"{screenshot_dir}/01_initial_state.png")
        print("[SCREENSHOT] 01_initial_state.png")
        
        # Look for course selector
        print("[TEST] Looking for course selector...")
        
        # Try to find and click BCA option
        try:
            # Wait for course selector to be visible
            page.wait_for_selector("button, select, [role='combobox']", timeout=5000)
            
            # Take screenshot before selection
            page.screenshot(path=f"{screenshot_dir}/02_before_course_select.png")
            print("[SCREENSHOT] 02_before_course_select.png")
            
            # Look for BCA button or option
            bca_buttons = page.query_selector_all("button:has-text('BCA'), [data-value='BCA'], option:has-text('BCA')")
            
            if bca_buttons:
                print(f"[TEST] Found {len(bca_buttons)} BCA option(s)")
                bca_buttons[0].click()
                time.sleep(1)
                page.screenshot(path=f"{screenshot_dir}/03_after_course_select.png")
                print("[SCREENSHOT] 03_after_course_select.png")
            else:
                print("[TEST] BCA button not found, trying alternative selectors...")
                # Try clicking any button that might be a course selector
                buttons = page.query_selector_all("button")
                print(f"[TEST] Found {len(buttons)} buttons total")
                for i, btn in enumerate(buttons[:5]):
                    text = btn.text_content()
                    print(f"  Button {i}: {text}")
        except Exception as e:
            print(f"[ERROR] Course selection failed: {e}")
        
        # Find and click chat input
        print("[TEST] Looking for chat input...")
        try:
            # Wait for input field
            page.wait_for_selector("input[type='text'], textarea, [contenteditable='true']", timeout=5000)
            
            # Find input
            inputs = page.query_selector_all("input[type='text'], textarea")
            if inputs:
                print(f"[TEST] Found {len(inputs)} input field(s)")
                chat_input = inputs[-1]  # Usually the last input is the chat input
                
                # Type message
                print("[TEST] Typing 'Fees structure'...")
                chat_input.fill("Fees structure")
                time.sleep(0.5)
                
                page.screenshot(path=f"{screenshot_dir}/04_after_typing.png")
                print("[SCREENSHOT] 04_after_typing.png")
                
                # Find and click send button
                send_buttons = page.query_selector_all("button:has-text('Send'), button[type='submit'], button:has-text('→')")
                if send_buttons:
                    print("[TEST] Clicking send button...")
                    send_buttons[0].click()
                    
                    # Wait for response
                    print("[TEST] Waiting for response...")
                    time.sleep(3)
                    
                    page.screenshot(path=f"{screenshot_dir}/05_after_send.png")
                    print("[SCREENSHOT] 05_after_send.png")
                    
                    # Extract message text
                    messages = page.query_selector_all("[role='article'], .message, .chat-message, [class*='message']")
                    print(f"\n[RESULT] Found {len(messages)} message elements")
                    
                    if messages:
                        last_message = messages[-1]
                        message_text = last_message.text_content()
                        print(f"\n[UI MESSAGE SHOWN]:\n{message_text}\n")
                        
                        # Analyze message
                        print("[ANALYSIS]:")
                        print(f"- Only BCA fees? {'YES' if 'BCA' in message_text and message_text.count('₹') == 1 else 'NO'}")
                        print(f"- Any other courses shown? {'YES' if any(course in message_text for course in ['MBA', 'MCA', 'BBA', 'B.Com', 'M.Com', 'BHM']) and 'BCA' in message_text else 'NO'}")
                        print(f"- Fallback message shown? {'YES' if 'Try asking about' in message_text else 'NO'}")
                        
                        # Save message to file
                        with open(f"{screenshot_dir}/message_content.txt", "w") as f:
                            f.write(message_text)
                        print(f"\n[SAVED] Message content to message_content.txt")
                else:
                    print("[ERROR] Send button not found")
            else:
                print("[ERROR] Input field not found")
        except Exception as e:
            print(f"[ERROR] Chat interaction failed: {e}")
        
        # Final screenshot
        time.sleep(1)
        page.screenshot(path=f"{screenshot_dir}/06_final_state.png")
        print("[SCREENSHOT] 06_final_state.png")
        
        print(f"\n[COMPLETE] All screenshots saved to {screenshot_dir}/")
        
        browser.close()

if __name__ == "__main__":
    run_ui_test()
