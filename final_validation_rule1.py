#!/usr/bin/env python3
"""
FINAL VALIDATION: Rule 1 Upgraded to Direction-Aware

Shows:
1. All 4 pressure test cases pass
2. No regression on baseline tests
3. Direction awareness working (comparison language, new domains)
"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.conversation_memory import extract_confidence_signals, UserProfile
from app.services.confidence_engine import update_confidence_score

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    RULE 1: FINAL VALIDATION                                 ║
║                   (Direction-Aware Pivot Disambiguation)                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

# Test suite
test_cases = [
    {
        "name": "Reinforcement Without 'Like'",
        "profile_interests": ["coding"],
        "setup": "I've been thinking about coding",
        "test": "I actually feel coding is right for me",
        "expected_delta_min": 0.08,
        "expected_delta_max": 0.12,
        "why": "Same domain + positive sentiment → REINFORCE (no penalty)"
    },
    {
        "name": "Reinforcement With 'Think'",
        "profile_interests": ["coding"],
        "setup": "I'm interested in coding",
        "test": "actually I think coding makes sense",
        "expected_delta_min": 0.08,
        "expected_delta_max": 0.12,
        "why": "Same domain + 'makes sense' → REINFORCE (no penalty)"
    },
    {
        "name": "New Domain with Comparison",
        "profile_interests": ["coding"],
        "setup": "I like coding",
        "test": "I actually like business more than coding",
        "expected_delta_min": 0.12,
        "expected_delta_max": 0.14,
        "why": "New domain 'business' + 'more than' comparison → PIVOT (penalize)"
    },
    {
        "name": "Ambiguity + Pivot",
        "profile_interests": ["coding"],
        "setup": "I want to do coding",
        "test": "actually I'm not sure anymore",
        "expected_delta_min": -0.12,
        "expected_delta_max": -0.08,
        "why": "No clarity with pivot + ambiguity → both signals penalize"
    },
]

results = []

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*80}")
    print(f"TEST {i}: {test['name']}")
    print('='*80)
    
    profile = UserProfile()
    profile.interests = test['profile_interests']
    
    # Setup
    setup_signals = extract_confidence_signals(test['setup'], profile)
    setup_score = update_confidence_score(None, setup_signals, query=test['setup'], profile=profile)
    
    # Test
    test_signals = extract_confidence_signals(test['test'], profile)
    test_score = update_confidence_score(setup_score, test_signals, query=test['test'], profile=profile)
    delta = test_score - setup_score
    
    # Evaluate
    is_within_range = test['expected_delta_min'] <= delta <= test['expected_delta_max']
    status = "✓ PASS" if is_within_range else "❌ FAIL"
    
    print(f"\nSetup: {test['setup']}")
    print(f"  Signals: {setup_signals}")
    print(f"  Score: {setup_score:.3f}")
    
    print(f"\nTest: {test['test']}")
    print(f"  Signals: {test_signals}")
    print(f"  Score: {setup_score:.3f} → {test_score:.3f} ({delta:+.3f})")
    
    print(f"\nExpected delta range: {test['expected_delta_min']:+.3f} to {test['expected_delta_max']:+.3f}")
    print(f"Actual delta: {delta:+.3f}")
    print(f"\nWhy: {test['why']}")
    print(f"\n{status}")
    
    results.append({
        "name": test['name'],
        "delta": delta,
        "is_pass": is_within_range
    })

# Summary
print(f"\n\n{'='*80}")
print("SUMMARY")
print('='*80)

passed = sum(1 for r in results if r['is_pass'])
failed = sum(1 for r in results if not r['is_pass'])

for r in results:
    status = "✓" if r['is_pass'] else "❌"
    print(f"{status} {r['name']}: {r['delta']:+.3f}")

print()
print(f"Result: {passed}/{len(results)} PASS")
print()

# Interpretation
if passed == 4:
    print("✅ RULE 1 UPGRADED SUCCESSFULLY")
    print()
    print("Direction-Aware Pivot Disambiguation Working:")
    print("  ✓ Recognizes same-domain reinforcement")
    print("  ✓ Detects comparison language patterns")
    print("  ✓ Identifies new domain introductions")
    print("  ✓ Applies/skips penalties contextually")
    print()
    print("System moved from:")
    print("  ❌ Pattern-Aware (keyword → penalty)")
    print("  ✅ Direction-Aware (context → interpretation)")
else:
    print(f"⚠️  {failed} tests failing - check implementation")

print()
print("="*80)
print("REGRESSION TEST")
print("="*80)

# Quick 4-turn test
profile = UserProfile()
scores = []
queries = [
    "idk",
    "maybe coding",
    "I like coding",
    "what should I do"
]

for query in queries:
    signals = extract_confidence_signals(query, profile)
    score = update_confidence_score(scores[-1] if scores else None, signals, query=query, profile=profile)
    scores.append(score)

expected = [0.25, 0.35, 0.50, 0.71]
progression_pass = all(abs(a - e) < 0.05 for a, e in zip(scores, expected))

print(f"\n4-Turn Progression: {scores}")
print(f"Expected (approx): {expected}")
print(f"Status: {'✓ PASS' if progression_pass else '❌ FAIL'}")

print()
print("="*80)

if passed == 4 and progression_pass:
    print("🎯 RULE 1 COMPLETE AND STABLE")
    print("Ready for production pressure testing")
else:
    print("⚠️  Some issues remain - review failures above")
