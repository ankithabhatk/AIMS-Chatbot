import asyncio
import json
import time
from pathlib import Path

from playwright.async_api import async_playwright


BASE_URL = "http://127.0.0.1:3000"
RESULTS_PATH = Path("/tmp/e2e_frontend_login_chat_results.json")

QUESTIONS = [
    {
        "query": "What programs does AIMS offer?",
        "expected": ["mba", "bba", "mca", "bca"],
    },
    {
        "query": "What is the fee structure for MBA?",
        "expected": ["mba", "₹", "per year", "fees"],
    },
    {
        "query": "What is the fee structure for MCA?",
        "expected": ["mca", "₹", "per year", "fees"],
    },
    {
        "query": "What is the admission process?",
        "expected": ["apply", "application", "interview", "documents"],
    },
    {
        "query": "What is the placement record?",
        "expected": ["placement", "recruit", "package", "84%"],
    },
    {
        "query": "What hostel facilities are available?",
        "expected": ["hostel", "wi-fi", "security", "rooms"],
    },
    {
        "query": "Are scholarships available?",
        "expected": ["scholarship", "merit", "financial", "available"],
    },
    {
        "query": "What MBA specializations are available?",
        "expected": ["finance", "marketing", "hr", "analytics"],
    },
    {
        "query": "Where is the campus located?",
        "expected": ["bangalore", "karnataka", "campus", "location"],
    },
    {
        "query": "What documents are required for admission?",
        "expected": ["documents", "mark", "score", "certificate"],
    },
]

GENERIC_ANSWERS = [
    "try asking about courses, fees, or admission process.",
    "please enter a valid question.",
    "i'm sorry, i'm having trouble connecting to my brain.",
]


def is_valid_answer(answer: str, expected_keywords: list[str]) -> tuple[bool, str]:
    normalized = " ".join(answer.lower().split())

    if not normalized:
        return False, "empty answer"

    if any(generic in normalized for generic in GENERIC_ANSWERS):
        return False, "generic fallback answer"

    if len(normalized.split()) < 4:
        return False, "answer too short"

    if not any(keyword.lower() in normalized for keyword in expected_keywords):
        return False, f"missing expected keywords: {', '.join(expected_keywords)}"

    return True, "ok"

async def run():
    email = f"codex-e2e-{int(time.time())}@example.com"
    password = "Secret123!"

    results: dict = {
        "signup_email": email,
        "console_errors": [],
        "page_errors": [],
        "failed_requests": [],
        "http_events": [],
        "error_responses": [],
        "login_debug": {},
        "dialogs": [],
        "questions": [],
    }

    browser = None
    page = None

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )
            context = await browser.new_context(viewport={"width": 1440, "height": 1024})
            page = await context.new_page()
            browser.on("disconnected", lambda: results.update({"browser_disconnected": True}))

            page.on(
                "console",
                lambda message: results["console_errors"].append(
                    f"{message.type}: {message.text}"
                )
                if message.type in {"error", "warning"}
                else None,
            )
            page.on("pageerror", lambda error: results["page_errors"].append(str(error)))
            page.on(
                "dialog",
                lambda dialog: (
                    results["dialogs"].append(dialog.message),
                    asyncio.create_task(dialog.accept()),
                ),
            )
            page.on(
                "requestfailed",
                lambda request: results["failed_requests"].append(
                    {
                        "url": request.url,
                        "method": request.method,
                        "error": request.failure,
                    }
                ),
            )
            page.on(
                "response",
                lambda response: (
                    results["http_events"].append(
                        {"url": response.url, "status": response.status}
                    )
                    if "/api/v1/auth/" in response.url or "/api/v1/chat" in response.url
                    else None,
                    results["error_responses"].append(
                        {"url": response.url, "status": response.status}
                    )
                    if response.status >= 400
                    else None,
                ),
            )

            print("STEP: open /auth", flush=True)
            await page.goto(f"{BASE_URL}/auth", wait_until="domcontentloaded")
            await page.wait_for_selector('form[data-auth-ready="true"]')

            if await page.locator("[data-nextjs-dialog]").count():
                raise RuntimeError("Next.js error overlay detected on /auth")

            print("STEP: signup", flush=True)
            await page.get_by_role("button", name="Signup").click()
            await page.wait_for_selector('form[data-auth-ready="true"]')
            signup_form = page.locator("form").first
            await signup_form.get_by_placeholder("Your full name").fill("Codex Student")
            await signup_form.get_by_placeholder("you@example.com").fill(email)
            await signup_form.get_by_placeholder("AIMS2024").fill("AIMS2024")
            await signup_form.get_by_placeholder("Min 6 characters").fill(password)
            await signup_form.get_by_placeholder("Confirm password").fill(password)
            await signup_form.get_by_role("button", name="Create Account").click()
            await page.wait_for_timeout(1000)

            print("STEP: login", flush=True)
            login_form = page.locator("form").first
            await login_form.get_by_placeholder("you@example.com").fill(email)
            await login_form.locator('input[type="password"]').fill(password)
            async with page.expect_response(
                lambda response: "/api/v1/auth/login" in response.url,
                timeout=15000,
            ) as login_response_info:
                await login_form.get_by_role("button", name="Sign In").click()

            login_response = await login_response_info.value
            login_body = await login_response.text()
            results["login_debug"]["response_status"] = login_response.status
            results["login_debug"]["response_body"] = login_body

            for _ in range(30):
                if "/dashboard" in page.url:
                    break
                await page.wait_for_timeout(500)

            results["login_debug"]["final_url"] = page.url
            results["login_debug"]["error_text"] = (
                await page.locator("p.text-red-400").all_inner_texts()
            )
            results["login_debug"]["auth_storage"] = await page.evaluate(
                "localStorage.getItem('aims_auth')"
            )

            if "/dashboard" not in page.url:
                raise RuntimeError(
                    "Login did not redirect to /dashboard after a successful submit"
                )

            print("STEP: open chat", flush=True)
            await page.get_by_role("button", name="Start Chat").click()
            print("STEP: fill onboarding", flush=True)
            await page.get_by_placeholder("Enter your name").fill("Codex Student")
            await page.get_by_placeholder("Enter your email").fill(email)
            await page.get_by_placeholder("Enter phone number").fill("9876543210")
            await page.locator(".radio-card", has_text="MBA").click()
            await page.get_by_role("button", name="Submit").click()
            await page.wait_for_timeout(1000)

            answer_locator = page.locator(
                ".message-row.bot .message-bubble .message-content"
            )
            input_locator = page.get_by_placeholder("Type your inquiry here...")

            for question in QUESTIONS:
                print(f"STEP: ask -> {question['query']}", flush=True)
                before_count = await answer_locator.count()
                await input_locator.fill(question["query"])
                await input_locator.press("Enter")

                await page.wait_for_function(
                    """(previousCount) => {
                        return document.querySelectorAll('.message-row.bot .message-bubble .message-content').length > previousCount
                    }""",
                    arg=before_count,
                    timeout=15000,
                )

                answer = (await answer_locator.last.inner_text()).strip()
                is_valid, reason = is_valid_answer(answer, question["expected"])

                results["questions"].append(
                    {
                        "query": question["query"],
                        "answer": answer,
                        "valid": is_valid,
                        "reason": reason,
                    }
                )
                print(f"RESULT: {question['query']} -> {reason}", flush=True)

            await page.screenshot(path="/tmp/e2e_frontend_login_chat.png", full_page=True)
            await browser.close()
    except Exception as error:
        results["fatal_error"] = str(error)
        if page is not None:
            try:
                results["login_debug"]["final_url"] = page.url
                results["login_debug"]["error_text"] = (
                    await page.locator("p.text-red-400").all_inner_texts()
                )
                results["login_debug"]["auth_storage"] = await page.evaluate(
                    "localStorage.getItem('aims_auth')"
                )
            except Exception:
                pass
        RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
        if browser is not None:
            await browser.close()
        raise

    RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


if __name__ == "__main__":
    try:
        output = asyncio.run(run())
        print(json.dumps(output, indent=2), flush=True)
    except Exception as error:
        if RESULTS_PATH.exists():
            print(RESULTS_PATH.read_text(encoding="utf-8"), flush=True)
        else:
            failure = {"fatal_error": str(error)}
            RESULTS_PATH.write_text(json.dumps(failure, indent=2), encoding="utf-8")
            print(json.dumps(failure, indent=2), flush=True)
        raise
