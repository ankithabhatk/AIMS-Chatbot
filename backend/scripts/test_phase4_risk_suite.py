#!/usr/bin/env python3
"""
Phase 4 regression suite for the EduNexus chatbot orchestration layer.

This covers the post-implementation risk checklist around:
- intent routing
- response contract consistency
- fallback behavior
- self-healing regressions
- session/context handling
- optional browser-flow verification

Usage:
  ./backend/.venv/bin/python backend/scripts/test_phase4_risk_suite.py
  ./backend/.venv/bin/python backend/scripts/test_phase4_risk_suite.py --web-url http://127.0.0.1:3000
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional
from unittest.mock import AsyncMock, patch


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi import BackgroundTasks

from app.api import chat_phase4
from app.models.schemas import ChatRequest
from app.services.llm.small_model_engine import get_small_model_engine
from app.services.orchestration.self_healing_engine import FALLBACK_ANSWER, execute_orchestration, get_self_healing_engine


CheckFn = Callable[[], "CheckResult"]


@dataclass
class CheckResult:
    id: str
    name: str
    status: str
    details: str
    elapsed_ms: int = 0


class CheckFailure(AssertionError):
    pass


class CheckSkip(RuntimeError):
    pass


def pass_result(check_id: str, name: str, details: str, elapsed_ms: int) -> CheckResult:
    return CheckResult(id=check_id, name=name, status="PASS", details=details, elapsed_ms=elapsed_ms)


def fail_result(check_id: str, name: str, details: str, elapsed_ms: int) -> CheckResult:
    return CheckResult(id=check_id, name=name, status="FAIL", details=details, elapsed_ms=elapsed_ms)


def skip_result(check_id: str, name: str, details: str, elapsed_ms: int) -> CheckResult:
    return CheckResult(id=check_id, name=name, status="SKIP", details=details, elapsed_ms=elapsed_ms)


def ensure(condition: bool, details: str) -> None:
    if not condition:
        raise CheckFailure(details)


async def _resolve_user_context_passthrough(request: ChatRequest, session_id: str) -> Dict[str, Any]:
    return chat_phase4._extract_user_context(request)


def _no_log(*args: Any, **kwargs: Any) -> None:
    return None


def _no_sync_session(*args: Any, **kwargs: Any) -> None:
    return None


async def call_chat(
    query: str,
    *,
    user_context: Optional[Dict[str, Any]] = None,
    retrieved_chunks: Optional[Any] = None,
    intent: Optional[str] = None,
    confidence: Optional[Any] = None,
    patch_context: bool = True,
) -> Dict[str, Any]:
    request = ChatRequest(
        query=query,
        user_context=user_context,
        retrieved_chunks=retrieved_chunks,
        intent=intent,
        confidence=confidence,
        context={"session_id": f"risk-suite-{int(time.time() * 1000)}"},
    )

    patches = [
        patch.object(chat_phase4, "_log_query", new=_no_log),
    ]
    if patch_context:
        patches.extend(
            [
                patch.object(chat_phase4, "_resolve_user_context", new=_resolve_user_context_passthrough),
                patch.object(chat_phase4, "_sync_session_and_lead", new=_no_sync_session),
            ]
        )

    with patches[0], *(patches[1:]):
        payload = await chat_phase4.chat_endpoint(request, BackgroundTasks())
    return payload


def run_sync_check(check_id: str, name: str, fn: Callable[[], str]) -> CheckResult:
    started = time.time()
    try:
        details = fn()
        return pass_result(check_id, name, details, int((time.time() - started) * 1000))
    except CheckSkip as exc:
        return skip_result(check_id, name, str(exc), int((time.time() - started) * 1000))
    except Exception as exc:
        detail = str(exc) or traceback.format_exc(limit=1)
        return fail_result(check_id, name, detail, int((time.time() - started) * 1000))


def run_async_check(check_id: str, name: str, fn: Callable[[], Awaitable[str]]) -> CheckResult:
    started = time.time()
    try:
        details = asyncio.run(fn())
        return pass_result(check_id, name, details, int((time.time() - started) * 1000))
    except CheckSkip as exc:
        return skip_result(check_id, name, str(exc), int((time.time() - started) * 1000))
    except Exception as exc:
        detail = str(exc) or traceback.format_exc(limit=1)
        return fail_result(check_id, name, detail, int((time.time() - started) * 1000))


def check_small_big_collision_and_contract() -> str:
    query = "mba fees and placements"
    small = get_small_model_engine().process(query)
    big = execute_orchestration(query).as_dict()
    required_keys = {"answer", "intent", "mode", "confidence", "self_score", "fallback"}

    ensure(required_keys.issubset(set(small.keys())), f"Small model keys missing: {sorted(required_keys - set(small.keys()))}")
    ensure(required_keys.issubset(set(big.keys())), f"Big model keys missing: {sorted(required_keys - set(big.keys()))}")

    small_answer = small["answer"].lower()
    big_answer = big["answer"].lower()
    ensure("fee" in small_answer and "placement" in small_answer, "Small model combined answer dropped either fee or placement content")
    ensure("fee" in big_answer and "placement" in big_answer, "Big model combined answer dropped either fee or placement content")

    return "Small and big paths expose the same core schema and both retain fee + placement content for a combined query."


def check_self_heal_preserves_structured_answer() -> str:
    result = execute_orchestration("mba fees")
    lines = [line.strip() for line in result.answer.splitlines() if line.strip()]

    ensure(not result.fallback, "Structured fees query fell back unexpectedly")
    ensure(result.mode == "structured", f"Expected structured mode, got {result.mode}")
    ensure(lines and lines[0].lower().startswith("mba fee structure"), f"Unexpected first line: {lines[:1]}")
    ensure(any("annual fee:" in line.lower() for line in lines), "Structured fee answer lost the annual fee line")
    ensure(any("contact:" in line.lower() for line in lines), "Structured fee answer lost the admissions contact line")

    return "Structured fee answers stay line-oriented and do not get rewritten into fallback/noise output."


async def check_hostel_facilities_avoid_fallback() -> str:
    payload = await call_chat("tell me about hostel facilities")
    answer = str(payload.get("answer", "")).lower()

    ensure(not payload.get("fallback"), f"Hostel query unexpectedly fell back: {payload}")
    ensure(payload.get("mode") == "structured", f"Expected structured campus handling, got {payload.get('mode')}")
    ensure("hostel" in answer and ("wifi" in answer or "wi-fi" in answer) and "mess" in answer, "Hostel response lost expected facility facts")

    return "Hostel/facilities queries resolve to a grounded non-fallback answer."


def check_intent_collapse_difference_query() -> str:
    result = execute_orchestration("placement vs admission difference").as_dict()
    answer = result["answer"].lower()

    ensure(not result["fallback"], "Difference query fell back instead of answering or comparing")
    ensure("placement" in answer and "admission" in answer, "Difference query collapsed to a single intent")

    return "Difference query preserved both placement and admission semantics."


def check_bullet_filter_retains_valid_content() -> str:
    engine = get_self_healing_engine()
    answer = "• Hostel available\n• WiFi\n• Mess facility"
    chunks = [
        {
            "content": "Hostel available. WiFi. Mess facility.",
            "score": 0.95,
            "url": "https://www.theaims.ac.in/hostel",
            "heading": "Hostel",
            "id": "chunk-1",
        }
    ]

    filtered = engine._remove_unsupported_bullets(answer, chunks)
    ensure("Hostel available" in filtered, "Bullet filter removed 'Hostel available'")
    ensure("WiFi" in filtered, "Bullet filter removed 'WiFi'")
    ensure("Mess facility" in filtered, "Bullet filter removed 'Mess facility'")

    return "Supported short bullets survive the cleanup filter."


async def check_confidence_coercion_does_not_break_fees() -> str:
    payload = await call_chat("mba fees", confidence=0.2)
    ensure(not payload.get("fallback"), f"Low predicted confidence wrongly forced fallback: {payload}")
    ensure(payload.get("intent") == "fees", f"Expected fees intent, got {payload.get('intent')}")

    return "Low external confidence does not override a deterministic structured fee answer."


def check_multi_intent_priority_order() -> str:
    result = execute_orchestration("mba fees placement salary").as_dict()
    answer = result["answer"].lower()

    ensure(not result["fallback"], "Multi-intent fees/placements query fell back")
    ensure("fee" in answer and "placement" in answer, "Multi-intent query answered only one side of the request")

    return "Fees + placements multi-intent queries keep both dimensions in the final answer."


async def check_weak_rag_chunks_fallback() -> str:
    payload = await call_chat(
        "placement record",
        retrieved_chunks=[
            {"content": "random text", "score": 0.2, "url": "", "heading": "", "id": "weak-1"},
            {"content": "irrelevant info", "score": 0.2, "url": "", "heading": "", "id": "weak-2"},
        ],
    )
    ensure(payload.get("fallback"), f"Weak chunks should have forced fallback, got {payload}")

    return "Weak/irrelevant RAG chunks collapse to fallback instead of producing garbage."


async def check_iit_query_stays_low_confidence() -> str:
    payload = await call_chat("mba fee in iit bombay")
    ensure(payload.get("fallback"), f"Out-of-scope IIT fee query should fallback, got {payload}")
    ensure(float(payload.get("confidence", 1.0)) <= 0.45, f"Out-of-scope query returned misleading confidence: {payload.get('confidence')}")
    ensure(payload.get("answer") == FALLBACK_ANSWER, "Fallback answer drifted for out-of-scope IIT query")

    return "Out-of-scope IIT fee queries stay on fallback with low confidence."


def check_out_of_scope_filter_not_too_hard() -> str:
    result = execute_orchestration("mba vs iit mba difference").as_dict()
    ensure(not result["fallback"], "Comparison query was fully blocked instead of answering the AIMS side")
    return "Comparison query returned a partial/non-blocked answer."


async def check_user_context_does_not_override_explicit_course() -> str:
    payload = await call_chat("mba fees", user_context={"course": "BCA"})
    answer = str(payload.get("answer", ""))

    ensure("MBA" in answer, f"Explicit MBA query lost MBA context: {answer}")
    ensure("For BCA" not in answer, f"User course incorrectly overrode explicit MBA query: {answer}")

    return "Explicit course terms in the query beat saved user course context."


async def check_legacy_courses_flow() -> str:
    payload = await call_chat("courses")
    answer = str(payload.get("answer", "")).lower()

    ensure(not payload.get("fallback"), f"'courses' regressed into fallback: {payload}")
    ensure(payload.get("intent") == "courses", f"Expected courses intent, got {payload.get('intent')}")
    ensure("postgraduate" in answer and "undergraduate" in answer, "Courses answer lost the grouped course listing")

    return "Legacy 'courses' queries still resolve through the structured path."


async def check_db_failure_graceful() -> str:
    import app.services.database.supabase_client as supabase_client
    import app.services.lead_handler as lead_handler

    request = ChatRequest(
        query="mba fees",
        user_context={"email": "student@example.com", "course": "MBA"},
        context={"session_id": "db-down-risk-suite"},
    )

    with patch.object(lead_handler, "get_or_create_session", side_effect=RuntimeError("db down")), \
        patch.object(lead_handler, "update_session_on_query", side_effect=RuntimeError("db down")), \
        patch.object(lead_handler, "mark_session_as_lead", side_effect=RuntimeError("db down")), \
        patch.object(lead_handler, "get_email_from_session", new=AsyncMock(side_effect=RuntimeError("db down"))), \
        patch.object(lead_handler, "recover_session_from_db", new=AsyncMock(side_effect=RuntimeError("db down"))), \
        patch.object(supabase_client, "get_lead_store", side_effect=RuntimeError("db down")), \
        patch.object(chat_phase4, "_log_query", new=_no_log):
        payload = await chat_phase4.chat_endpoint(request, BackgroundTasks())

    ensure(not payload.get("fallback"), f"DB-side failures should not break structured answers: {payload}")
    ensure("MBA" in str(payload.get("answer", "")), "Structured answer was lost during DB failure handling")

    return "DB/session failures stay isolated from the answer path."


def check_timeout_interaction_gap() -> str:
    raise CheckSkip("No explicit request-timeout controller exists in the current orchestration path; add one before this can be asserted automatically.")


def run_optional_ui_suite(web_url: str, headful: bool = False) -> List[CheckResult]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - optional dependency path
        return [skip_result("15-18", "UI / Browser Flow", f"Playwright unavailable: {exc}", 0)]

    output_dir = Path("/tmp/phase4-risk-suite")
    output_dir.mkdir(parents=True, exist_ok=True)

    def wait_for_idle(page: Any, ms: int = 1200) -> None:
        page.wait_for_timeout(ms)

    def send_query(page: Any, text: str) -> None:
        page.fill("textarea", text)
        page.click("button.send-btn")
        page.wait_for_timeout(2500)

    started = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not headful)
            context = browser.new_context(viewport={"width": 1440, "height": 960})
            page = context.new_page()
            requests: List[Dict[str, Any]] = []

            def handle_request(request: Any) -> None:
                if request.method == "POST" and request.url.endswith("/api/v1/chat"):
                    try:
                        requests.append(request.post_data_json)
                    except Exception:
                        requests.append({"raw": request.post_data})

            page.on("request", handle_request)

            page.goto(web_url, wait_until="domcontentloaded", timeout=20000)
            page.evaluate("window.localStorage.clear()")
            page.reload(wait_until="domcontentloaded")
            wait_for_idle(page)

            page.click(".floating-robot-trigger")
            page.fill('input[name="name"]', "Risk Suite")
            page.fill('input[name="email"]', "risk-suite@example.com")
            page.fill('input[name="mobile"]', "9876543210")
            page.click('.radio-card:has-text("MBA")')
            page.click('button[type="submit"]')
            page.wait_for_timeout(2000)

            ensure(page.locator("text=Thank you").count() > 0, "Onboarding acknowledgement did not render")

            send_query(page, "mba fees")
            ensure(requests, "No chat API request was captured from the UI")
            last_request = requests[-1]
            ensure(last_request.get("context", {}).get("session_id"), f"UI payload missing context.session_id: {last_request}")
            ensure(last_request.get("user", {}).get("course") == "MBA", f"UI payload missing user course: {last_request}")
            ensure(page.locator("text=MBA fee structure").count() > 0, "Fees response did not render in the UI")

            page.reload(wait_until="domcontentloaded")
            wait_for_idle(page)
            page.click(".floating-robot-trigger")
            ensure(page.locator('input[name="name"]').count() == 0, "Refresh reopened onboarding instead of restoring the saved profile")

            send_query(page, "hostel")
            ensure(page.locator("text=Hostel").count() > 0, "Hostel response did not render after refresh")

            page.fill("textarea", "mba fees")
            for _ in range(5):
                page.click("button.send-btn", force=True)
            page.wait_for_timeout(2500)

            user_texts = page.locator(".message-row.user .message-bubble").all_inner_texts()
            duplicate_count = sum(1 for text in user_texts if text.strip().lower() == "mba fees")
            ensure(duplicate_count == 1, f"Spam send created duplicate user turns: {duplicate_count}")

            send_query(page, "wat corses u hav")
            send_query(page, "hostel facilities")
            send_query(page, "mba fees and admission")
            send_query(page, "tell me about iit bombay")

            page.screenshot(path=str(output_dir / "phase4-ui-suite.png"), full_page=True)
            browser.close()

        elapsed_ms = int((time.time() - started) * 1000)
        return [
            pass_result(
                "15-18",
                "UI / Browser Flow",
                "Captured chat payloads, verified refresh persistence, and confirmed spam-click protection in the live UI.",
                elapsed_ms,
            )
        ]
    except Exception as exc:
        elapsed_ms = int((time.time() - started) * 1000)
        return [fail_result("15-18", "UI / Browser Flow", str(exc), elapsed_ms)]


def build_results(web_url: Optional[str], headful: bool) -> List[CheckResult]:
    results: List[CheckResult] = []
    results.append(run_sync_check("1+9", "Small vs Big Contract", check_small_big_collision_and_contract))
    results.append(run_sync_check("2", "Structured Self-Heal Preservation", check_self_heal_preserves_structured_answer))
    results.append(run_async_check("3", "Hostel Avoids Fallback", check_hostel_facilities_avoid_fallback))
    results.append(run_sync_check("4", "Intent Collapse Guard", check_intent_collapse_difference_query))
    results.append(run_sync_check("5", "Bullet Filter Retention", check_bullet_filter_retains_valid_content))
    results.append(run_async_check("6", "Confidence Coercion Guard", check_confidence_coercion_does_not_break_fees))
    results.append(run_sync_check("7", "Multi-Intent Fees + Placements", check_multi_intent_priority_order))
    results.append(run_async_check("8", "Weak RAG Chunks Fallback", check_weak_rag_chunks_fallback))
    results.append(run_async_check("10", "Misleading Self-Score Guard", check_iit_query_stays_low_confidence))
    results.append(run_sync_check("11", "Out-of-Scope Filter Softness", check_out_of_scope_filter_not_too_hard))
    results.append(run_async_check("12", "Explicit Query Beats User Context", check_user_context_does_not_override_explicit_course))
    results.append(run_async_check("13", "Legacy Courses Flow", check_legacy_courses_flow))
    results.append(run_async_check("16", "DB Failure Isolation", check_db_failure_graceful))
    results.append(run_sync_check("14", "Timeout Interaction", check_timeout_interaction_gap))
    if web_url:
        results.extend(run_optional_ui_suite(web_url, headful=headful))
    else:
        results.append(skip_result("15-18", "UI / Browser Flow", "Skipped: pass --web-url to run the live browser/session suite.", 0))
    return results


def print_report(results: List[CheckResult]) -> None:
    print("\nPhase 4 Risk Suite")
    print("==================")
    for result in results:
        print(f"[{result.status:<4}] {result.id:<5} {result.name} ({result.elapsed_ms} ms)")
        print(f"       {result.details}")

    passed = sum(1 for result in results if result.status == "PASS")
    failed = sum(1 for result in results if result.status == "FAIL")
    skipped = sum(1 for result in results if result.status == "SKIP")

    print("\nSummary")
    print("-------")
    print(f"Passed : {passed}")
    print(f"Failed : {failed}")
    print(f"Skipped: {skipped}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Phase 4 chatbot risk suite.")
    parser.add_argument("--web-url", help="Optional frontend URL for the live browser/session suite.")
    parser.add_argument("--headful", action="store_true", help="Run the browser suite with a visible window.")
    parser.add_argument("--output-json", help="Optional path to write the result report as JSON.")
    args = parser.parse_args()

    results = build_results(args.web_url, args.headful)
    print_report(results)

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps([asdict(result) for result in results], indent=2))
        print(f"\nWrote JSON report to {output_path}")

    return 1 if any(result.status == "FAIL" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
