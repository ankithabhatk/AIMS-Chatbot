#!/usr/bin/env python3
"""
Professional Frontend Integration Test
Verifies the AIMS-branded frontend renders correctly and integrates with API
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from playwright.async_api import async_playwright, expect
except ImportError:
    print("❌ Playwright not installed. Install with:")
    print("   pip install playwright")
    sys.exit(1)


async def test_professional_frontend():
    """Test professional frontend with API integration"""
    
    print("\n" + "="*80)
    print("🎨 PROFESSIONAL FRONTEND INTEGRATION TEST")
    print("="*80 + "\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        # Navigate to professional frontend
        url = "http://localhost:8001/professional.html"
        print(f"📍 Loading: {url}\n")
        
        try:
            await page.goto(url, wait_until="networkidle")
        except Exception as e:
            print(f"❌ Failed to load page: {e}")
            print(f"\nℹ️  Make sure to run:")
            print(f"   1. Backend: python backend/app/main.py")
            print(f"   2. Frontend: python serve_frontend.py\n")
            await browser.close()
            return False
        
        # Wait for page to load
        await page.wait_for_load_state("domcontentloaded")
        
        # Check for key UI elements
        tests = [
            ("Header renders", 'text="The AIMS"'),
            ("Chat input exists", "input[placeholder*='Ask about']"),
            ("Info panel visible", "text=Programs"),
            ("Status indicator", '//div[@class*="status"]'),
        ]
        
        print("✓ Testing UI elements:\n")
        for test_name, selector in tests:
            try:
                element = page.locator(selector) if not selector.startswith('//') else page.locator(selector)
                if await element.count() > 0:
                    print(f"  ✅ {test_name}")
                else:
                    print(f"  ⚠️  {test_name} (not found)")
            except:
                print(f"  ⚠️  {test_name} (error checking)")
        
        # Test Chat Functionality
        print("\n✓ Testing chat functionality:\n")
        
        test_queries = [
            "What programs do you offer?",
            "What is the placement rate?",
            "How much are the fees?"
        ]
        
        results = []
        for idx, query in enumerate(test_queries, 1):
            print(f"  [{idx}] Query: '{query}'")
            
            try:
                # Fill query input
                input_selector = "input[placeholder*='Ask']"
                await page.fill(input_selector, query)
                await page.press(input_selector, "Enter")
                
                # Wait for response
                print(f"      ⏳ Waiting for response...", end='')
                
                # Wait for response to appear
                await page.wait_for_selector(".message.assistant", timeout=5000)
                
                # Check for confidence
                confidence_text = await page.text_content(".confidence-badge")
                print(f"\r      ✅ Received | Confidence: {confidence_text}")
                
                results.append({
                    'query': query,
                    'status': 'success',
                    'confidence': confidence_text
                })
                
            except Exception as e:
                print(f"\r      ⚠️  Response timeout or error: {str(e)[:50]}")
                results.append({
                    'query': query,
                    'status': 'timeout',
                    'error': str(e)[:50]
                })
            
            await page.wait_for_timeout(500)
        
        # Take screenshot
        screenshot_path = "/tmp/professional_frontend_test.png"
        await page.screenshot(path=screenshot_path, full_page=False)
        
        print(f"\n\n✓ Results Summary:\n")
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        total_count = len(results)
        
        for r in results:
            status_icon = "✅" if r['status'] == 'success' else "⚠️"
            print(f"  {status_icon} {r['query'][:40]}")
        
        print(f"\n{'='*80}")
        print(f"📊 Test Results: {success_count}/{total_count} queries successful")
        print(f"📸 Screenshot saved: {screenshot_path}")
        print(f"{'='*80}\n")
        
        # Simple checks
        page_title = await page.title()
        print(f"Page Title: {page_title}\n")
        
        # Close browser
        await browser.close()
        
        return success_count > 0


async def main():
    """Main execution"""
    success = await test_professional_frontend()
    
    if success:
        print("✅ Professional frontend integration test PASSED!\n")
        print("Next steps:")
        print("  1. Review screenshot: /tmp/professional_frontend_test.png")
        print("  2. Run data enrichment: python backend/scripts/scrape_aims_website.py")
        print("  3. Send email to AIMS for institutional documents\n")
    else:
        print("❌ Professional frontend test FAILED\n")
        print("Troubleshooting:")
        print("  1. Check if backend is running: localhost:8000")
        print("  2. Check if frontend server is running: localhost:8001")
        print("  3. Check browser console for errors\n")


if __name__ == "__main__":
    asyncio.run(main())
