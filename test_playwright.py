import asyncio
from playwright.async_api import async_playwright
import os

PROOF_DIR = "/tmp/proof"
os.makedirs(PROOF_DIR, exist_ok=True)

async def run_tests():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Testing: mba fees")
        await page.goto("http://localhost:5001/professional.html", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        await page.fill("input#queryInput", "mba fees")
        await page.locator("button.send-btn").click()
        await page.wait_for_timeout(3000)
        await page.screenshot(path=f"{PROOF_DIR}/fees_response.png")

        print("Testing: mba admission process")
        await page.goto("http://localhost:5001/professional.html", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        await page.fill("input#queryInput", "mba admission process")
        await page.locator("button.send-btn").click()
        await page.wait_for_timeout(3000)
        await page.screenshot(path=f"{PROOF_DIR}/admission_response.png")

        print("Testing: mba placements")
        await page.goto("http://localhost:5001/professional.html", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        await page.fill("input#queryInput", "mba placements")
        await page.locator("button.send-btn").click()
        await page.wait_for_timeout(3000)
        await page.screenshot(path=f"{PROOF_DIR}/placements_response.png")

        await browser.close()
        print(f"Screenshots saved to {PROOF_DIR}")

if __name__ == "__main__":
    asyncio.run(run_tests())
