"""
Test confidence recovery after disruption.

8-turn sequence: build → disrupt → recover → decide
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.conversation_memory import (
    get_memory_store,
    extract_user_profile,
)
from app.services.confidence_engine import update_confidence_score


def test_recovery_sequence():
    """
    Test confidence recovery dynamics.
    
    Sequence:
    1. "idk"
    2. "maybe coding"
    3. "I like coding"
    4. "what should I do?"
    5. "actually I hate coding"
    6. "maybe business?"
    7. "yeah business seems better"
    8. "what should I do now?"
    """
    memory = get_memory_store()
    session_id = "test_recovery"
    memory.clear_session(session_id)
    
    print("\n" + "="*80)
    print("CONFIDENCE RECOVERY SEQUENCE TEST")
    print("="*80)
    
    queries = [
        "idk",
        "maybe coding",
        "I like coding",
        "what should I do?",
        "actually I hate coding",
        "maybe business?",
        "yeah business seems better",
        "what should I do now?"
    ]
    
    prev_score = None
    for i, query in enumerate(queries, 1):
        profile = memory.get_profile(session_id)
        signals = extract_user_profile(query, profile)
        
        # Calculate delta manually for display
        conf_signals = signals.get('confidence_signals', [])
        if conf_signals:
            new_score = update_confidence_score(
                prev_score if prev_score is not None else profile.confidence_score,
                conf_signals,
                query=query,
                profile=profile
            )
            delta = new_score - (prev_score if prev_score is not None else profile.confidence_score)
        else:
            delta = 0.0
            new_score = profile.confidence_score
        
        profile_after = memory.update_profile(session_id, signals, query)
        score = profile_after.confidence_score
        
        print(f"\nTurn {i}: \"{query}\"")
        print(f"  Signals: {conf_signals}")
        print(f"  Delta: {delta:+.3f}")
        print(f"  Score: {score:.3f}")
        if i >= 5:
            print(f"  Turn history (last 3): {profile_after.confidence_signal_history[-3:]}")
        
        prev_score = score


if __name__ == "__main__":
    test_recovery_sequence()
