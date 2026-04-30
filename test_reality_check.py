#!/usr/bin/env python3
"""
Reality check: Can the system handle the messy progression?

User: idk → maybe coding → I like coding → what should I do 
     → actually I hate coding → maybe business → I want business

Expected: 0.25 → 0.35 → 0.50 → 0.71 → 0.50 → 0.55 → 0.70
"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.confidence_engine import update_confidence_score

scenarios = [
    (1, "idk", ["ambiguity"], 0.25),
    (2, "maybe coding", ["weak_clarity"], 0.35),
    (3, "I like coding", ["weak_clarity", "weak_clarity"], 0.50),
    (4, "what should I do", ["decision_request", "strong_clarity"], 0.71),
    (5, "actually I hate coding", ["contradiction"], 0.50),
    (6, "maybe business", ["weak_clarity"], 0.55),
    (7, "I want business", ["strong_clarity"], 0.70),
]

print("="*80)
print("REALITY CHECK: Messy Progression Test")
print("="*80)
print()

score = None
results = []

for turn, statement, signals, expected in scenarios:
    score = update_confidence_score(score, signals)
    delta = score - results[-1][1] if results else 0
    
    # Check if within tolerance (±0.05)
    is_pass = abs(score - expected) <= 0.05
    status = "✓" if is_pass else "✗"
    
    results.append((turn, score, expected, is_pass))
    
    print(f"Turn {turn}: {statement}")
    print(f"  signals:  {signals}")
    print(f"  expected: {expected:.2f}")
    print(f"  actual:   {score:.2f}  {status}")
    if not is_pass:
        print(f"  ERROR: off by {abs(score - expected):+.2f}")
    print()

print("="*80)
print("SUMMARY")
print("="*80)
print("Turn | Statement                   | Expected | Actual | Status")
print("-" * 80)

for turn, actual, expected, is_pass in results:
    status = "✓ PASS" if is_pass else "✗ FAIL"
    print(f"  {turn}  | {scenarios[turn-1][1]:25} | {expected:.2f}    | {actual:.2f}  | {status}")

all_pass = all(r[3] for r in results)
print()
print(f"Overall: {'✅ PASS' if all_pass else '❌ FAIL'}")
print()

if all_pass:
    print("System confirmed: Handles explore→build→decide→doubt→rebuild naturally")
else:
    print("System mismatch: See failures above")
