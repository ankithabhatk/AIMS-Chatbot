#!/usr/bin/env python3
"""
PRESSURE TEST: Rule 1 UPGRADED - Direction-Aware

Testing the improved logic with direction checking and comparison detection.
"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.conversation_memory import extract_confidence_signals, UserProfile
from app.services.confidence_engine import update_confidence_score

print("="*80)
print("PRESSURE TEST: Rule 1 UPGRADED (Direction-Aware)")
print("="*80)
print()

test_cases = [
    {
        "name": "Test 1: Reinforcement Without 'Like'",
        "setup": "I've been thinking about coding",
        "test": "I actually feel coding is right for me",
        "expected": "REINFORCE (no penalty)",
        "why": "Same domain (coding) + positive sentiment (feel...is right)"
    },
    {
        "name": "Test 2: Reinforcement With 'Think'",
        "setup": "I'm interested in coding",
        "test": "actually I think coding makes sense",
        "expected": "REINFORCE (no penalty)",
        "why": "Same domain (coding) + positive sentiment (makes sense)"
    },
    {
        "name": "Test 3: False Positive FIXED - Direction Change",
        "setup": "I like coding",
        "test": "I actually like business more than coding",
        "expected": "PIVOT (apply penalty)",
        "why": "New domain (business) + comparison language (more than)"
    },
    {
        "name": "Test 4: Neutral Pivot With Ambiguity",
        "setup": "I want to do coding",
        "test": "actually I'm not sure anymore",
        "expected": "PIVOT + AMBIGUITY (both signals)",
        "why": "Direction unclear, uncertainty expressed"
    },
]

results = []

for i, test in enumerate(test_cases, 1):
    print(f"\n{test['name']}")
    print("-" * 80)
    
    # Setup profile with coding interest
    profile = UserProfile()
    profile.interests = ["coding"]
    
    print(f"Context: {test['setup']}")
    print(f"Profile: {profile.interests}")
    print(f"Test Query: {test['test']}")
    print()
    
    # Setup turn (establish initial score)
    setup_signals = extract_confidence_signals(test['setup'], profile)
    setup_score = update_confidence_score(None, setup_signals, query=test['setup'], profile=profile)
    
    print(f"Setup: '{test['setup']}'")
    print(f"  Signals: {setup_signals}")
    print(f"  Score: {setup_score:.3f}")
    print()
    
    # Test turn - PASS PROFILE for direction-aware checking
    test_signals = extract_confidence_signals(test['test'], profile)
    test_score = update_confidence_score(setup_score, test_signals, query=test['test'], profile=profile)
    delta = test_score - setup_score
    
    print(f"Test: '{test['test']}'")
    print(f"  Signals: {test_signals}")
    print(f"  Score: {setup_score:.3f} → {test_score:.3f} ({delta:+.3f})")
    print()
    
    print(f"Expected: {test['expected']}")
    print(f"Why: {test['why']}")
    print()
    
    # Analyze
    has_pivot = "pivot" in test_signals
    has_ambiguity = "ambiguity" in test_signals
    
    if i == 1:
        # Test 1: Should reinforce (no pivot penalty or minimal)
        status = "✓ PASS" if delta > 0.1 else "❌ FAIL"
        result = f"Delta {delta:+.3f}: {'Good reinforcement' if delta > 0.1 else 'Weak'}"
    elif i == 2:
        # Test 2: Should reinforce (no pivot penalty or minimal)
        status = "✓ PASS" if delta > 0.1 else "❌ FAIL"
        result = f"Delta {delta:+.3f}: {'Good reinforcement' if delta > 0.1 else 'Weak'}"
    elif i == 3:
        # Test 3: Should pivot (penalty applied, so delta reduced)
        # Setup 0.45 with clarity, test should be lower due to pivot penalty
        status = "✓ PASS" if delta <= 0.15 else "❌ FAIL"
        result = f"Delta {delta:+.3f}: {'Penalized' if delta <= 0.15 else 'TOO HIGH - not penalized properly'}"
    elif i == 4:
        # Test 4: Should have both pivot and ambiguity
        status = "✓ PASS" if has_pivot and has_ambiguity else "❌ FAIL"
        result = f"Signals: {test_signals} - {'Both present' if has_pivot and has_ambiguity else 'Missing signals'}"
    
    print(f"Status: {status}")
    print(f"Analysis: {result}")
    print()
    
    results.append({
        "test": i,
        "name": test['name'],
        "signals": test_signals,
        "delta": delta,
        "score": test_score,
        "status": status
    })

print("="*80)
print("SUMMARY")
print("="*80)
print()

passed = sum(1 for r in results if "✓ PASS" in r['status'])
failed = sum(1 for r in results if "❌ FAIL" in r['status'])

for r in results:
    print(f"{r['status']} | Test {r['test']}: {r['delta']:+.3f} | {r['name']}")

print()
print(f"Result: {passed}/4 PASS, {failed}/4 FAIL")
print()

if passed == 4:
    print("🎯 ALL TESTS PASS - Rule 1 is now direction-aware!")
else:
    print(f"⚠️  {failed} tests still failing - check implementation")

print()
print("="*80)
print("KEY IMPROVEMENT")
print("="*80)
print("""
Rule 1 UPGRADED FROM: Pattern-Aware → Direction-Aware

Now checks:
1. Comparison language ("more than", "instead of") → PIVOT
2. New domains ("business" not in profile interests) → PIVOT
3. Same domain + positive sentiment → REINFORCE
4. Falls back to patterns if unclear

Before: "actually like business" → incorrectly reinforced
After: "actually like business MORE THAN coding" → correctly penalized
""")
