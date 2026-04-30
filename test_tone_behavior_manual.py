"""
Manual tone behavior verification.

Verify that tone FEELS correct at different confidence levels:
- Turn 3 (0.525, medium) → practical/balanced
- Turn 4 (0.705, high) → decisive/directive
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.conversation_memory import (
    get_memory_store,
    extract_user_profile,
)
from app.services.counselor_handler import get_counselor_response


def test_tone_at_medium_confidence():
    """Test tone feels practical/balanced at medium confidence (0.525)."""
    memory = get_memory_store()
    session_id = "test_tone_medium"
    memory.clear_session(session_id)
    
    print("\n" + "="*80)
    print("TONE TEST: MEDIUM CONFIDENCE (Turn 3)")
    print("="*80)
    
    # Build to Turn 3
    queries = [
        "idk what to do",
        "maybe coding",
        "I like coding and want good salary"
    ]
    
    for query in queries:
        signals = extract_user_profile(query, memory.get_profile(session_id))
        memory.update_profile(session_id, signals)
    
    profile = memory.get_profile(session_id)
    print(f"\nConfidence Score: {profile.confidence_score:.3f}")
    print(f"Confidence Category: {profile.confidence_category}")
    print(f"Expected: ~0.525 (medium)")
    
    # Get response
    response = get_counselor_response("tell me more", session_id)
    
    if response and response.get('answer'):
        answer = response['answer']
        print(f"\n--- RESPONSE (first 500 chars) ---")
        print(answer[:500])
        print("...")
        
        answer_lower = answer.lower()
        
        # Check for balanced tone indicators
        balanced_indicators = [
            "practical", "here's", "consider", "path", "option",
            "i'd recommend", "based on what you've told me"
        ]
        has_balanced = any(ind in answer_lower for ind in balanced_indicators)
        
        # Should NOT have exploratory tone
        exploratory_indicators = ["unsure", "it's okay to feel", "no pressure"]
        has_exploratory = any(ind in answer_lower for ind in exploratory_indicators)
        
        # Should NOT have overly decisive tone
        overly_decisive = ["strongly", "clear goals", "i'd strongly recommend"]
        has_overly_decisive = any(ind in answer_lower for ind in overly_decisive)
        
        print(f"\n--- TONE ANALYSIS ---")
        print(f"Has balanced tone: {has_balanced}")
        print(f"Has exploratory tone: {has_exploratory}")
        print(f"Has overly decisive tone: {has_overly_decisive}")
        
        print(f"\n--- EXPECTED ---")
        print(f"✓ Balanced/practical tone")
        print(f"✗ NOT exploratory (too soft)")
        print(f"✗ NOT overly decisive (too strong)")
        
        if has_balanced and not has_exploratory and not has_overly_decisive:
            print(f"\n✅ TONE FEELS CORRECT: Practical/balanced")
            return True
        else:
            print(f"\n⚠️  TONE MISMATCH")
            return False
    
    return False


def test_tone_at_high_confidence():
    """Test tone feels decisive/directive at high confidence (0.705)."""
    memory = get_memory_store()
    session_id = "test_tone_high"
    memory.clear_session(session_id)
    
    print("\n" + "="*80)
    print("TONE TEST: HIGH CONFIDENCE (Turn 4)")
    print("="*80)
    
    # Build to Turn 4
    queries = [
        "idk what to do",
        "maybe coding",
        "I like coding and want good salary",
        "what should I do?"
    ]
    
    for query in queries:
        signals = extract_user_profile(query, memory.get_profile(session_id))
        memory.update_profile(session_id, signals)
    
    profile = memory.get_profile(session_id)
    print(f"\nConfidence Score: {profile.confidence_score:.3f}")
    print(f"Confidence Category: {profile.confidence_category}")
    print(f"Expected: ~0.705 (high)")
    
    # Get response (should be final recommendation)
    response = get_counselor_response(queries[-1], session_id)
    
    if response and response.get('answer'):
        answer = response['answer']
        print(f"\n--- RESPONSE (first 500 chars) ---")
        print(answer[:500])
        print("...")
        
        answer_lower = answer.lower()
        
        # Check for decisive tone indicators
        decisive_indicators = [
            "strongly", "clear", "i'd strongly recommend",
            "based on your clear goals", "here's what i'd strongly suggest"
        ]
        has_decisive = any(ind in answer_lower for ind in decisive_indicators)
        
        # Should NOT have exploratory tone
        exploratory_indicators = ["unsure", "it's okay to feel", "no pressure", "explore"]
        has_exploratory = any(ind in answer_lower for ind in exploratory_indicators)
        
        # Should have directive language
        directive_indicators = ["you should", "i recommend", "my recommendation", "here's the honest path"]
        has_directive = any(ind in answer_lower for ind in directive_indicators)
        
        print(f"\n--- TONE ANALYSIS ---")
        print(f"Has decisive tone: {has_decisive}")
        print(f"Has directive language: {has_directive}")
        print(f"Has exploratory tone: {has_exploratory}")
        
        print(f"\n--- EXPECTED ---")
        print(f"✓ Decisive/directive tone")
        print(f"✓ Clear recommendation")
        print(f"✗ NOT exploratory")
        
        if (has_decisive or has_directive) and not has_exploratory:
            print(f"\n✅ TONE FEELS CORRECT: Decisive/directive")
            return True
        else:
            print(f"\n⚠️  TONE MISMATCH")
            return False
    
    return False


if __name__ == "__main__":
    try:
        result1 = test_tone_at_medium_confidence()
        result2 = test_tone_at_high_confidence()
        
        print("\n" + "="*80)
        print("TONE BEHAVIOR VERIFICATION")
        print("="*80)
        print(f"Medium confidence (0.525): {'✅ CORRECT' if result1 else '❌ INCORRECT'}")
        print(f"High confidence (0.705): {'✅ CORRECT' if result2 else '❌ INCORRECT'}")
        
        if result1 and result2:
            print("\n✅ TONE LAYER IS TRULY FIXED")
            print("Tone correctly reflects confidence category at all levels.")
        else:
            print("\n⚠️  TONE LAYER NEEDS ADJUSTMENT")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
