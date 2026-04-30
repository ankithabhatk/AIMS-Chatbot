#!/usr/bin/env python3
"""
Test 4-turn sequence: Verify signal amplification fix
Run this to see if Turn 3+ now reaches the target progression
"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.confidence_engine import update_confidence_score

# Test progression
print("="*80)
print("4-TURN CONFIDENCE PROGRESSION TEST")
print("="*80)

# Turn 1: New user with ambiguity
print("\nTurn 1:")
signals_1 = ["ambiguity"]
score_1 = update_confidence_score(None, signals_1)
print(f"signals: {signals_1}")
print(f"score: {score_1:.3f}")
print(f"target: ~0.25")
print(f"status: {'✓' if 0.20 <= score_1 <= 0.30 else '✗'}")

# Turn 2: Single weak clarity signal
print("\nTurn 2:")
signals_2 = ["weak_clarity"]
score_2 = update_confidence_score(score_1, signals_2)
print(f"signals: {signals_2}")
print(f"score: {score_2:.3f}")
print(f"target: ~0.35–0.40")
print(f"status: {'✓' if 0.33 <= score_2 <= 0.42 else '✗'}")

# Turn 3: MULTIPLE weak clarity signals (amplified)
print("\nTurn 3:")
signals_3 = ["weak_clarity", "weak_clarity"]
score_3 = update_confidence_score(score_2, signals_3)
print(f"signals: {signals_3}")
print(f"score: {score_3:.3f}")
print(f"target: ~0.50–0.55")
print(f"status: {'✓' if 0.48 <= score_3 <= 0.56 else '✗'}")

# Turn 4: Decision request with strong clarity
print("\nTurn 4:")
signals_4 = ["decision_request", "strong_clarity"]
score_4 = update_confidence_score(score_3, signals_4)
print(f"signals: {signals_4}")
print(f"score: {score_4:.3f}")
print(f"target: ≥0.70")
print(f"status: {'✓' if score_4 >= 0.70 else '✗'}")

print("\n" + "="*80)
print("SEQUENCE SUMMARY")
print("="*80)
print(f"Turn 1: {score_1:.3f}")
print(f"Turn 2: {score_2:.3f}")
print(f"Turn 3: {score_3:.3f}")
print(f"Turn 4: {score_4:.3f}")
print()
print(f"Overall: {'PASS' if all([
    0.20 <= score_1 <= 0.30,
    0.33 <= score_2 <= 0.42,
    0.48 <= score_3 <= 0.56,
    score_4 >= 0.70
]) else 'FAIL'}")
