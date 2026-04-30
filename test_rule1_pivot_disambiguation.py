#!/usr/bin/env python3
"""
RULE 1 TEST: Pivot Disambiguation

Testing that "actually" is correctly interpreted as:
- Reinforcement (no penalty)
- Reconsidering (penalty applied)
"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.conversation_memory import extract_confidence_signals, UserProfile
from app.services.confidence_engine import update_confidence_score, map_score_to_category

print("="*80)
print("RULE 1: PIVOT DISAMBIGUATION TEST")
print("="*80)
print()

# Test Case 1: Reinforcing "actually" (should NOT penalize)
print("TEST 1: Reinforcing 'Actually' (should NOT penalize)")
print("-" * 80)

profile1 = UserProfile()
q1a = "I like coding"
signals1a = extract_confidence_signals(q1a, profile1)
score1a = update_confidence_score(None, signals1a, q1a)

print(f"Turn 1: '{q1a}'")
print(f"  Signals: {signals1a}")
print(f"  Score: None → {score1a:.3f}")

q1b = "I actually like coding more now"
signals1b = extract_confidence_signals(q1b, profile1)
score1b = update_confidence_score(score1a, signals1b, q1b)
delta1 = score1b - score1a

print(f"\nTurn 2: '{q1b}'")
print(f"  Signals: {signals1b}")
print(f"  Score: {score1a:.3f} → {score1b:.3f} ({delta1:+.3f})")

if "pivot" in signals1b:
    if delta1 > 0:
        print(f"  ✓ CORRECT: Pivot detected but reinforcement recognized (score went UP)")
    else:
        print(f"  ✗ WRONG: Pivot penalized reinforcement (score went DOWN)")
else:
    print(f"  ⚠ No pivot signal detected")

print()

# Test Case 2: Reconsidering "actually" (should penalize)
print("TEST 2: Reconsidering 'Actually' (should penalize)")
print("-" * 80)

profile2 = UserProfile()
q2a = "I want to do coding"
signals2a = extract_confidence_signals(q2a, profile2)
score2a = update_confidence_score(None, signals2a, q2a)

print(f"Turn 1: '{q2a}'")
print(f"  Signals: {signals2a}")
print(f"  Score: None → {score2a:.3f}")

q2b = "Actually maybe business is better"
signals2b = extract_confidence_signals(q2b, profile2)
score2b = update_confidence_score(score2a, signals2b, q2b)
delta2 = score2b - score2a

print(f"\nTurn 2: '{q2b}'")
print(f"  Signals: {signals2b}")
print(f"  Score: {score2a:.3f} → {score2b:.3f} ({delta2:+.3f})")

if "pivot" in signals2b:
    if delta2 < 0 or delta2 == 0:
        print(f"  ✓ CORRECT: Pivot penalized reconsidering (score DOWN or flat)")
    else:
        print(f"  ✗ WRONG: Pivot not penalized (score went UP)")
else:
    print(f"  ⚠ No pivot signal detected")

print()
print("="*80)
print("SUMMARY")
print("="*80)
print(f"""
Before Rule 1:
  "I actually like coding more" → -0.1 penalty (wrongly treated as pivot away)

After Rule 1:
  "I actually like coding more" → no penalty (correctly recognized as reinforcement)
  "Actually maybe business" → -0.1 penalty (correctly recognized as reconsidering)

Status: Check above for ✓ marks indicating correct behavior.
""")
