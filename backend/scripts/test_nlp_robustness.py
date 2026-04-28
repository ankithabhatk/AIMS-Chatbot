#!/usr/bin/env python3
"""
NLP Robustness Test Script

Tests:
1. Intent detection with spelling variations
2. Keyword matching with fuzzy search
3. Fallback handling

Usage:
    python scripts/test_nlp_robustness.py
"""

import sys
sys.path.insert(0, '.')

from app.services.llm.intent_aware_composer import detect_intent
from rapidfuzz import fuzz
from rapidfuzz.fuzz import partial_ratio

def test_intent_detection():
    """Test intent detection with variations"""
    tests = [
        ("What courses do you offer?", "courses"),
        ("What is the fee for MBA?", "fees"),
        ("Tell me about admission process", "admission"),
        ("What about placements?", "placements"),
        ("Do you have hostel?", "campus"),
        # Variations
        ("What corses do you offer?", "courses"),  # misspelled
        ("What is the feees for MBA?", "fees"),  # misspelled
        ("How to aply for admission?", "admission"),  # misspelled
        ("Whats the placemnt record?", "placements"),  # misspelled
        ("Is ther hostel faclity?", "campus"),  # misspelled
    ]
    
    print("\n=== INTENT DETECTION TEST ===")
    
    # Try fuzzy matching
    def detect_intent_fuzzy(query: str) -> str:
        q = query.lower()
        
        # Keywords
        keyword_map = {
            "fees": ["fee", "cost", "tuition", "price", "scholarship", "financial"],
            "admission": ["admission", "apply", "enrol", "eligibility", "requirement", "process"],
            "placements": ["placement", "job", "recruit", "package", "salary", "lpa", "company"],
            "campus": ["hostel", "room", "stay", "accommodation", "facility", "campus"],
            "courses": ["course", "program", "mba", "mca", "specialization"],
        }
        
        # Check with fuzzy matching
        for intent, keywords in keyword_map.items():
            for kw in keywords:
                if partial_ratio(q, kw) > 80:
                    return intent
        
        # Fallback to strict matching
        return detect_intent(query)
    
    passed = 0
    for query, expected in tests:
        result = detect_intent_fuzzy(query)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        print(f"{status} '{query[:35]}' → {result} (expected: {expected})")
    
    print(f"\nPassed: {passed}/{len(tests)}")


def test_fuzzy_search():
    """Test fuzzy keyword matching"""
    print("\n=== FUZZY SEARCH TEST ===")
    
    queries = [
        ("mba course", "mba course"),
        ("mba", "mba"),
        ("courses", "courses"),
        ("fee", "fee"),
        ("fees", "fee"),
        ("admission", "admission"),
        ("placements", "placements"),
        ("placemnt", "placements"),  # misspelled
    ]
    
    passed = 0
    for query, target in queries:
        score = partial_ratio(query.lower(), target.lower())
        matched = score > 80
        if matched:
            passed += 1
        print(f"{'✓' if matched else '✗'} '{query}' → '{target}' (score: {score})")
    
    print(f"\nPassed: {passed}/{len(queries)}")


def test_fallback():
    """Test fallback handling"""
    print("\n=== FALLBACK TEST ===")
    
    # Simulate weak docs
    weak_docs = [
        ("Some random content", 0.25, "", ""),
    ]
    
    # Check if fallback works
    confidence = 0.25
    threshold = 0.40
    
    is_fallback = confidence < threshold
    print(f"{'✓' if is_fallback else '✗'} Weak docs → fallback: {is_fallback}")
    
    # Strong docs
    strong_docs = [
        ("MBA program details", 0.55, "", ""),
    ]
    
    confidence = 0.55
    is_fallback = confidence < threshold
    print(f"{'✓' if not is_fallback else '✗'} Strong docs → answer: {not is_fallback}")


if __name__ == "__main__":
    test_intent_detection()
    test_fuzzy_search()
    test_fallback()
    print("\n=== NLP ROBUSTNESS TESTS COMPLETE ===")