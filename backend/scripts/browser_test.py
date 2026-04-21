#!/usr/bin/env python3
"""
Agentic Browser Test - Chatbot Verification
Tests the chatbot by simulating a human user with Playwright
"""

import asyncio
import subprocess
import time
import os
import sys
import json
import uuid
import requests
from pathlib import Path
from typing import Optional

# Try to import Playwright
try:
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    print("❌ Playwright not installed. Installing...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "playwright"],
        check=True,
    )
    from playwright.async_api import async_playwright, Page, Browser


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

API_BASE_URL = "http://localhost:8000"
HEALTH_CHECK_URL = f"{API_BASE_URL}/api/v1/health"
CHAT_ENDPOINT = f"{API_BASE_URL}/api/v1/chat"
STATS_ENDPOINT = f"{API_BASE_URL}/api/v1/stats"

# Test queries simulating real student questions
TEST_QUERIES = [
    "What programs does AIMS offer?",
    "What is the fee structure for MBA?",
    "Does AIMS have placement assistance?",
    "What is the admission process?",
    "Does AIMS have campus facilities like hostel or gym?",
]

# Color codes for terminal output
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


# ============================================================================
# HEALTH & READINESS CHECKS
# ============================================================================

def check_api_health() -> bool:
    """
    Check if API is running and healthy
    """
    print(f"\n{Colors.OKCYAN}🔍 Checking API Health...{Colors.ENDC}")
    
    try:
        response = requests.get(HEALTH_CHECK_URL, timeout=5)
        if response.status_code == 200:
            print(f"{Colors.OKGREEN}✅ API is healthy{Colors.ENDC}")
            return True
        else:
            print(
                f"{Colors.FAIL}❌ API returned status {response.status_code}{Colors.ENDC}"
            )
            return False
    except requests.exceptions.ConnectionError:
        print(
            f"{Colors.FAIL}❌ Cannot connect to API at {API_BASE_URL}{Colors.ENDC}"
        )
        print(f"   Make sure the API is running: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"{Colors.FAIL}❌ Health check error: {e}{Colors.ENDC}")
        return False


def get_api_stats() -> Optional[dict]:
    """
    Get API statistics
    """
    try:
        response = requests.get(STATS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"{Colors.WARNING}⚠️  Could not fetch stats: {e}{Colors.ENDC}")
    return None


# ============================================================================
# API DIRECT TESTING (No Browser)
# ============================================================================

def test_chat_api() -> dict:
    """
    Test the chat endpoint directly (simulates browser POST request)
    
    Returns:
        Result dict with success status and metrics
    """
    print(f"\n{Colors.OKCYAN}🧪 Testing Chat API (Direct)...{Colors.ENDC}")
    
    results = {
        "total_queries": len(TEST_QUERIES),
        "successful_responses": 0,
        "with_confidence": 0,
        "average_response_time": 0,
        "queries": [],
    }
    
    response_times = []
    session_id = str(uuid.uuid4())
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n   Query {i}/{len(TEST_QUERIES)}: {Colors.BOLD}{query}{Colors.ENDC}")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                CHAT_ENDPOINT,
                json={"query": query, "session_id": session_id},
                timeout=10,
            )
            
            elapsed = time.time() - start_time
            response_times.append(elapsed)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract response details
                answer = data.get("answer", "")
                confidence = data.get("confidence", 0)  # Field name is 'confidence'
                sources = data.get("sources", [])
                is_fallback = data.get("fallback", False)  # Use fallback field from API
                
                results["successful_responses"] += 1
                
                if confidence:
                    results["with_confidence"] += 1
                
                status = (
                    f"{Colors.WARNING}⚠️  FALLBACK{Colors.ENDC}"
                    if is_fallback
                    else f"{Colors.OKGREEN}✅ ANSWERED{Colors.ENDC}"
                )
                
                print(f"      Status: {status}")
                print(f"      Confidence: {Colors.BOLD}{confidence:.1%}{Colors.ENDC}")
                print(f"      Time: {elapsed:.2f}s")
                print(f"      Sources: {len(sources)} document(s)")
                
                # Store query result
                results["queries"].append({
                    "query": query,
                    "answered_directly": not is_fallback,
                    "confidence": confidence,
                    "time_seconds": elapsed,
                    "sources_used": len(sources),
                    "answer_preview": answer[:100] + "..." if len(answer) > 100 else answer,
                })
                
            else:
                print(
                    f"      {Colors.FAIL}❌ Error: HTTP {response.status_code}{Colors.ENDC}"
                )
                print(f"         Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"      {Colors.FAIL}❌ Timeout (>10s){Colors.ENDC}")
        except Exception as e:
            print(f"      {Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
    
    # Calculate metrics
    if response_times:
        results["average_response_time"] = sum(response_times) / len(response_times)
    
    return results


# ============================================================================
# BROWSER VISUAL TESTING (Optional)
# ============================================================================

async def create_test_html():
    """Create a simple HTML test page for browser interaction"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AIMS Chatbot Test</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; }
            .test-container { border: 1px solid #ccc; padding: 20px; border-radius: 8px; }
            .input-group { margin: 20px 0; }
            input { width: 100%; padding: 10px; font-size: 14px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; border-radius: 4px; }
            .response { margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 4px; min-height: 100px; }
            .error { color: red; }
            .success { color: green; }
            .loading { color: orange; }
        </style>
    </head>
    <body>
        <h1>AIMS Chatbot Test</h1>
        <div class="test-container">
            <h2>Ask a Question</h2>
            <div class="input-group">
                <input type="text" id="queryInput" placeholder="Ask about AIMS..." 
                       value="What programs does AIMS offer?">
            </div>
            <button onclick="sendQuery()">Send Query</button>
            <div id="responseContainer" class="response" style="display:none;">
                <div id="responseContent"></div>
            </div>
        </div>

        <script>
            const API_URL = 'http://localhost:8000/api/v1/chat';
            let sessionId = Math.random().toString(36);

            async function sendQuery() {
                const query = document.getElementById('queryInput').value;
                const container = document.getElementById('responseContainer');
                const content = document.getElementById('responseContent');

                if (!query.trim()) {
                    alert('Please enter a query');
                    return;
                }

                content.innerHTML = '<span class="loading">Loading...</span>';
                container.style.display = 'block';

                try {
                    const response = await fetch(API_URL, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            query: query,
                            session_id: sessionId
                        })
                    });

                    if (response.ok) {
                        const data = await response.json();
                        let html = '';
                        html += '<strong>Question:</strong> ' + query + '<br><br>';
                        html += '<strong class="success">Answer:</strong><br>';
                        html += data.answer + '<br><br>';
                        html += '<strong>Confidence:</strong> ' + (data.confidence_score * 100).toFixed(1) + '%<br>';
                        html += '<strong>Response Time:</strong> ' + (data.response_time_ms || 0) + 'ms';
                        content.innerHTML = html;
                    } else {
                        content.innerHTML = '<span class="error">Error: ' + response.statusText + '</span>';
                    }
                } catch (error) {
                    content.innerHTML = '<span class="error">Error: ' + error.message + '</span>';
                }
            }

            // Auto-send on Enter key
            document.getElementById('queryInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendQuery();
            });
        </script>
    </body>
    </html>
    """
    return html_content


async def test_with_browser():
    """
    Test the chatbot using Playwright browser automation
    """
    print(f"\n{Colors.OKCYAN}🌐 Testing with Browser (Playwright)...{Colors.ENDC}")
    
    # Create temporary HTML file
    test_html_path = "/tmp/chatbot_test.html"
    html_content = await create_test_html()
    with open(test_html_path, "w") as f:
        f.write(html_content)
    
    print(f"   Created test page: {test_html_path}")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to test page
            file_url = f"file://{test_html_path}"
            print(f"   Opening test page in browser...")
            await page.goto(file_url)
            
            # Wait for page to load
            await page.wait_for_load_state("domcontentloaded")
            
            # Fill in first test query
            query_input = page.locator("#queryInput")
            await query_input.clear()
            await query_input.fill(TEST_QUERIES[0])
            
            # Click send button
            print(f"   Testing first query: {TEST_QUERIES[0]}")
            send_button = page.locator("button")
            await send_button.click()
            
            # Wait for response
            response_container = page.locator("#responseContainer")
            await response_container.wait_for(timeout=15000)
            
            # Get response content
            response_content = await response_container.text_content()
            
            print(f"{Colors.OKGREEN}✅ Browser test successful!{Colors.ENDC}")
            print(f"   Response preview: {response_content[:200]}...")
            
            # Take screenshot for proof
            screenshot_path = "/tmp/chatbot_test_screenshot.png"
            await page.screenshot(path=screenshot_path)
            print(f"   Screenshot saved: {screenshot_path}")
            
            return True
            
        except Exception as e:
            print(f"{Colors.FAIL}❌ Browser test failed: {e}{Colors.ENDC}")
            return False
        finally:
            await browser.close()


# ============================================================================
# RESULTS & REPORTING
# ============================================================================

def print_test_results(api_results: dict, stats: Optional[dict] = None):
    """
    Print formatted test results
    """
    print(f"\n{Colors.HEADER}{'='*80}")
    print(f"TEST RESULTS SUMMARY")
    print(f"{'='*80}{Colors.ENDC}\n")
    
    # API Stats
    if stats:
        print(f"{Colors.BOLD}📊 Index Status:{Colors.ENDC}")
        print(f"   Documents in index: {stats.get('search_stats', {}).get('total_documents', 'N/A')}")
        print(f"   Model: {stats.get('search_stats', {}).get('embedding_model', 'N/A')}")
        print()
    
    # Query Results
    print(f"{Colors.BOLD}🧪 Query Results:{Colors.ENDC}")
    print(f"   Total queries: {api_results['total_queries']}")
    print(f"   Successful responses: {api_results['successful_responses']}/{api_results['total_queries']}")
    print(
        f"   Success rate: {Colors.BOLD}{(api_results['successful_responses'] / api_results['total_queries'] * 100):.1f}%{Colors.ENDC}"
    )
    print(f"   Average response time: {api_results['average_response_time']:.2f}s")
    print()
    
    # Per-query breakdown
    print(f"{Colors.BOLD}📋 Per-Query Breakdown:{Colors.ENDC}")
    for query_result in api_results["queries"]:
        status = (
            f"{Colors.OKGREEN}✅ Direct{Colors.ENDC}"
            if query_result["answered_directly"]
            else f"{Colors.WARNING}⚠️  Fallback{Colors.ENDC}"
        )
        print(f"   {status} | Confidence: {query_result['confidence']:.1%} | Time: {query_result['time_seconds']:.2f}s")
        print(f"      Q: {query_result['query']}")
        print(f"      A: {query_result['answer_preview']}")
        print()
    
    # Overall assessment
    print(f"{Colors.BOLD}🎯 Overall Assessment:{Colors.ENDC}")
    success_rate = (
        api_results["successful_responses"] / api_results["total_queries"] * 100
    )
    
    if success_rate >= 70:
        print(f"   {Colors.OKGREEN}✅ EXCELLENT - System is production-ready{Colors.ENDC}")
    elif success_rate >= 50:
        print(f"   {Colors.OKGREEN}✅ GOOD - System is working, ready for data enrichment{Colors.ENDC}")
    elif success_rate >= 30:
        print(f"   {Colors.WARNING}⚠️  FAIR - System is working, but needs more data{Colors.ENDC}")
    else:
        print(f"   {Colors.FAIL}❌ NEEDS WORK - System needs significant improvements{Colors.ENDC}")
    
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}\n")


# ============================================================================
# MAIN TEST ORCHESTRATION
# ============================================================================

async def main():
    """
    Main test orchestration
    """
    print(f"\n{Colors.HEADER}")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "CHATBOT AGENTIC BROWSER TEST" + " "*31 + "║")
    print("╚" + "="*78 + "╝")
    print(f"{Colors.ENDC}\n")
    
    # Step 1: Health check
    if not check_api_health():
        print(f"\n{Colors.FAIL}❌ API is not running. Exiting.{Colors.ENDC}")
        sys.exit(1)
    
    # Step 2: Get API stats
    stats = get_api_stats()
    
    # Step 3: Test chat API directly
    api_results = test_chat_api()
    
    # Step 4: Optional browser test (if Playwright works)
    browser_success = False
    try:
        browser_success = await test_with_browser()
    except Exception as e:
        print(
            f"\n{Colors.WARNING}⚠️  Browser testing skipped (Playwright may need setup){Colors.ENDC}"
        )
        print(f"   To enable: pip install playwright && playwright install")
    
    # Step 5: Print results
    print_test_results(api_results, stats)
    
    # Step 6: Save results to file
    results_file = "/tmp/chatbot_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "api_test_results": api_results,
            "api_stats": stats,
            "browser_test_success": browser_success,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, f, indent=2)
    print(f"📁 Full results saved to: {results_file}\n")


if __name__ == "__main__":
    asyncio.run(main())
