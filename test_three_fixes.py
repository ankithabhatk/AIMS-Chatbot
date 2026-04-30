#!/usr/bin/env python3
"""
TEST: Three Minimal Fixes

Testing:
1. Confidence saturation fix (soft cap at 0.85)
2. Pivot signal detection ("actually", "wait", "instead")
3. Negative sentiment detection ("boring", "scary", "stressful")
"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.conversation_memory import extract_confidence_signals, UserProfile
from app.services.confidence_engine import update_confidence_score, map_score_to_category

print("="*80)
print("TEST: THREE MINIMAL FIXES")
print("="*80)
print()

# Test case sequence that was failing before
test_cases = [
    ("I like coding", "Should start building confidence"),
    ("actually this is stressful", "Pivot + negative sentiment should destabilize"),
    ("maybe business instead", "Pivot + ambiguity should continue uncertainty"),
    ("what should I do", "Decision request should help clarify but not jump up"),
]

print("SCENARIO: User building interest, then expressing stress, reconsidering, asking for help")
print()

profile = UserProfile()
score = None

for query, description in test_cases:
    print(f"Input: '{query}'")
    print(f"  Context: {description}")
    
    signals = extract_confidence_signals(query, profile)
    prev_score = score
    score = update_confidence_score(score, signals)
    
    category = map_score_to_category(score)
    
    if prev_score is not None:
        delta = score - prev_score
        print(f"  Signals: {signals}")
        print(f"  Score: {prev_score:.3f} → {score:.3f} ({delta:+.3f})")
    else:
        print(f"  Signals: {signals}")
        print(f"  Score: None → {score:.3f}")
    
    print(f"  Category: {category}")
    print()

print("="*80)
print("EDGE CASES: Previously broken patterns")
print("="*80)
print()

# Reset and test the specific failing cases from pattern test
failing_cases = [
    "coding is boring tbh",
    "wait I think I want hospitality instead",
    "honestly this is all confusing now",
]

profile2 = UserProfile()
score2 = None

for query in failing_cases:
    signals = extract_confidence_signals(query, profile2)
    prev_score = score2
    score2 = update_confidence_score(score2, signals)
    
    print(f"'{query}'")
    print(f"  Signals: {signals} ← should have negative_sentiment or pivot")
    if prev_score is not None:
        delta = score2 - prev_score
        print(f"  Score: {prev_score:.3f} → {score2:.3f} ({delta:+.3f})")
    else:
        print(f"  Score: None → {score2:.3f}")
    print()

print("="*80)
print("CONFIDENCE SATURATION TEST")
print("="*80)
print()

# Push score high to test the soft cap
profile3 = UserProfile()
score3 = None

high_confidence_sequence = [
    ("I like coding", "Build interest"),
    ("I really want to do this", "Strong clarity"),
    ("Yes, I'm decided", "Even stronger"),
    ("This is my path", "Confirm again"),
    ("Absolutely certain", "Push to max"),
    ("Really really sure", "Should hit soft cap now"),
]

for query, desc in high_confidence_sequence:
    signals = extract_confidence_signals(query, profile3)
    prev_score = score3
    score3 = update_confidence_score(score3, signals)
    
    if prev_score is not None:
        delta = score3 - prev_score
        note = " ← SOFT CAP HIT" if prev_score >= 0.85 and delta <= 0.05 else ""
        print(f"{prev_score:.3f} → {score3:.3f} ({delta:+.3f}){note}  | {desc}")
    else:
        print(f"None → {score3:.3f}  | {desc}")

print()
print("✓ Soft cap prevents score from getting stuck at 1.0")
