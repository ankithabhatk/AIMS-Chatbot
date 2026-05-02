#!/usr/bin/env python
"""Quick diagnostic: show actual bot responses for each eval query."""
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.services.evaluator import load_dataset, _run_pipeline, score_response

dataset = load_dataset(os.path.join(_ROOT, "tests", "eval_dataset.json"))
for item in dataset:
    result = _run_pipeline(item["query"])
    resp = result["response"]
    score = score_response(resp, item["expected_keywords"], item.get("expected_answer",""))
    print(f"\n{'='*60}")
    print(f"Q: {item['query']}")
    print(f"Expected tokens: {item.get('expected_answer','')}")
    print(f"Bot response: {resp[:200]}")
    print(f"Score: {score}  Confidence: {result['confidence']:.2f}  Fallback: {result['fallback']}")
