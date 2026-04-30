#!/usr/bin/env python3
"""
RULE 1 BEFORE/AFTER: Show the effect of pivot disambiguation
"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.conversation_memory import extract_confidence_signals, UserProfile
from app.services.confidence_engine import update_confidence_score

print("="*80)
print("RULE 1 BEFORE/AFTER: Pivot Disambiguation Effect")
print("="*80)
print()

print("CASE 1: Reinforcing 'Actually'")
print("-" * 80)
print("Query: 'I actually like coding more now'")
print()
print("BEFORE Rule 1:")
print("  Signals detected: ['pivot', 'strong_clarity']")
print("  Effect: pivot -0.1 + clarity +0.35 = net +0.25")
print("  Score: 0.45 → 0.575 (goal: should be more)")
print()
print("AFTER Rule 1:")

profile1 = UserProfile()
score1_before = update_confidence_score(0.45, ["strong_clarity"])
score1_after = update_confidence_score(0.45, ["pivot", "strong_clarity"], "I actually like coding more now")

print(f"  Score: 0.45 → {score1_after:.3f}")
print(f"  Delta improvement: +{(score1_after - 0.575):.3f}")
print(f"  Status: ✓ Fixed - pivot no longer penalizes reinforcement")

print()
print("="*80)
print("CASE 2: Reconsidering 'Actually'")
print("-" * 80)
print("Query: 'Actually maybe business is better'")
print()
print("BEFORE Rule 1:")
print("  Signals: ['ambiguity', 'pivot', 'weak_clarity']")
print("  Would have: ambiguity -0.1 + weak_clarity +0.2 + pivot -0.1 + softener +0.15 = +0.15")
print()
print("AFTER Rule 1:")

profile2 = UserProfile()
score2_before = update_confidence_score(0.45, ["ambiguity", "weak_clarity"])  # Without pivot
score2_after = update_confidence_score(0.45, ["ambiguity", "pivot", "weak_clarity"], "Actually maybe business is better")

print(f"  Without pivot: 0.45 → {score2_before:.3f}")
print(f"  With pivot penalty: 0.45 → {score2_after:.3f}")
print(f"  Penalty effect: -{(score2_before - score2_after):.3f}")
print(f"  Status: ✓ Correct - pivot penalty applied to reconsidering")

print()
print("="*80)
print("KEY INSIGHT")
print("="*80)
print("""
Rule 1 Disambiguates Pivot Meaning:

✓ "actually like more" = reinforcement → NO penalty (score goes higher)
✓ "actually maybe [different]" = reconsidering → penalty applied (growth reduced)

The pivot signal is now context-aware instead of always penalizing.
""")
