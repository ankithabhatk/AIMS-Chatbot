from playwright.sync_api import sync_playwright
import time

URL = "http://localhost:3000"

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("\n🚀 Opening chatbot...")
        page.goto(URL)
        time.sleep(3)
        
        print("🤖 Clicking robot trigger...")
        page.locator(".floating-robot-trigger").click()
        time.sleep(2)
        
        # Inspect form HTML
        print("\n📋 Checking form selectors...")
        
        # Check for all input types
        name_input = page.locator("input[name='name']")
        print(f"name input count: {name_input.count()}")
        
        email_input = page.locator("input[name='email']")
        print(f"email input count: {email_input.count()}")
        
        mobile_input = page.locator("input[name='mobile']")
        print(f"mobile input count: {mobile_input.count()}")
        
        # Check for select
        course_select = page.locator("select[name='course']")
        print(f"select count: {course_select.count()}")
        
        # Check for any buttons
        submit_btn = page.locator("button[type='submit']")
        print(f"submit buttons: {submit_btn.count()}")
        
        # Print all buttons
        all_buttons = page.locator("button")
        print(f"all buttons: {all_buttons.count()}")
        for i in range(min(5, all_buttons.count())):
            btn_text = all_buttons.nth(i).inner_text()
            print(f"  Button {i}: {btn_text}")
        
        # Look at form container HTML
        form_html = page.locator("form")
        print(f"form elements: {form_html.count()}")
        
        # Get page HTML snippet
        print("\n📄 Page HTML (form area):")
        content = page.content()
        if "welcome-form" in content:
            start = content.find("welcome-form")
            print(content[start:start+800])
        
        browser.close()

if __name__ == "__main__":
    run_test()
