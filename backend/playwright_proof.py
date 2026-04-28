"""
Playwright Proof Script
=======================
Hits /api/v1/chat directly (no frontend needed) and renders
the JSON response in an HTML page for screenshot capture.

Saves to /tmp/proof/:
  - fees_response.png
  - admission_response.png
  - placements_response.png
"""

import asyncio
import json
import os
import httpx
from playwright.async_api import async_playwright

API_URL = "http://localhost:8000/api/v1/chat"
PROOF_DIR = "/tmp/proof"


async def query_api(query: str) -> dict:
    """Hit the chat API and return the JSON response."""
    payload = {
        "query": query,
        "context": {"session_id": f"proof-{query[:10].replace(' ', '-')}"}
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(API_URL, json=payload)
        r.raise_for_status()
        return r.json()


def build_html(query: str, data: dict) -> str:
    """Render the API response as a styled HTML card."""
    intent = data.get("intent") or data.get("meta", {}).get("intent", "—")
    mode = data.get("meta", {}).get("compose_mode") or data.get("mode", "—")
    status = data.get("status", "unlock")
    confidence = data.get("confidence", 0)
    answer = data.get("answer") or ""
    sections = data.get("sections") or []
    ctas = data.get("ctas") or []
    fallback = data.get("fallback", False)

    # Build sections HTML
    sections_html = ""
    for s in sections:
        if not s:
            continue
        title = s.get("title", "")
        items = s.get("items", [])
        items_html = "".join(f"<li>{item}</li>" for item in items)
        sections_html += f"""
        <div class="section">
            <h3>{title}</h3>
            <ul>{items_html}</ul>
        </div>"""

    # Build CTAs HTML
    ctas_html = ""
    for cta in ctas:
        ctas_html += f'<button class="cta">{cta.get("label", "")}</button>'

    answer_html = f'<p class="answer">{answer}</p>' if answer else ""

    status_color = "#e74c3c" if status == "lock" else "#27ae60"
    fallback_badge = '<span class="badge fallback">FALLBACK</span>' if fallback else '<span class="badge ok">OK</span>'

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Proof: {query}</title>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; background: #0f0f1a; color: #e0e0f0; padding: 32px; margin: 0; }}
  .card {{ background: #1a1a2e; border-radius: 16px; padding: 28px; max-width: 720px; border: 1px solid #2a2a4a; box-shadow: 0 8px 32px rgba(0,0,0,0.4); }}
  .query {{ font-size: 22px; font-weight: 700; color: #a78bfa; margin-bottom: 16px; }}
  .meta {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }}
  .chip {{ background: #2a2a4a; border-radius: 8px; padding: 4px 12px; font-size: 12px; }}
  .chip strong {{ color: #a78bfa; }}
  .answer {{ background: #222240; border-left: 4px solid #a78bfa; padding: 14px 18px; border-radius: 8px; margin-bottom: 20px; white-space: pre-wrap; line-height: 1.6; }}
  .section {{ background: #1e1e3a; border-radius: 10px; padding: 16px 20px; margin-bottom: 14px; }}
  .section h3 {{ margin: 0 0 10px; color: #c4b5fd; font-size: 15px; }}
  .section ul {{ margin: 0; padding-left: 20px; }}
  .section li {{ margin-bottom: 6px; line-height: 1.5; }}
  .ctas {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 20px; }}
  .cta {{ background: linear-gradient(135deg, #7c3aed, #4f46e5); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-size: 14px; cursor: pointer; font-weight: 600; }}
  .badge {{ border-radius: 6px; padding: 3px 10px; font-size: 11px; font-weight: 700; }}
  .badge.ok {{ background: #166534; color: #86efac; }}
  .badge.fallback {{ background: #7f1d1d; color: #fca5a5; }}
  .status {{ display: inline-block; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; background: {status_color}22; color: {status_color}; border: 1px solid {status_color}; }}
  h2 {{ margin: 0 0 6px; color: #fff; font-size: 18px; }}
  .raw {{ margin-top: 24px; background: #111; border-radius: 8px; padding: 14px; font-size: 11px; font-family: monospace; color: #6ee7b7; overflow-x: auto; }}
</style>
</head>
<body>
<div class="card">
  <div class="query">🔍 Query: "{query}"</div>
  <div class="meta">
    <div class="chip"><strong>Intent:</strong> {intent}</div>
    <div class="chip"><strong>Mode:</strong> {mode}</div>
    <div class="chip"><strong>Confidence:</strong> {confidence}</div>
    <div class="chip"><strong>Status:</strong> <span class="status">{status}</span></div>
    <div class="chip">{fallback_badge}</div>
  </div>
  {answer_html}
  {sections_html}
  <div class="ctas">{ctas_html}</div>
  <details>
    <summary style="color:#6b7280;cursor:pointer;font-size:12px;margin-top:16px">Raw JSON</summary>
    <pre class="raw">{json.dumps(data, indent=2, ensure_ascii=False)}</pre>
  </details>
</div>
</body>
</html>"""


async def main():
    os.makedirs(PROOF_DIR, exist_ok=True)

    tests = [
        ("mba fees", "fees_response.png"),
        ("mba admission process", "admission_response.png"),
        ("mba placements", "placements_response.png"),
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 800, "height": 700})

        for query, filename in tests:
            print(f"\n▶ Testing: '{query}'")
            try:
                data = await query_api(query)
                print(f"  intent={data.get('intent') or data.get('meta', {}).get('intent')}")
                print(f"  status={data.get('status')}")
                print(f"  sections={len(data.get('sections') or [])}")
                print(f"  ctas={len(data.get('ctas') or [])}")
                print(f"  answer_preview={str(data.get('answer', ''))[:80]}")

                html = build_html(query, data)
                await page.set_content(html, wait_until="domcontentloaded")
                await page.wait_for_timeout(500)

                path = os.path.join(PROOF_DIR, filename)
                await page.screenshot(path=path, full_page=True)
                print(f"  ✅ Screenshot saved: {path}")

            except Exception as e:
                print(f"  ❌ Error: {e}")
                # Save error page
                err_html = f"<html><body style='background:#1a0000;color:#ff6b6b;padding:40px;font-family:monospace'><h2>Error for '{query}'</h2><pre>{e}</pre></body></html>"
                await page.set_content(err_html)
                path = os.path.join(PROOF_DIR, filename)
                await page.screenshot(path=path)

        await browser.close()
        print(f"\n✅ All screenshots saved to {PROOF_DIR}/")


if __name__ == "__main__":
    asyncio.run(main())
