import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.abspath("."))
from app.services.evaluator import _run_pipeline, compute_similarity, _clean_response

result = _run_pipeline("Does AIMS have hostel facility?")
resp = result["response"]
cleaned = _clean_response(resp)
ea = "AIMS has on-campus hostel separate blocks for boys and girls 24/7 security CCTV wifi mess facility medical support"

print("=== RAW RESPONSE (first 400 chars) ===")
print(repr(resp[:400]))
print()
print("=== CLEANED RESPONSE (first 400 chars) ===")
print(repr(cleaned[:400]))
print()
sim_raw = compute_similarity(resp, ea)
sim_clean = compute_similarity(cleaned, ea)
print(f"sim RAW   = {sim_raw}")
print(f"sim CLEAN = {sim_clean}")
