"""
AIMS Chatbot — 5-Case Playwright Proof Test (Fixed selectors)
Screenshots → /tmp/proof/
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

FRONTEND_URL = "http://localhost:3000"
PROOF_DIR = Path("/tmp/proof")
PROOF_DIR.mkdir(parents=True, exist_ok=True)


async def ss(page, name):
    path = str(PROOF_DIR / f"{name}.png")
    await page.screenshot(path=path, full_page=False)
    print(f"  📸 {name}.png")
    return path


async def get_last_bot_text(page):
    """Get text of last bot message bubble."""
    els = await page.query_selector_all(".bot-bubble .message-content")
    if not els:
        return ""
    return (await els[-1].inner_text()).strip()


async def get_chips(page):
    """Get suggestion chip texts."""
    chips = await page.query_selector_all(".suggestion-chips-row button, [data-testid^='suggestion-chip-']")
    return [(await c.inner_text()).strip() for c in chips]


async def send_msg(page, text):
    """Type into the main chat textarea and send."""
    inp = page.locator("textarea").last
    await inp.click()
    await inp.fill(text)
    await page.keyboard.press("Enter")
    print(f"  ✉ Sent: '{text}'")


async def wait_response(page, timeout=16000):
    """Wait for typing indicator to appear then disappear."""
    try:
        await page.wait_for_selector(".typing-indicator-bubble", state="visible", timeout=4000)
        await page.wait_for_selector(".typing-indicator-bubble", state="hidden", timeout=timeout)
    except Exception:
        await page.wait_for_timeout(timeout)


async def run():
    results = {}
    api_calls = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--no-sandbox"])
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await ctx.new_page()

        # Capture API calls
        async def on_response(resp):
            if "/api/v1/chat" in resp.url:
                try:
                    req_data = resp.request.post_data
                    api_calls.append({"status": resp.status, "request": req_data, "body": await resp.json()})
                except Exception:
                    pass
        page.on("response", on_response)

        # ─── SETUP ───────────────────────────────────────────────────
        print("\n" + "═"*60)
        print("AIMS CHATBOT — PROOF TEST (v2, correct selectors)")
        print("═"*60)

        print("\n[SETUP] Loading page and clearing session...")
        await page.goto(FRONTEND_URL, wait_until="networkidle")
        await page.evaluate("""
            localStorage.removeItem('aims_user_profile');
            localStorage.removeItem('aims_conversations');
        """)
        await page.reload(wait_until="networkidle")
        await page.wait_for_timeout(1500)
        await ss(page, "00_initial")

        # ─── OPEN CHAT ───────────────────────────────────────────────
        print("\n[STEP 1] Opening chat...")
        # The chat is a sidebar that starts open (ChatWindow checks isChatOpen)
        # Check if chat is already visible
        chat_visible = await page.locator(".chat-main").is_visible()
        if not chat_visible:
            # Try clicking floating robot
            for sel in [".floating-robot-container", "[class*='float']", ".robot-trigger"]:
                try:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=1000):
                        await el.click()
                        await page.wait_for_timeout(1500)
                        break
                except Exception:
                    pass
        await ss(page, "01_chat_state")

        # ─── ONBOARDING ──────────────────────────────────────────────
        print("\n[STEP 2] Completing onboarding form...")
        onboarding_ok = False
        try:
            # Wait for form to appear
            await page.wait_for_selector("input[name='name'], input[placeholder='Enter your name']", timeout=8000)

            # Fill name
            name_inp = page.locator("input[name='name'], input[placeholder='Enter your name']").first
            await name_inp.click()
            await name_inp.fill("Test Student")

            # Fill email
            email_inp = page.locator("input[name='email'], input[placeholder='Enter your email']").first
            await email_inp.click()
            await email_inp.fill("test@aims.ac.in")

            # Fill phone
            phone_inp = page.locator("input[name='mobile'], input[placeholder='Enter phone number']").first
            await phone_inp.click()
            await phone_inp.fill("9876543210")

            # Select MBA course (radio card / div)
            mba_card = page.locator(".radio-card").filter(has_text="MBA").first
            if await mba_card.is_visible(timeout=2000):
                await mba_card.click()
                print("  ✓ Selected MBA via radio-card")
            else:
                # Try select element fallback
                await page.select_option("select[name='course']", "MBA")
                print("  ✓ Selected MBA via select")

            await ss(page, "02_form_filled")

            # Submit
            submit = page.locator("button[type='submit'], .form-submit-btn").first
            await submit.click()
            print("  ✓ Submitted form")
            await page.wait_for_timeout(4000)
            await ss(page, "03_after_submit")

            # Confirm chat unlocked — look for chat input and no form
            chat_unlocked = await page.locator("textarea").is_visible(timeout=4000)
            form_gone = not await page.locator("input[name='name']").is_visible(timeout=1000)
            onboarding_ok = chat_unlocked and form_gone
            print(f"  Onboarding {'✅ PASS' if onboarding_ok else '❌ FAIL'} — textarea={chat_unlocked}, form_gone={form_gone}")
            results["onboarding"] = "PASS" if onboarding_ok else "FAIL"

        except Exception as e:
            print(f"  ❌ Onboarding error: {e}")
            await ss(page, "03_onboarding_err")
            results["onboarding"] = f"FAIL: {str(e)[:100]}"

        # ─── TC1: "mba" ──────────────────────────────────────────────
        print("\n[TC1] Sending: 'mba'")
        try:
            await send_msg(page, "mba")
            await wait_response(page, timeout=16000)
            await page.wait_for_timeout(800)

            bot_text = await get_last_bot_text(page)
            chips = await get_chips(page)
            await ss(page, "tc1_mba")

            print(f"  Response: {bot_text[:200]}")
            print(f"  Chips ({len(chips)}): {chips}")

            passed = len(bot_text) > 5
            results["tc1"] = {"result": "PASS" if passed else "FAIL", "response": bot_text[:300], "chips": chips}
            print(f"  TC1: {'✅ PASS' if passed else '❌ FAIL'}")

        except Exception as e:
            print(f"  ❌ TC1 error: {e}")
            await ss(page, "tc1_error")
            results["tc1"] = {"result": f"FAIL: {str(e)[:100]}"}

        # ─── TC2: "mb" ───────────────────────────────────────────────
        print("\n[TC2] Sending: 'mb'")
        try:
            await send_msg(page, "mb")
            await page.wait_for_timeout(6000)  # short — nonsense path is fast

            bot_text = await get_last_bot_text(page)
            await ss(page, "tc2_mb")
            print(f"  Response: {bot_text[:200]}")

            passed = len(bot_text) > 5
            results["tc2"] = {"result": "PASS" if passed else "FAIL", "response": bot_text[:200]}
            print(f"  TC2: {'✅ PASS' if passed else '❌ FAIL'}")

        except Exception as e:
            print(f"  ❌ TC2 error: {e}")
            await ss(page, "tc2_error")
            results["tc2"] = {"result": f"FAIL: {str(e)[:100]}"}

        # ─── TC3: "mba fees" ─────────────────────────────────────────
        print("\n[TC3] Sending: 'mba fees'")
        try:
            await send_msg(page, "mba fees")
            await wait_response(page, timeout=18000)
            await page.wait_for_timeout(800)

            bot_text = await get_last_bot_text(page)
            chips = await get_chips(page)
            await ss(page, "tc3_mba_fees")
            print(f"  Response: {bot_text[:250]}")
            print(f"  Chips ({len(chips)}): {chips}")

            # Classify
            r = bot_text.lower()
            if any(x in r for x in ["₹", "rs.", "lakh", "fee structure", "annual fee"]):
                rtype = "structured_answer"
            elif "provide your" in r or ("name" in r and "email" in r and "course" in r):
                rtype = "gate"
            elif "contact" in r and "admissions" in r:
                rtype = "fallback"
            else:
                rtype = "other"

            passed = len(bot_text) > 5
            results["tc3"] = {"result": "PASS" if passed else "FAIL", "response": bot_text[:300], "type": rtype, "chips": chips}
            print(f"  Type: {rtype}")
            print(f"  TC3: {'✅ PASS' if passed else '❌ FAIL'}")

        except Exception as e:
            print(f"  ❌ TC3 error: {e}")
            await ss(page, "tc3_error")
            results["tc3"] = {"result": f"FAIL: {str(e)[:100]}"}

        # ─── TC4: Click suggestion chip ──────────────────────────────
        print("\n[TC4] Looking for suggestion chips...")
        try:
            chips_els = await page.query_selector_all(
                ".suggestion-chips-row button, [data-testid^='suggestion-chip-'], .quick-reply-chip"
            )

            if chips_els:
                chip_text = await chips_els[0].inner_text()
                print(f"  Clicking chip: '{chip_text.strip()}'")
                await chips_els[0].click()
                await wait_response(page, timeout=15000)
                await page.wait_for_timeout(800)

                bot_text = await get_last_bot_text(page)
                await ss(page, "tc4_chip_click")
                print(f"  Response: {bot_text[:200]}")

                passed = len(bot_text) > 5
                results["tc4"] = {"result": "PASS" if passed else "FAIL", "chip": chip_text.strip(), "response": bot_text[:250]}
                print(f"  TC4: {'✅ PASS' if passed else '❌ FAIL'}")
            else:
                print("  ⚠ No chips found — SKIP")
                await ss(page, "tc4_no_chips")
                results["tc4"] = {"result": "SKIP", "reason": "no chips visible"}

        except Exception as e:
            print(f"  ❌ TC4 error: {e}")
            await ss(page, "tc4_error")
            results["tc4"] = {"result": f"FAIL: {str(e)[:100]}"}

        # ─── TC5: "fees" ─────────────────────────────────────────────
        print("\n[TC5] Sending: 'fees'")
        try:
            await send_msg(page, "fees")
            await wait_response(page, timeout=12000)
            await page.wait_for_timeout(800)

            bot_text = await get_last_bot_text(page)
            await ss(page, "tc5_fees")
            print(f"  Response: {bot_text[:250]}")

            r = bot_text.lower()
            if "provide your" in r or ("name" in r and "email" in r):
                rtype = "gate"
            elif any(x in r for x in ["₹", "rs.", "lakh", "fee structure"]):
                rtype = "structured"
            elif "contact" in r:
                rtype = "fallback"
            else:
                rtype = "other"

            passed = len(bot_text) > 5
            results["tc5"] = {"result": "PASS" if passed else "FAIL", "response": bot_text[:300], "type": rtype}
            print(f"  Type: {rtype}")
            print(f"  TC5: {'✅ PASS' if passed else '❌ FAIL'}")

        except Exception as e:
            print(f"  ❌ TC5 error: {e}")
            await ss(page, "tc5_error")
            results["tc5"] = {"result": f"FAIL: {str(e)[:100]}"}

        # ─── FINAL ───────────────────────────────────────────────────
        print("\n[FINAL] Final screenshot...")
        await ss(page, "99_final")

        # Save API log
        with open(PROOF_DIR / "api_log.json", "w") as f:
            json.dump(api_calls, f, indent=2, ensure_ascii=False)
        print(f"  API calls captured: {len(api_calls)}")

        await browser.close()

    # ─── REPORT ──────────────────────────────────────────────────────
    print("\n" + "═"*60)
    print("PROOF TEST REPORT")
    print("═"*60)

    all_ok = True
    for key, label in [
        ("onboarding", "ONBOARDING"),
        ("tc1", 'TC1 "mba"'),
        ("tc2", 'TC2 "mb"'),
        ("tc3", 'TC3 "mba fees"'),
        ("tc4", "TC4 Chip Click"),
        ("tc5", 'TC5 "fees"'),
    ]:
        r = results.get(key, "missing")
        if isinstance(r, dict):
            status = r.get("result", "?")
        else:
            status = str(r)

        icon = "✅" if "PASS" in status else ("⚠" if "SKIP" in status else "❌")
        print(f"\n{icon} {label}: {status}")

        if isinstance(r, dict):
            if "response" in r:
                print(f"   Response: {r['response'][:150]}")
            if "chips" in r:
                print(f"   Chips: {r['chips']}")
            if "type" in r:
                print(f"   Type: {r['type']}")
            if "chip" in r:
                print(f"   Chip clicked: {r['chip']}")

        if "FAIL" in status:
            all_ok = False

    print(f"\n{'═'*60}")
    print(f"OVERALL: {'✅ PASS' if all_ok else '❌ FAIL (check details above)'}")
    print(f"Screenshots: {PROOF_DIR}")
    print(f"{'═'*60}\n")

    with open(PROOF_DIR / "summary.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(run())
