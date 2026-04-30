#!/usr/bin/env python3
"""
PRESSURE TEST: Three Structural Edge Cases

Not looking for correctness. Looking for plausibility.

Test 1: Signal Collision
Test 2: False Pivot  
Test 3: Emotional vs Logical Conflict

Plus 5 additional real-world messy inputs.
"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.conversation_memory import extract_confidence_signals, UserProfile
from app.services.confidence_engine import update_confidence_score, map_score_to_category

def test_scenario(name, queries_with_context):
    """Run a scenario and show behavior."""
    print(f"\n{'='*80}")
    print(f"PRESSURE TEST: {name}")
    print(f"{'='*80}")
    
    profile = UserProfile()
    score = None
    
    for query, context in queries_with_context:
        signals = extract_confidence_signals(query, profile)
        prev_score = score
        score = update_confidence_score(score, signals)
        category = map_score_to_category(score)
        delta = score - prev_score if prev_score is not None else 0
        
        print(f"\nQuery: '{query}'")
        print(f"Context: {context}")
        print(f"Signals: {signals}")
        
        if prev_score is not None:
            direction = "↑ UP" if delta > 0 else "↓ DOWN" if delta < 0 else "→ FLAT"
            print(f"Score: {prev_score:.3f} → {score:.3f} ({delta:+.3f}) {direction}")
        else:
            print(f"Score: None → {score:.3f}")
        
        print(f"Category: {category}")
        
        # Analysis
        if "strong_clarity" in signals and "negative_sentiment" in signals:
            print("⚠️  SIGNAL COLLISION: clarity + negative sentiment")
        if "pivot" in signals and "strong_clarity" in signals and delta > 0:
            print("⚠️  FALSE PIVOT: 'actually' with upward movement")
        if "strong_clarity" in signals and "negative_sentiment" in signals and delta > 0:
            print("🤔 INTERESTING: goal clarity + fear but score went up")

# PRESSURE TEST 1: Signal Collision
test_scenario(
    "Signal Collision - Mixed Sentiment",
    [
        ("I like coding but it's stressful and maybe not for me", 
         "Multiple conflicting signals: clarity + negative + ambiguity")
    ]
)

# PRESSURE TEST 2: False Pivot
test_scenario(
    "False Pivot - 'Actually' as Reinforcement",
    [
        ("I like coding", "Building initial interest"),
        ("I actually like coding more now", "Reinforcement, not reversal - 'actually' is confirmatory here")
    ]
)

# PRESSURE TEST 3: Emotional vs Logical Conflict  
test_scenario(
    "Emotional vs Logical Conflict",
    [
        ("I want to do coding", "Goal clarity"),
        ("But I feel it's too hard", "Emotional resistance"),
        ("I want to do coding but I feel it's too hard", "Combined statement")
    ]
)

# ADDITIONAL REAL-WORLD INPUTS
test_scenario(
    "Real-World Messy Input #1",
    [
        ("idk bro coding seems cool but also scary", 
         "Ambiguity + interest + fear")
    ]
)

test_scenario(
    "Real-World Messy Input #2",
    [
        ("wait maybe business is better idk", 
         "Pause + pivot + ambiguity")
    ]
)

test_scenario(
    "Real-World Messy Input #3",
    [
        ("i like coding but not studying",
         "Interest in one aspect but negative on another")
    ]
)

test_scenario(
    "Real-World Messy Input #4",
    [
        ("actually yeah coding is good",
         "'Actually' + reinforcement, not pivot away")
    ]
)

test_scenario(
    "Real-World Messy Input #5",
    [
        ("this is confusing now",
         "Return to ambiguity after clarity")
    ]
)

print(f"\n{'='*80}")
print("OBSERVATIONS")
print(f"{'='*80}")
print("""
✓ System behavior under signal collisions:
  - Does mixed sentiment cause reasonable fluctuation or noise?
  
✓ False pivot detection:
  - Does 'actually' always pivot or does it sometimes reinforce?
  
✓ Emotional vs logical:
  - Does internal conflict register as moderate change or collapse?

✓ Real human language:
  - Do actual messy inputs show sensible score movement?
  - Do signals capture what the user is actually expressing?

Check above for plausibility, not correctness.
""")
