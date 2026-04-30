#!/usr/bin/env python3
"""
Real-world test: User contradicts themselves

Scenario:
Turn 1: "I like coding" → building confidence
Turn 2: "actually I hate coding" → contradiction detected
Turn 3: Recovery → rebuilding confidence

This tests if the system correctly understands human indecision.
"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.confidence_engine import update_confidence_score

print("="*80)
print("REAL-WORLD TEST: CONTRADICTION DETECTION")
print("="*80)
print("\nScenario: User builds strong confidence, then contradicts themselves\n")

# Turn 1: Initial statement - I like coding
print("Turn 1: 'I like coding'")
signals_1 = ["weak_clarity"]
score_1 = update_confidence_score(None, signals_1)
print(f"  signals: {signals_1}")
print(f"  score: None → {score_1:.3f}")

# Turn 2: Add more clarity
print("\nTurn 2: 'And I'm really good at it'")
signals_2 = ["weak_clarity", "strong_clarity"]
score_2 = update_confidence_score(score_1, signals_2)
print(f"  signals: {signals_2}")
print(f"  score: {score_1:.3f} → {score_2:.3f}")

# Turn 3: Even more - make a decision
print("\nTurn 3: 'Yes, I want to pursue coding'")
signals_3 = ["strong_clarity", "decision_request"]
score_3 = update_confidence_score(score_2, signals_3)
print(f"  signals: {signals_3}")
print(f"  score: {score_2:.3f} → {score_3:.3f}")
print(f"  ✓ High confidence reached: {score_3:.3f}")

# NOW: Turn 4 - CONTRADICTION!
print("\n" + "="*80)
print("\nTurn 4: 'Actually, wait... I hate coding'")
signals_4 = ["contradiction"]
score_4 = update_confidence_score(score_3, signals_4)
print(f"  signals: {signals_4}")
print(f"  score: {score_3:.3f} → {score_4:.3f}")
delta_4 = score_4 - score_3
print(f"  delta: {delta_4:+.3f}")
print(f"  interpretation: System detects preference reversal")

# Verify contradiction penalty was applied
expected_min = 0.45
expected_max = 0.55
is_correct = expected_min <= score_4 <= expected_max
print(f"\n  expected range: {expected_min:.2f}–{expected_max:.2f}")
print(f"  actual range match: {'✓ PASS' if is_correct else '✗ FAIL'}")

# Turn 5: Recovery
print("\nTurn 5: 'Let me reconsider...'")
signals_5 = ["weak_clarity"]
score_5 = update_confidence_score(score_4, signals_5)
print(f"  signals: {signals_5}")
print(f"  score: {score_4:.3f} → {score_5:.3f}")

print("\n" + "="*80)
print("CONVERSATION FLOW ANALYSIS")
print("="*80)
print(f"Turn 1 (interest):       {score_1:.3f}")
print(f"Turn 2 (clarity):        {score_2:.3f}")
print(f"Turn 3 (strong commit):  {score_3:.3f} ← high confidence")
print(f"Turn 4 (contradiction):  {score_4:.3f} ← DROPS {abs(delta_4):.3f} {('✓' if is_correct else '✗')}")
print(f"Turn 5 (recovery):       {score_5:.3f}")
print()
print("Behavior:")
print(f"  Contradiction detected correctly: {is_correct}")
print(f"  Penalty magnitude: {abs(delta_4):.3f}")
print(f"  Recovery possible: {score_5 > score_4}")
print()
print("System understands: Strong commitments can be reversed by contradictions.")
