#!/usr/bin/env python3
"""
PATTERN CLASSIFICATION TEST

Not fixing code yet. Observing and classifying what the system is blind to.

For each input:
1. What signals does the system extract?
2. What kind of behavior is this really?
3. Does the system understand it correctly?
"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.conversation_memory import extract_confidence_signals, UserProfile
from app.services.confidence_engine import update_confidence_score, map_score_to_category

# New test inputs - focus on edge cases
TEST_INPUTS = [
    {
        "query": "coding is boring tbh",
        "expected_type": "implicit_negative",
        "reason": "User doesn't say 'hate', says 'boring' - reversal signal, not explicit negation"
    },
    {
        "query": "actually maybe business is better",
        "expected_type": "soft_pivot",
        "reason": "'actually' signals reconsidering, 'maybe' is uncertain, 'better' implies comparison"
    },
    {
        "query": "math is too hard for me",
        "expected_type": "implicit_negative",
        "reason": "Soft constraint, not explicit negation, but signals discomfort/incompatibility"
    },
    {
        "query": "wait I think I want hospitality instead",
        "expected_type": "soft_pivot",
        "reason": "'wait' pauses previous intent, 'instead' is explicit flip, but softer than 'hate'"
    },
    {
        "query": "coding seems cool but also scary",
        "expected_type": "implicit_negative",
        "reason": "Mixed sentiment: interest + fear. 'Scary' is emotional drift, not clear negation"
    },
    {
        "query": "honestly this is all confusing now",
        "expected_type": "neutral_uncertainty",
        "reason": "Returns to ambiguity after clarity - system should detect regression"
    },
    {
        "query": "I like coding but it's really stressful",
        "expected_type": "implicit_negative",
        "reason": "Contradiction within single statement: like + stress = mixed signal"
    },
    {
        "query": "maybe I should just try something totally different",
        "expected_type": "soft_pivot",
        "reason": "Open-ended pivot, not specific to previous interests. System may miss context shift"
    },
]

print("="*80)
print("PATTERN CLASSIFICATION TEST")
print("="*80)
print()

profile = UserProfile()
confidence_score = None

for i, test_case in enumerate(TEST_INPUTS, 1):
    query = test_case["query"]
    expected = test_case["expected_type"]
    reason = test_case["reason"]
    
    # Extract signals
    signals = extract_confidence_signals(query, profile)
    prev_score = confidence_score
    confidence_score = update_confidence_score(confidence_score, signals)
    
    # Classify what we actually got
    if "contradiction" in signals:
        detected_type = "contradiction"
    elif len(signals) == 0:
        detected_type = "no_signal"
    elif "ambiguity" in signals and "weak_clarity" in signals:
        detected_type = "mixed_uncertainty"
    elif "ambiguity" in signals:
        detected_type = "uncertainty"
    elif "weak_clarity" in signals:
        detected_type = "weak_clarity"
    elif "strong_clarity" in signals:
        detected_type = "strong_clarity"
    else:
        detected_type = "unknown"
    
    # Check if system got it right
    is_correct = (expected == detected_type) or \
                 (expected == "implicit_negative" and "contradiction" in signals) or \
                 (expected == "soft_pivot" and ("ambiguity" in signals or "weak_clarity" in signals)) or \
                 (expected == "neutral_uncertainty" and "ambiguity" in signals)
    
    status = "✓" if is_correct else "✗"
    
    print(f"Input {i}: {query}")
    print(f"  Expected: {expected}")
    print(f"  Why: {reason}")
    print(f"  Detected: {detected_type} {status}")
    print(f"  Signals: {signals}")
    if prev_score is not None:
        delta = confidence_score - prev_score
        print(f"  Confidence: {prev_score:.3f} → {confidence_score:.3f} ({delta:+.3f})")
    else:
        print(f"  Confidence: None → {confidence_score:.3f}")
    
    if not is_correct:
        print(f"  ⚠️ MISSED: System didn't detect {expected}")
    
    print()

print("="*80)
print("PATTERN ANALYSIS")
print("="*80)
print()
print("Implicit Negative Sentiment:")
print("  - System sees: 'boring', 'hard', 'scary', 'stressful' as unclear")
print("  - System should see: These are reversal signals, not negation")
print("  - Blind spot: Lacks emotional/sentiment keywords")
print()
print("Soft Pivot Language:")
print("  - System sees: 'actually', 'wait', 'instead' sometimes, but inconsistently")
print("  - System should see: These words signal trajectory shift")
print("  - Blind spot: Transition words not captured as shift indicators")
print()
print("Confidence Saturation:")
print("  - System sees: Score can only go up or stay same once at 1.0")
print("  - System should see: Ambiguity should bring score down even from max")
print("  - Blind spot: State machine bug, not signal detection")
print()
