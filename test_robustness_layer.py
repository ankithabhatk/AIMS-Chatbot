"""Test SymSpell + Confidence + Clarification layers."""

import sys
sys.path.insert(0, "/Users/maneeth/Desktop/Chat-Bot/backend")

from app.services.orchestration.engine import (
    execute_orchestration,
    correct_query_typos,
    _compute_rag_confidence,
    generate_clarification_response,
    CLARIFICATION_THRESHOLD,
)

print("=" * 70)
print("1. TYPO CORRECTION TESTS (SymSpell)")
print("=" * 70)

typo_tests = [
    ("plcement info", "placement info"),
    ("admision process", "admission process"),
    ("locaton of colage", "location of college"),
    ("fees structre", "fees structure"),
    ("mba cources", "mba courses"),
    ("how to rech", "how to reach"),
]

for original, expected_like in typo_tests:
    corrected, orig = correct_query_typos(original)
    status = "PASS" if corrected != original else "NO_CHANGE"
    print(f"[{status}] '{original}' -> '{corrected}'")

print("\n" + "=" * 70)
print("2. FULL PIPELINE TESTS")
print("=" * 70)

pipeline_tests = [
    # (query, expected_mode_contains)
    ("where is the college", "tool"),
    ("how to apply", "tool"),
    ("mba fees", "structured"),
    ("bca admission", "structured"),
    # Typo + intent
    ("plcement info", "rag"),          # corrected to "placement info" -> RAG
    ("admision process", "structured"), # corrected to "admission process" -> structured
    # Ambiguous / low confidence queries
    ("course worth", "clarification"),
    ("something random", "clarification"),
]

for query, expected_mode in pipeline_tests:
    try:
        result = execute_orchestration(query)
        status = "PASS" if expected_mode in result.mode else "FAIL"
        print(f"\n[{status}] Query: '{query}'")
        print(f"         Mode: {result.mode} | Confidence: {result.confidence:.2f}")
        print(f"         Answer: {result.answer[:100]}...")
    except Exception as e:
        print(f"\n[ERROR] Query: '{query}' -> {e}")

print("\n" + "=" * 70)
print("3. CONFIDENCE THRESHOLD TESTS")
print("=" * 70)

# Simulate low-confidence scenario directly
clarification = generate_clarification_response("course worth", ["courses"])
print(f"Clarification mode: {clarification.mode}")
print(f"Clarification answer:\n{clarification.answer}\n")
print(f"Suggestions: {clarification.suggestions}")

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
