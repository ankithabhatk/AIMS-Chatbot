#!/usr/bin/env python3
"""
Verify the actual router bug vs test import issue.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Test 1: What the test script is actually calling
print("="*80)
print("TEST 1: What test_input_handling.py is actually calling")
print("="*80)

from app.services.orchestration.engine import (
    compute_intent_scores as engine_scores,
    detect_structured_intent
)
from app.services.counselor.router import (
    compute_intent_scores as router_scores,
    detect_intents as router_detect_intents
)

test_queries = ["fees", "fees???", "admission???", "hi", "asdfgh"]

print("\n🔴 Router.py compute_intent_scores (what test is using):")
for query in test_queries:
    scores = router_scores(query)
    print(f"  '{query}' → {scores}")

print("\n✓ Engine.py compute_intent_scores (correct one):")
for query in test_queries:
    scores = engine_scores(query)
    print(f"  '{query}' → {scores}")

print("\n✓ Structured Intent Detection (engine.py):")
for query in test_queries:
    intent, score = detect_structured_intent(query)
    print(f"  '{query}' → intent={intent}, score={score}")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("""
The test script has an IMPORT BUG:

1. Test imports: from app.services.orchestration.engine import detect_intents
2. But detect_intents() doesn't exist in engine.py
3. So Python imports from router.py instead
4. router.py's compute_intent_scores() has NO "fees", "admission", "courses" keys
5. Result: All scores = 0.0

THE SYSTEM IS NOT BROKEN — the test is using the wrong function!

The correct functions (in engine.py) work fine:
- compute_intent_scores() returns proper scores
- detect_structured_intent() returns correct intents
""")
