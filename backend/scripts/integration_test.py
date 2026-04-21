#!/usr/bin/env python3
"""
Integration Test: Frontend ↔ Backend
Tests the complete chatbot flow through the browser
"""

import asyncio
import sys
import json
import time
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright not installed. Installing...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    from playwright.async_api import async_playwright


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


FRONTEND_URL = "http://localhost:8001/index.html"
BACKEND_URL = "http://localhost:8000"

TEST_QUERIES = [
    "What programs does AIMS offer?",
    "What is the fee structure for MBA?",
    "Does AIMS have placement assistance?",
]


async def test_frontend_backend_integration():
    """Test complete chatbot flow through browser"""

    print(f"\n{Colors.HEADER}")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "INTEGRATION TEST: Frontend ↔ Backend" + " "*21 + "║")
    print("╚" + "="*78 + "╝")
    print(f"{Colors.ENDC}\n")

    async with async_playwright() as p:
        print(f"{Colors.OKCYAN}🌐 Starting browser...{Colors.ENDC}")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Navigate to frontend
            print(f"\n{Colors.OKCYAN}📄 Loading frontend...{Colors.ENDC}")
            print(f"   URL: {FRONTEND_URL}")

            await page.goto(FRONTEND_URL, wait_until="domcontentloaded", timeout=10000)
            await page.wait_for_load_state("networkidle")

            print(f"{Colors.OKGREEN}✅ Frontend loaded successfully{Colors.ENDC}")

            # Test queries
            results = []

            for i, query in enumerate(TEST_QUERIES, 1):
                print(f"\n{Colors.OKCYAN}🧪 Test {i}/{len(TEST_QUERIES)}{Colors.ENDC}")
                print(f"   Query: {Colors.BOLD}{query}{Colors.ENDC}")

                # Fill in query
                input_field = page.locator("#queryInput")
                await input_field.fill(query)

                # Click send
                send_btn = page.locator("#sendBtn")
                await send_btn.click()

                # Wait for response (max 10s)
                start_time = time.time()
                response_found = False

                for attempt in range(20):
                    # Check if we got a bot response by counting messages
                    messages = await page.locator(".message.bot").count()

                    if messages > i:  # We have a new bot message
                        response_found = True
                        elapsed = time.time() - start_time
                        print(f"   {Colors.OKGREEN}✅ Response received in {elapsed:.2f}s{Colors.ENDC}")

                        # Get the answer text
                        bot_messages = page.locator(".message.bot")
                        last_message = bot_messages.nth(messages - 1)
                        answer_text = await last_message.locator(".message-content").text_content()

                        print(f"   Answer: {answer_text[:80]}...")

                        # Check for confidence
                        confidence_element = last_message.locator(".confidence")
                        confidence_found = False

                        try:
                            confidence_text = await confidence_element.text_content(timeout=1000)
                            if confidence_text:
                                confidence_found = True
                                print(f"   {Colors.OKGREEN}{confidence_text}{Colors.ENDC}")
                        except:
                            pass

                        results.append({
                            "query": query,
                            "success": True,
                            "response_time": elapsed,
                            "confidence_visible": confidence_found,
                        })

                        break

                    await asyncio.sleep(0.5)

                if not response_found:
                    elapsed = time.time() - start_time
                    print(f"   {Colors.FAIL}❌ No response after {elapsed:.1f}s{Colors.ENDC}")

                    results.append({
                        "query": query,
                        "success": False,
                        "response_time": elapsed,
                    })

            # Take final screenshot
            print(f"\n{Colors.OKCYAN}📸 Taking screenshot...{Colors.ENDC}")
            screenshot_path = "/tmp/integration_test_screenshot.png"
            await page.screenshot(path=screenshot_path)
            print(f"   Saved: {screenshot_path}")

            # Print results
            print_results(results)

        except Exception as e:
            print(f"\n{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()


def print_results(results):
    """Print test results"""

    successful = sum(1 for r in results if r["success"])
    total = len(results)

    print(f"\n{Colors.HEADER}")
    print("=" * 80)
    print("INTEGRATION TEST RESULTS")
    print("=" * 80)
    print(f"{Colors.ENDC}\n")

    print(f"{Colors.BOLD}📊 Summary:{Colors.ENDC}")
    print(f"   Total tests: {total}")
    print(f"   Successful: {Colors.OKGREEN}{successful}/{total}{Colors.ENDC}")
    print(f"   Success rate: {Colors.BOLD}{(successful/total*100):.0f}%{Colors.ENDC}\n")

    print(f"{Colors.BOLD}📋 Details:{Colors.ENDC}")
    for result in results:
        status = f"{Colors.OKGREEN}✅{Colors.ENDC}" if result["success"] else f"{Colors.FAIL}❌{Colors.ENDC}"
        print(f"\n   {status} {result['query']}")
        print(f"      Time: {result['response_time']:.2f}s")
        if result["success"]:
            print(f"      Confidence: {'📊 Visible' if result.get('confidence_visible') else '⚠️  Not visible'}")

    print(f"\n{Colors.HEADER}")
    print("=" * 80)
    print(f"{Colors.ENDC}\n")

    # Overall assessment
    if successful == total:
        print(f"{Colors.OKGREEN}✅ INTEGRATION SUCCESSFUL!{Colors.ENDC}")
        print("\nFrontend ↔ Backend connection is working perfectly.")
        print("The chatbot UI can communicate with the API.")
    else:
        print(f"{Colors.WARNING}⚠️  PARTIAL SUCCESS{Colors.ENDC}")
        print(f"   {successful}/{total} queries responded successfully.")


async def main():
    await test_frontend_backend_integration()


if __name__ == "__main__":
    asyncio.run(main())
