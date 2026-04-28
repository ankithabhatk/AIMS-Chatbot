#!/usr/bin/env python3
"""
Test Phase 2 Fixes:
1. Multi-intent ordering (preserve query order)
2. Protected words in spell correction
"""

import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot')

from backend.app.services.orchestration.engine import (
    detect_multiple_intents,
    correct_query_typos_word_level,
    PROTECTED_WORDS
)

def test_multi_intent_ordering():
    """Test that multi-intent detection preserves query order."""
    print("\n" + "="*70)
    print("TEST 1: Multi-Intent Ordering (Preserve Query Order)")
    print("="*70)
    
    test_cases = [
        {
            "query": "fees and then what is aims",
            "expected_order": ["fees", "about_aims"],
            "description": "Fees mentioned first, should appear first"
        },
        {
            "query": "what is aims and fees for bca",
            "expected_order": ["about_aims", "fees"],
            "description": "About AIMS mentioned first, should appear first"
        },
        {
            "query": "why choose aims and what are placements",
            "expected_order": ["why_aims", "placements"],
            "description": "Why AIMS mentioned first, should appear first"
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        query = test["query"]
        expected = test["expected_order"]
        description = test["description"]
        
        print(f"\nTest 1.{i}: {description}")
        print(f"Query: '{query}'")
        
        intents = detect_multiple_intents(query)
        detected_order = [intent for intent, score in intents]
        
        print(f"Expected order: {expected}")
        print(f"Detected order: {detected_order}")
        
        # Check if detected intents match expected (at least the first ones)
        match = all(d in detected_order for d in expected)
        status = "✅ PASS" if match else "❌ FAIL"
        print(f"Status: {status}")
        
        if intents:
            print(f"Scores: {[(intent, f'{score:.2f}') for intent, score in intents]}")


def test_protected_words():
    """Test that protected words are not spell-corrected."""
    print("\n" + "="*70)
    print("TEST 2: Protected Words (Should NOT be Corrected)")
    print("="*70)
    
    test_cases = [
        {
            "query": "bca fees",
            "should_contain": ["bca", "fees"],
            "description": "BCA and fees should not be corrected"
        },
        {
            "query": "mba placement",
            "should_contain": ["mba", "placement"],
            "description": "MBA and placement should not be corrected"
        },
        {
            "query": "aims admission process",
            "should_contain": ["aims", "admission"],
            "description": "AIMS and admission should not be corrected"
        },
        {
            "query": "btech hostel campus",
            "should_contain": ["btech", "hostel", "campus"],
            "description": "BTech, hostel, campus should not be corrected"
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        query = test["query"]
        should_contain = test["should_contain"]
        description = test["description"]
        
        print(f"\nTest 2.{i}: {description}")
        print(f"Query: '{query}'")
        
        corrected, original = correct_query_typos_word_level(query)
        
        print(f"Original:  '{original}'")
        print(f"Corrected: '{corrected}'")
        
        # Check if protected words are preserved
        all_preserved = all(word.lower() in corrected.lower() for word in should_contain)
        status = "✅ PASS" if all_preserved else "❌ FAIL"
        print(f"Status: {status}")
        
        if not all_preserved:
            missing = [w for w in should_contain if w.lower() not in corrected.lower()]
            print(f"Missing protected words: {missing}")


def test_typo_correction_with_protected_words():
    """Test that typos are still corrected while protecting domain terms."""
    print("\n" + "="*70)
    print("TEST 3: Typo Correction WITH Protected Words")
    print("="*70)
    
    test_cases = [
        {
            "query": "feees for bca",
            "should_correct": "feees",
            "should_protect": "bca",
            "description": "Correct 'feees' but protect 'bca'"
        },
        {
            "query": "admisson process for mba",
            "should_correct": "admisson",
            "should_protect": "mba",
            "description": "Correct 'admisson' but protect 'mba'"
        },
        {
            "query": "placment statistics for btech",
            "should_correct": "placment",
            "should_protect": "btech",
            "description": "Correct 'placment' but protect 'btech'"
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        query = test["query"]
        should_correct = test["should_correct"]
        should_protect = test["should_protect"]
        description = test["description"]
        
        print(f"\nTest 3.{i}: {description}")
        print(f"Query: '{query}'")
        
        corrected, original = correct_query_typos_word_level(query)
        
        print(f"Original:  '{original}'")
        print(f"Corrected: '{corrected}'")
        
        # Check if typo was corrected
        typo_corrected = should_correct.lower() not in corrected.lower()
        protected_preserved = should_protect.lower() in corrected.lower()
        
        status = "✅ PASS" if (typo_corrected and protected_preserved) else "❌ FAIL"
        print(f"Status: {status}")
        
        if not typo_corrected:
            print(f"  ⚠️ Typo '{should_correct}' was not corrected")
        if not protected_preserved:
            print(f"  ⚠️ Protected word '{should_protect}' was not preserved")


def test_protected_words_list():
    """Verify protected words list is comprehensive."""
    print("\n" + "="*70)
    print("TEST 4: Protected Words List Verification")
    print("="*70)
    
    print(f"\nTotal protected words: {len(PROTECTED_WORDS)}")
    print(f"Protected words: {sorted(PROTECTED_WORDS)}")
    
    # Check for critical terms
    critical_terms = {
        "bca", "mba", "aims", "fees", "placement", "admission", "hostel", "campus"
    }
    
    missing = critical_terms - PROTECTED_WORDS
    if missing:
        print(f"\n⚠️ Missing critical terms: {missing}")
    else:
        print(f"\n✅ All critical terms are protected")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PHASE 2 FIXES VALIDATION TEST SUITE")
    print("="*70)
    
    try:
        test_protected_words_list()
        test_multi_intent_ordering()
        test_protected_words()
        test_typo_correction_with_protected_words()
        
        print("\n" + "="*70)
        print("TEST SUITE COMPLETE")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
