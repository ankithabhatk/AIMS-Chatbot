#!/usr/bin/env python3
"""
Real UI test - click robot, select course, ask question, capture response
"""
import time
from playwright.sync_api import sync_playwright
import os

def run_ui_test():
    """Run real UI test"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"[BROWSER CONSOLE] {msg.type}: {msg.text}"))
        
        screenshot_dir = "test_screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        
        print("[TEST] Opening app...")
        page.goto("http://localhost:3000", wait_until="networkidle")
        time.sleep(2)
        
        # Screenshot 1: Initial state
        page.screenshot(path=f"{screenshot_dir}/01_initial.png")
        print("[SCREENSHOT] 01_initial.png")
        
        # Click the floating robot
        print("[TEST] Clicking floating robot...")
        try:
            robot = page.query_selector(".floating-robot-trigger")
            if robot:
                robot.click()
                time.sleep(2)
                page.screenshot(path=f"{screenshot_dir}/02_after_robot_click.png")
                print("[SCREENSHOT] 02_after_robot_click.png")
            else:
                print("[ERROR] Robot not found")
        except Exception as e:
            print(f"[ERROR] {e}")
        
        # Look for course selector and fill form
        print("[TEST] Looking for onboarding form...")
        try:
            # Wait for form inputs
            page.wait_for_selector("input[type='text'], input[type='email'], input[type='tel']", timeout=3000)
            
            # Fill in form fields
            inputs = page.query_selector_all("input[type='text'], input[type='email'], input[type='tel']")
            print(f"[TEST] Found {len(inputs)} input fields")
            
            if len(inputs) >= 3:
                # Fill name
                inputs[0].fill("Test User")
                print("[TEST] Filled name")
                
                # Fill email
                inputs[1].fill("test@example.com")
                print("[TEST] Filled email")
                
                # Fill phone
                inputs[2].fill("9876543210")
                print("[TEST] Filled phone")
            
            # Select BCA course
            buttons = page.query_selector_all("button, div[class*='radio']")
            print(f"[TEST] Found {len(buttons)} buttons/radio elements")
            
            for btn in buttons:
                text = btn.text_content().strip()
                if "BCA" in text or "bca" in text.lower():
                    print(f"[TEST] Found BCA button: {text}")
                    btn.click()
                    time.sleep(0.5)
                    page.screenshot(path=f"{screenshot_dir}/03_after_bca_select.png")
                    print("[SCREENSHOT] 03_after_bca_select.png")
                    break
            
            # Find and click Submit button
            submit_buttons = page.query_selector_all("button")
            for btn in submit_buttons:
                text = btn.text_content().strip()
                if "Submit" in text:
                    print("[TEST] Found Submit button, clicking...")
                    btn.click()
                    time.sleep(2)
                    page.screenshot(path=f"{screenshot_dir}/03b_after_submit.png")
                    print("[SCREENSHOT] 03b_after_submit.png")
                    break
        except Exception as e:
            print(f"[ERROR] Form filling: {e}")
        
        # Find chat input
        print("[TEST] Looking for chat input...")
        try:
            inputs = page.query_selector_all("input[type='text'], textarea, [contenteditable]")
            print(f"[TEST] Found {len(inputs)} input elements")
            
            if inputs:
                # Use the last input (usually the chat input)
                chat_input = inputs[-1]
                print("[TEST] Typing 'Fees structure'...")
                chat_input.fill("Fees structure")
                time.sleep(0.5)
                
                page.screenshot(path=f"{screenshot_dir}/04_after_typing.png")
                print("[SCREENSHOT] 04_after_typing.png")
                
                # Find send button
                send_buttons = page.query_selector_all("button")
                for btn in send_buttons:
                    text = btn.text_content().strip()
                    if "Send" in text or "→" in text or text == "":
                        # Try clicking this button
                        try:
                            btn.click()
                            print("[TEST] Clicked send button")
                            time.sleep(3)
                            break
                        except:
                            pass
                
                page.screenshot(path=f"{screenshot_dir}/05_after_send.png")
                print("[SCREENSHOT] 05_after_send.png")
                
                # Extract message
                print("\n[EXTRACTING MESSAGE]...")
                messages = page.query_selector_all("[role='article'], .message, [class*='message'], div")
                
                # Find the last message with substantial text
                for msg in reversed(messages):
                    text = msg.text_content().strip()
                    if len(text) > 50 and any(word in text.lower() for word in ['fee', 'bca', 'annual', '₹']):
                        print(f"\n[UI MESSAGE SHOWN]:\n{text}\n")
                        
                        # Analyze
                        print("[ANALYSIS]:")
                        has_bca = "BCA" in text or "bca" in text.lower()
                        has_multiple_courses = sum(1 for course in ['MBA', 'MCA', 'BBA', 'B.Com', 'M.Com', 'BHM'] if course in text) > 1
                        has_fallback = "Try asking about" in text
                        
                        print(f"- Only BCA fees? {'YES' if has_bca and not has_multiple_courses else 'NO'}")
                        print(f"- Any other courses shown? {'YES' if has_multiple_courses else 'NO'}")
                        print(f"- Fallback message shown? {'YES' if has_fallback else 'NO'}")
                        
                        # Save message
                        with open(f"{screenshot_dir}/message_content.txt", "w") as f:
                            f.write(text)
                        print(f"\n[SAVED] Message to message_content.txt")
                        break
        except Exception as e:
            print(f"[ERROR] Chat interaction: {e}")
        
        # Final screenshot
        page.screenshot(path=f"{screenshot_dir}/06_final.png")
        print("[SCREENSHOT] 06_final.png")
        
        print(f"\n[COMPLETE] Screenshots saved to {screenshot_dir}/")
        
        browser.close()

if __name__ == "__main__":
    run_ui_test()
