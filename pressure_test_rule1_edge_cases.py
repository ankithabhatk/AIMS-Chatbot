#!/usr/bin/env python3
"""
PRESSURE TEST: Rule 1 Edge Cases

Testing the weaknesses in current pattern-matching approach.
These are the cases where context-awareness is necessary.
"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.conversation_memory import extract_confidence_signals, UserProfile
from app.services.confidence_engine import update_confidence_score

print("="*80)
print("PRESSURE TEST: Rule 1 Edge Cases")
print("="*80)
print()

# Setup profile with coding interest
profile = UserProfile()
# Assume user has already established coding interest
profile.interests = ["coding"]

test_cases = [
    {
        "name": "Test 1: Reinforcement Without 'Like'",
        "setup": "I've been thinking about coding",
        "test": "I actually feel coding is right for me",
        "expected": "REINFORCE (no penalty)",
        "why": "Same domain, positive language"
    },
    {
        "name": "Test 2: Reinforcement With 'Think'",
        "setup": "I'm interested in coding",
        "test": "actually I think coding makes sense",
        "expected": "REINFORCE (no penalty)",
        "why": "Same domain, affirmative language"
    },
    {
        "name": "Test 3: False Positive - Direction Change",
        "setup": "I like coding",
        "test": "I actually like business more than coding",
        "expected": "PIVOT (apply penalty)",
        "why": "Different domain mentioned, comparison language"
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
    print(f"Context: {test['setup']}")
    print(f"Test Query: {test['test']}")
    print()
    
    # Setup turn (establish initial score)
    setup_signals = extract_confidence_signals(test['setup'], profile)
    setup_score = update_confidence_score(None, setup_signals, test['setup'])
    
    print(f"Setup: '{test['setup']}'")
    print(f"  Signals: {setup_signals}")
    print(f"  Score: {setup_score:.3f}")
    print()
    
    # Test turn
    test_signals = extract_confidence_signals(test['test'], profile)
    test_score = update_confidence_score(setup_score, test_signals, test['test'])
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
    has_clarity = "strong_clarity" in test_signals or "weak_clarity" in test_signals
    
    if i == 1:
        # Test 1: Should reinforce (no pivot penalty)
        status = "✓ PASS" if delta > 0 and not has_pivot else "❌ FAIL"
        result = f"Delta {delta:+.3f}: {'OK' if delta > 0 else 'DOWN'}"
    elif i == 2:
        # Test 2: Should reinforce (no pivot penalty)
        status = "✓ PASS" if delta > 0 else "❌ FAIL"
        result = f"Delta {delta:+.3f}: {'UP (reinforce)' if delta > 0 else 'DOWN (penalized)'}"
    elif i == 3:
        # Test 3: Should pivot (apply penalty, or at least not go up much)
        status = "✓ PASS" if delta <= 0 or delta < 0.1 else "❌ FAIL"
        result = f"Delta {delta:+.3f}: {'Penalized pivot' if delta <= 0 else 'Barely up (concerning)'}"
    elif i == 4:
        # Test 4: Should have both pivot and ambiguity
        status = "✓ PASS" if has_pivot and has_ambiguity else "❌ FAIL"
        result = f"Signals: {test_signals}"
    
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

print("="*80)
print("INSIGHT")
print("="*80)
print("""
Current Pattern Matching Issues:

Test 1 ❌ "actually feel X is right"
  - Pattern doesn't include "feel" or "is right"
  - Will penalize when should reinforce
  
Test 2 ❓ "actually I think X makes sense"
  - Pattern includes "actually i think this is" but NOT "makes sense"
  - Might miss or might catch
  
Test 3 ❌ "actually like business MORE THAN coding"
  - Sees "actually like" → thinks reinforcement
  - But "more than" indicates comparison/switch
  - Will NOT penalize when should
  
Test 4 ✓ "actually I'm not sure"
  - Should work: ambiguity + pivot detected
  
⸻

The Pattern Problem:

You're checking for:
  reinforcing_patterns = ["actually like", "actually yeah", ...]

But real signals are:
  - Same domain mentioned?
  - Positive/negative sentiment?
  - Comparison language used?
  - Any NEW domain introduced?

Profile-aware logic needed.
""")
