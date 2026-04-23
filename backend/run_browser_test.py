import asyncio
from playwright.async_api import async_playwright

artifacts_dir = "/Users/maneeth/.gemini/antigravity/brain/d9544ace-b789-4799-b4cc-a3551e28b15c/artifacts"

async def run_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Capture console and network
        logs = []
        page.on("console", lambda msg: logs.append(f"CONSOLE: {msg.type} {msg.text}"))
        page.on("requestfailed", lambda request: logs.append(f"NETWORK ERROR: {request.url} - {request.failure}"))
        page.on("response", lambda response: logs.append(f"NETWORK: {response.url} - {response.status}") if not response.ok else None)

        async def type_and_send(text, wait_ms=2000):
            print(f"Sending: {text}")
            await page.get_by_placeholder("Type your inquiry here...").fill(text)
            await page.get_by_placeholder("Type your inquiry here...").press("Enter")
            await page.wait_for_timeout(wait_ms)

        print("1. Loading page...")
        await page.goto("http://localhost:3000")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=f"{artifacts_dir}/home_loaded.png")

        print("1.5 Opening chat...")
        await page.locator('.floating-robot-trigger').click()
        await page.wait_for_timeout(1000)

        print("2. Sending 'hello'")
        await type_and_send("hello", 3000)
        await page.screenshot(path=f"{artifacts_dir}/greeting.png")

        print("3. Sending 'mba fees'")
        await type_and_send("mba fees", 3000)
        await page.screenshot(path=f"{artifacts_dir}/fees_response.png")

        print("4. Sending 'mba admission process' and 'how to apply for mba'")
        await type_and_send("mba admission process", 3000)
        await type_and_send("how to apply for mba", 3000)
        await page.screenshot(path=f"{artifacts_dir}/next_step.png")

        print("5. Trigger capture with Name")
        await type_and_send("John Doe", 3000)
        await page.screenshot(path=f"{artifacts_dir}/capture_name.png")

        print("6. Send Phone and Email")
        await type_and_send("9876543210", 3000)
        await type_and_send("john@test.com", 3000)
        await page.screenshot(path=f"{artifacts_dir}/capture_complete.png")

        print("\n--- BROWSER LOGS ---")
        for log in logs:
            print(log)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())
