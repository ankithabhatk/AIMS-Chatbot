"""
Comprehensive browser test to find ALL remaining issues.

This test will:
1. Open the actual UI in a browser
2. Test all critical user flows
3. Capture screenshots of failures
4. Report exact issues with evidence

NO HALF-WAY. Find every bug.
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import os

# Test configuration
FRONTEND_URL = "http://localhost:3000"
SCREENSHOT_DIR = "test_screenshots_comprehensive"

# Create screenshot directory
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def setup_browser():
    """Setup Chrome browser with options."""
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    # Remove headless to see what's happening
    # options.add_argument('--headless')
    
    driver = webdriver.Chrome(options=options)
    return driver

def wait_for_response(driver, timeout=10):
    """Wait for bot response to appear."""
    time.sleep(2)  # Give time for response to render
    
def send_message(driver, message):
    """Send a message in the chat."""
    try:
        # Find input field
        input_field = driver.find_element(By.CSS_SELECTOR, "textarea, input[type='text']")
        input_field.clear()
        input_field.send_keys(message)
        input_field.send_keys(Keys.RETURN)
        
        wait_for_response(driver)
        return True
    except Exception as e:
        print(f"   ❌ Failed to send message: {e}")
        return False

def get_last_bot_message(driver):
    """Get the last bot message from the chat."""
    try:
        # Find all bot messages
        messages = driver.find_elements(By.CSS_SELECTOR, "[class*='message'], [class*='Message']")
        
        # Get the last message text
        if messages:
            last_message = messages[-1].text
            return last_message
        return ""
    except Exception as e:
        print(f"   ⚠️  Could not extract message: {e}")
        return ""

def check_for_lead_capture(response):
    """Check if response is asking for lead capture."""
    lead_indicators = [
        "provide your name",
        "provide your email",
        "provide your phone",
        "enter your details",
        "share your contact",
        "name, email",
        "email, phone"
    ]
    
    response_lower = response.lower()
    for indicator in lead_indicators:
        if indicator in response_lower:
            return True
    return False

def check_for_garbage_content(response, forbidden_keywords):
    """Check if response contains forbidden/irrelevant content."""
    response_lower = response.lower()
    found = []
    for keyword in forbidden_keywords:
        if keyword.lower() in response_lower:
            found.append(keyword)
    return found

def run_test_suite():
    """Run comprehensive test suite."""
    driver = setup_browser()
    
    try:
        print("=" * 80)
        print("COMPREHENSIVE BROWSER TEST - FINDING ALL BUGS")
        print("=" * 80)
        
        # Navigate to frontend
        print(f"\n[SETUP] Opening {FRONTEND_URL}")
        driver.get(FRONTEND_URL)
        time.sleep(3)
        
        # Take initial screenshot
        driver.save_screenshot(f"{SCREENSHOT_DIR}/01_initial_page.png")
        print("✅ Page loaded")
        
        # Click chat button to open chat
        try:
            chat_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button, [role='button']"))
            )
            chat_button.click()
            time.sleep(2)
            driver.save_screenshot(f"{SCREENSHOT_DIR}/02_chat_opened.png")
            print("✅ Chat opened")
        except Exception as e:
            print(f"❌ Could not open chat: {e}")
            driver.save_screenshot(f"{SCREENSHOT_DIR}/02_chat_open_failed.png")
            return
        
        # Test cases
        test_cases = [
            {
                "name": "Courses Query",
                "query": "What courses are offered?",
                "expected_keywords": ["MBA", "BCA", "BBA"],
                "forbidden_keywords": ["PhD", "research methodology", "caste seats"],
                "check_lead_capture": True,
                "description": "Should return clean course list, no PhD garbage, no lead form"
            },
            {
                "name": "BCA Fees Query",
                "query": "What are the BCA fees?",
                "expected_keywords": ["BCA", "fee", "₹"],
                "forbidden_keywords": ["BCom", "MBA", "placement", "recruiter", "marketing"],
                "check_lead_capture": True,
                "description": "Should return ONLY BCA fees, no other courses, no lead form"
            },
            {
                "name": "Scholarship Query",
                "query": "Tell me about scholarships",
                "expected_keywords": ["scholarship", "merit", "financial"],
                "forbidden_keywords": ["placement", "hostel"],
                "check_lead_capture": True,
                "description": "Should return scholarship info, no lead form"
            },
            {
                "name": "Hostel Query",
                "query": "What about hostel facilities?",
                "expected_keywords": ["hostel", "accommodation", "room"],
                "forbidden_keywords": ["placement", "admission", "fees"],
                "check_lead_capture": True,
                "description": "Should return hostel info, no lead form"
            },
            {
                "name": "Programs Query",
                "query": "Tell me about the programs",
                "expected_keywords": ["MBA", "BCA", "program"],
                "forbidden_keywords": ["PhD", "research"],
                "check_lead_capture": True,
                "description": "Should return program list, no PhD garbage, no lead form"
            },
        ]
        
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'=' * 80}")
            print(f"[TEST {i}] {test_case['name']}")
            print(f"Description: {test_case['description']}")
            print(f"Query: {test_case['query']}")
            print("=" * 80)
            
            # Send message
            if not send_message(driver, test_case["query"]):
                print("❌ FAILED: Could not send message")
                driver.save_screenshot(f"{SCREENSHOT_DIR}/test_{i:02d}_send_failed.png")
                results.append(False)
                continue
            
            # Get response
            response = get_last_bot_message(driver)
            driver.save_screenshot(f"{SCREENSHOT_DIR}/test_{i:02d}_{test_case['name'].replace(' ', '_')}.png")
            
            print(f"\n[RESPONSE]")
            print(f"{response[:300]}...")
            
            # Check for issues
            issues = []
            
            # Check 1: Lead capture hijacking
            if test_case.get("check_lead_capture"):
                if check_for_lead_capture(response):
                    issues.append("🚨 LEAD CAPTURE HIJACKING - Asking for email/phone instead of answering")
            
            # Check 2: Forbidden content (garbage/irrelevant)
            forbidden_found = check_for_garbage_content(response, test_case["forbidden_keywords"])
            if forbidden_found:
                issues.append(f"🚨 GARBAGE CONTENT - Found irrelevant keywords: {forbidden_found}")
            
            # Check 3: Expected content missing
            expected_missing = []
            response_lower = response.lower()
            for keyword in test_case["expected_keywords"]:
                if keyword.lower() not in response_lower:
                    expected_missing.append(keyword)
            
            if expected_missing:
                issues.append(f"⚠️  MISSING CONTENT - Expected keywords not found: {expected_missing}")
            
            # Report results
            if issues:
                print(f"\n❌ FAILED - {len(issues)} issue(s) found:")
                for issue in issues:
                    print(f"   {issue}")
                results.append(False)
            else:
                print(f"\n✅ PASSED - All checks passed")
                results.append(True)
        
        # Final summary
        print("\n" + "=" * 80)
        print("FINAL RESULTS")
        print("=" * 80)
        print(f"Tests Passed: {sum(results)}/{len(results)}")
        print(f"Tests Failed: {len(results) - sum(results)}/{len(results)}")
        
        if all(results):
            print("\n🎉 ALL TESTS PASSED - System is ready!")
        else:
            print("\n❌ SYSTEM NOT READY - Issues found:")
            for i, (test_case, passed) in enumerate(zip(test_cases, results), 1):
                status = "✅" if passed else "❌"
                print(f"   {status} Test {i}: {test_case['name']}")
        
        print(f"\nScreenshots saved to: {SCREENSHOT_DIR}/")
        print("=" * 80)
        
        return all(results)
        
    finally:
        # Keep browser open for inspection
        print("\n⏸️  Browser will stay open for 30 seconds for inspection...")
        time.sleep(30)
        driver.quit()

if __name__ == "__main__":
    success = run_test_suite()
    exit(0 if success else 1)
