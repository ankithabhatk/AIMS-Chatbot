#!/usr/bin/env python3
"""
DEBUG: Add instrumentation to see what's happening inside update_confidence_score
"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.conversation_memory import UserProfile

def debug_update_confidence_score(prev_score, signals, query=None, profile=None):
    """Copy of update_confidence_score with debug output"""
    
    print(f"\n>>> DEBUG update_confidence_score")
    print(f"    prev_score={prev_score}, signals={signals}")
    print(f"    query={query}")
    print(f"    profile.interests={profile.interests if profile else None}")
    print()
    
    if prev_score is None:
        prev_score = 0.3
    
    # COUNT SIGNALS
    weak_clarity_count = signals.count("weak_clarity")
    strong_clarity_count = signals.count("strong_clarity")
    ambiguity_count = signals.count("ambiguity")
    contradiction_count = signals.count("contradiction")
    pivot_count = signals.count("pivot")
    negative_sentiment_count = signals.count("negative_sentiment")
    decision_request_present = "decision_request" in signals
    
    print(f"Signal counts:")
    print(f"  weak_clarity: {weak_clarity_count}")
    print(f"  strong_clarity: {strong_clarity_count}")
    print(f"  pivot: {pivot_count}")
    print()
    
    raw_delta = 0.0
    
    # NO CONTRADICTION path
    if contradiction_count == 0:
        print("Path: NO CONTRADICTION")
        
        # Weak clarity
        if weak_clarity_count == 1:
            raw_delta += 0.20
            print(f"  weak_clarity (1): raw_delta += 0.20 → {raw_delta}")
        
        # Strong clarity
        if strong_clarity_count == 1:
            raw_delta += 0.35
            print(f"  strong_clarity (1): raw_delta += 0.35 → {raw_delta}")
        
        # PIVOT HANDLING
        if pivot_count > 0:
            print(f"  Pivot detected (count={pivot_count})")
            
            if query and (strong_clarity_count > 0 or weak_clarity_count > 0):
                print(f"    Pivot + clarity present, checking direction...")
                
                # Check pivot logic
                from app.services.confidence_engine import _is_reinforcing_pivot
                is_reinforcing = _is_reinforcing_pivot(query, profile)
                print(f"    _is_reinforcing_pivot() = {is_reinforcing}")
                
                if is_reinforcing:
                    print(f"    → SKIP penalty (reinforcement)")
                else:
                    raw_delta -= 0.1
                    print(f"    → APPLY penalty: raw_delta -= 0.1 → {raw_delta}")
            else:
                raw_delta -= 0.1
                print(f"  No query or clarity: raw_delta -= 0.1 → {raw_delta}")
        
        print(f"\nFinal raw_delta: {raw_delta}")
        
    return prev_score + raw_delta  # Simplified for debug

# Test
profile = UserProfile()
profile.interests = ["coding"]

query = "I actually feel coding is right for me"
signals = ["pivot", "weak_clarity"]
prev_score = 0.4

result = debug_update_confidence_score(prev_score, signals, query=query, profile=profile)
print(f"\n=== RESULT ===")
print(f"Score: {prev_score} → {result:.3f} ({result - prev_score:+.3f})")
