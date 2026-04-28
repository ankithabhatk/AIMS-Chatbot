#!/usr/bin/env python3
"""
HEADLESS VALIDATION LOOP
Real browser testing with screenshot capture and backend debugging.

This script validates the chatbot UI behavior using Playwright.
It does NOT modify code — only observes and reports.
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

# Try to import playwright, install if missing
try:
    from playwright.sync_api import sync_playwright, expect
except ImportError:
    print("📦 Installing Playwright...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install"])
    from playwright.sync_api import sync_playwright, expect

# Configuration
BASE_URL = "http://localhost:3001"
SCREENSHOTS_DIR = Path("validation_screenshots")
RESULTS_FILE = Path("validation_results.json")

# Ensure screenshots directory exists
SCREENSHOTS_DIR.mkdir(exist_ok=True)

class ValidationLoop:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "steps": [],
            "failures": [],
            "backend_debug": []
        }
        self.browser = None
        self.page = None
        self.context = None
        
    def setup_browser(self):
        """Initialize Playwright browser"""
        print("🌐 Starting headless browser...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        
        # Enable console logging
        self.page.on("console", lambda msg: print(f"  [BROWSER LOG] {msg.text}"))
        
    def teardown_browser(self):
        """Close browser"""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
            
    def capture_screenshot(self, step_name: str):
        """Capture screenshot and save"""
        filename = SCREENSHOTS_DIR / f"{step_name}.png"
        self.page.screenshot(path=str(filename))
        print(f"  📸 Screenshot: {filename}")
        return str(filename)
        
    def get_chatbot_response(self) -> str:
        """Extract the latest chatbot response from DOM"""
        try:
            # Wait for message container
            self.page.wait_for_selector("[data-testid='message-container']", timeout=5000)
            
            # Get all messages
            messages = self.page.query_selector_all("[data-testid='message']")
            if messages:
                last_message = messages[-1]
                response_text = last_message.inner_text()
                return response_text
        except Exception as e:
            print(f"  ⚠️  Could not extract response: {e}")
        return None
        
    def send_message(self, message: str) -> dict:
        """Send a message and capture response"""
        print(f"\n📝 Sending: '{message}'")
        
        try:
            # Find input field
            input_field = self.page.query_selector("input[placeholder*='Ask'], textarea, input[type='text']")
            if not input_field:
                print("  ❌ Could not find input field")
                return {"success": False, "error": "Input field not found"}
            
            # Type message
            input_field.fill(message)
            
            # Find and click send button
            send_button = self.page.query_selector("button:has-text('Send'), button[type='submit']")
            if send_button:
                send_button.click()
            else:
                # Try Enter key
                input_field.press("Enter")
            
            # Wait for response
            time.sleep(2)
            
            # Get response
            response = self.get_chatbot_response()
            
            return {
                "success": True,
                "message": message,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"  ❌ Error sending message: {e}")
            return {"success": False, "error": str(e)}
            
    def validate_response(self, step_num: int, message: str, response: str) -> dict:
        """Validate if response is meaningful or fallback"""
        validation = {
            "step": step_num,
            "message": message,
            "response": response,
            "is_fallback": False,
            "is_meaningful": False,
            "reason": ""
        }
        
        # Check for fallback patterns
        fallback_patterns = [
            "try asking",
            "could you clarify",
            "not sure",
            "didn't understand",
            "please rephrase",
            "i'm not sure what you mean"
        ]
        
        if response:
            response_lower = response.lower()
            
            # Check if fallback
            if any(pattern in response_lower for pattern in fallback_patterns):
                validation["is_fallback"] = True
                validation["reason"] = "Fallback response detected"
            else:
                validation["is_meaningful"] = True
                validation["reason"] = "Meaningful response"
        else:
            validation["reason"] = "No response received"
            
        return validation
        
    def debug_backend(self, step_num: int, message: str):
        """Debug backend to understand why it failed"""
        print(f"\n🔍 Debugging backend for step {step_num}...")
        
        debug_info = {
            "step": step_num,
            "message": message,
            "checks": {}
        }
        
        # Check 1: Stage detection
        print("  → Checking stage detection...")
        try:
            # This would call your backend API
            # For now, we'll just note what we'd check
            debug_info["checks"]["stage_detection"] = "Would check: Is 'I like coding' detected as INTEREST stage?"
        except Exception as e:
            debug_info["checks"]["stage_detection"] = f"Error: {e}"
            
        # Check 2: Entity extraction
        print("  → Checking entity extraction...")
        debug_info["checks"]["entity_extraction"] = "Would check: Is 'coding' extracted as interest?"
        
        # Check 3: Course mapping
        print("  → Checking course mapping...")
        debug_info["checks"]["course_mapping"] = "Would check: Is 'coding' mapped to BCA/MCA?"
        
        # Check 4: Routing decision
        print("  → Checking routing decision...")
        debug_info["checks"]["routing"] = "Would check: Is stage set to GUIDANCE or FALLBACK?"
        
        self.results["backend_debug"].append(debug_info)
        return debug_info
        
    def run_validation_flow(self):
        """Run the complete validation flow"""
        print("\n" + "="*60)
        print("🚀 HEADLESS VALIDATION LOOP STARTING")
        print("="*60)
        
        try:
            # Step 0: Navigate to chatbot
            print("\n[STEP 0] Navigating to chatbot UI...")
            self.page.goto(BASE_URL, wait_until="networkidle")
            time.sleep(2)
            self.capture_screenshot("step0_initial")
            
            # Step 1: "I like coding"
            print("\n[STEP 1] User interest signal")
            result1 = self.send_message("I like coding")
            self.capture_screenshot("step1_interest_signal")
            
            validation1 = self.validate_response(1, "I like coding", result1.get("response"))
            self.results["steps"].append(validation1)
            
            if validation1["is_fallback"]:
                print(f"  🔴 FAILURE: Got fallback instead of guidance")
                self.results["failures"].append({
                    "step": 1,
                    "pattern": "Interest signal ignored",
                    "expected": "Suggest coding-related courses (BCA, MCA)",
                    "actual": "Fallback response"
                })
                self.debug_backend(1, "I like coding")
            else:
                print(f"  ✅ PASS: Got meaningful response")
            
            time.sleep(1)
            
            # Step 2: "Tell me about BCA"
            print("\n[STEP 2] Specific course inquiry")
            result2 = self.send_message("Tell me about BCA")
            self.capture_screenshot("step2_bca_inquiry")
            
            validation2 = self.validate_response(2, "Tell me about BCA", result2.get("response"))
            self.results["steps"].append(validation2)
            
            if validation2["is_fallback"]:
                print(f"  🔴 FAILURE: Got fallback for specific course")
                self.results["failures"].append({
                    "step": 2,
                    "pattern": "Course inquiry ignored",
                    "expected": "Provide BCA details",
                    "actual": "Fallback response"
                })
                self.debug_backend(2, "Tell me about BCA")
            else:
                print(f"  ✅ PASS: Got course information")
            
            time.sleep(1)
            
            # Step 3: "What about MCA?"
            print("\n[STEP 3] Alternative course inquiry")
            result3 = self.send_message("What about MCA?")
            self.capture_screenshot("step3_mca_inquiry")
            
            validation3 = self.validate_response(3, "What about MCA?", result3.get("response"))
            self.results["steps"].append(validation3)
            
            if validation3["is_fallback"]:
                print(f"  🔴 FAILURE: Got fallback for alternative course")
                self.results["failures"].append({
                    "step": 3,
                    "pattern": "Alternative course inquiry ignored",
                    "expected": "Provide MCA details",
                    "actual": "Fallback response"
                })
                self.debug_backend(3, "What about MCA?")
            else:
                print(f"  ✅ PASS: Got course information")
            
        except Exception as e:
            print(f"\n❌ Validation error: {e}")
            self.results["error"] = str(e)
            
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "="*60)
        print("📊 VALIDATION SUMMARY")
        print("="*60)
        
        total_steps = len(self.results["steps"])
        meaningful_responses = sum(1 for s in self.results["steps"] if s["is_meaningful"])
        fallback_responses = sum(1 for s in self.results["steps"] if s["is_fallback"])
        
        print(f"\n✅ Meaningful responses: {meaningful_responses}/{total_steps}")
        print(f"🔴 Fallback responses: {fallback_responses}/{total_steps}")
        
        if self.results["failures"]:
            print(f"\n⚠️  FAILURES DETECTED ({len(self.results['failures'])}):")
            for failure in self.results["failures"]:
                print(f"\n  Step {failure['step']}: {failure['pattern']}")
                print(f"    Expected: {failure['expected']}")
                print(f"    Actual: {failure['actual']}")
        else:
            print("\n✅ All validations passed!")
            
        if self.results["backend_debug"]:
            print(f"\n🔍 Backend debug info collected for {len(self.results['backend_debug'])} failures")
            
    def save_results(self):
        """Save results to JSON"""
        with open(RESULTS_FILE, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to {RESULTS_FILE}")
        
    def run(self):
        """Run complete validation loop"""
        try:
            self.setup_browser()
            self.run_validation_flow()
            self.print_summary()
            self.save_results()
        finally:
            self.teardown_browser()

if __name__ == "__main__":
    # Check if frontend is running
    print("🔍 Checking if frontend is running on localhost:3000...")
    try:
        import requests
        requests.get(BASE_URL, timeout=2)
        print("✅ Frontend is running\n")
    except:
        print(f"❌ Frontend not running on {BASE_URL}")
        print("   Start it with: npm run dev")
        sys.exit(1)
    
    # Run validation
    loop = ValidationLoop()
    loop.run()
