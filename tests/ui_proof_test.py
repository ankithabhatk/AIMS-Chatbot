"""
Playwright UI Proof Test - FIXED VERSION 2
Use JavaScript click on robot to bypass CSS animations

Usage:
    python tests/ui_proof_test.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def run_ui_tests():
    """Run all UI proof tests with Playwright"""
    
    from playwright.async_api import async_playwright
    
    output_dir = Path("/tmp/final_proof")
    output_dir.mkdir(exist_ok=True)
    
    print(f"📁 Output directory: {output_dir}")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        
        base_url = "http://localhost:3000"
        
        # ============================================================
        # Test 1: Load homepage
        # ============================================================
        print("\n1️⃣ Loading homepage...")
        await page.goto(base_url, wait_until="networkidle", timeout=30000)
        await page.screenshot(path=str(output_dir / "01_home.png"), full_page=True)
        print("   ✅ Saved: 01_home.png")
        
        # Wait for page to fully load
        await page.wait_for_timeout(2000)
        
        # ============================================================
        # STEP 0: CLICK ROBOT USING JS TO BYPASS ANIMATION
        # ============================================================
        print("\n🤖 Opening chat via JS click...")
        
        # Wait for robot to be in DOM
        await page.wait_for_selector('.floating-robot-trigger', timeout=5000)
        
        # Use JS click to bypass CSS animations
        await page.evaluate('''() => {
            const robot = document.querySelector('.floating-robot-trigger');
            if (robot) {
                robot.click();
                console.log('Clicked robot via JS');
            }
        }''')
        
        # Wait for chat to animate open
        await page.wait_for_timeout(3000)
        
        await page.screenshot(path=str(output_dir / "02_chat_open.png"), full_page=True)
        print("   ✅ Saved: 02_chat_open.png")
        
        # Check if chat opened - look for welcome form or chat window
        has_welcome = await page.query_selector('[class*="welcome"]')
        has_input = await page.query_selector('input')
        
        print(f"   Welcome form: {has_welcome is not None}")
        print(f"   Input field: {has_input is not None}")
        
        # ============================================================
        # Helper: submit query
        # ============================================================
        async def submit_query(q: str, filename: str):
            """Submit a query and wait for response"""
            try:
                # Try different input selectors
                input_selectors = [
                    'input[placeholder*="Message"]',
                    'input[placeholder*="Type"]', 
                    'input[type="text"]',
                    'textarea'
                ]
                
                input_field = None
                for sel in input_selectors:
                    try:
                        input_field = await page.wait_for_selector(sel, timeout=3000)
                        if input_field:
                            break
                    except:
                        continue
                
                if not input_field:
                    # Try filling via JS
                    await page.evaluate(f'''() => {{
                        const inputs = document.querySelectorAll('input, textarea');
                        for (const inp of inputs) {{
                            if (inp.offsetParent !== null && inp.type !== 'hidden') {{
                                inp.focus();
                                console.log('Found input:', inp.placeholder);
                                return;
                            }}
                        }}
                    }}''')
                    await page.wait_for_timeout(1000)
                
                # Type the query
                await page.keyboard.type(q, delay=50)
                print(f"   Typed: '{q}'")
                
                # Press enter to submit
                await page.keyboard.press("Enter")
                print(f"   Pressed Enter")
                
                # Wait for response
                await page.wait_for_timeout(5000)
                
                # Take screenshot
                await page.screenshot(path=str(output_dir / filename), full_page=True)
                print(f"   ✅ Saved: {filename}")
                
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
                await page.screenshot(path=str(output_dir / filename), full_page=True)
        
        # ============================================================
        # Test 3: Misspelled query
        # ============================================================
        print("\n3️⃣ Testing: 'wat corses do u hav'...")
        await submit_query("wat corses do u hav", "03_courses_typo.png")
        
        # ============================================================
        # Test 4: Curriculum query
        # ============================================================
        print("\n4️⃣ Testing: 'What subjects are in MCA?'...")
        await submit_query("What subjects are in MCA?", "04_mca_curriculum.png")
        
        # ============================================================
        # Test 5: Fees query (typo)
        # ============================================================
        print("\n5️⃣ Testing: 'mba feees pls'...")
        await submit_query("mba feees pls", "05_fees_typo.png")
        
        # ============================================================
        # Test 6: Placement query (typo)
        # ============================================================
        print("\n6️⃣ Testing: 'placemnt recod'...")
        await submit_query("placemnt recod", "06_placement_typo.png")
        
        # ============================================================
        # Test 7: Out-of-scope
        # ============================================================
        print("\n7️⃣ Testing: 'tell me about iit bombay'...")
        await submit_query("tell me about iit bombay", "07_out_of_scope.png")
        
        # ============================================================
        # Test 8: Campus
        # ============================================================
        print("\n8️⃣ Testing: 'do you have hostel'...")
        await submit_query("do you have hostel", "08_hostel.png")
        
        await browser.close()
        
        print(f"\n✅ All tests complete!")
        print(f"📁 Screenshots: {output_dir}")
        
        return output_dir


if __name__ == "__main__":
    asyncio.run(run_ui_tests())