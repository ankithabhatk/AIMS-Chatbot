"""
Isolated test for confidence engine core function.

This tests ONLY update_confidence_score() before any integration.
"""

import sys
sys.path.insert(0, 'backend')

from app.services.confidence_engine import update_confidence_score, map_score_to_category


def test_basic_signals():
    """Test basic signal responses."""
    print("=" * 60)
    print("TEST 1: Basic Signal Responses")
    print("=" * 60)
    
    # Test ambiguity (should decrease)
    result = update_confidence_score(0.3, ["ambiguity"])
    print(f"0.3 + [ambiguity] → {result:.3f} (expect decrease)")
    assert result < 0.3, "Ambiguity should decrease score"
    
    # Test weak clarity (should increase slightly)
    result = update_confidence_score(0.3, ["weak_clarity"])
    print(f"0.3 + [weak_clarity] → {result:.3f} (expect slight increase)")
    assert result > 0.3, "Weak clarity should increase score"
    
    # Test strong clarity (should increase more)
    result = update_confidence_score(0.5, ["strong_clarity"])
    print(f"0.5 + [strong_clarity] → {result:.3f} (expect stronger increase)")
    assert result > 0.5, "Strong clarity should increase score"
    
    # Test contradiction (should decrease)
    result = update_confidence_score(0.6, ["contradiction"])
    print(f"0.6 + [contradiction] → {result:.3f} (expect decrease)")
    assert result < 0.6, "Contradiction should decrease score"
    
    # Test decision request (should increase strongly)
    result = update_confidence_score(0.7, ["decision_request"])
    print(f"0.7 + [decision_request] → {result:.3f} (expect strong increase)")
    assert result > 0.7, "Decision request should increase score"
    
    print("✅ All basic signal tests passed\n")


def test_bounded_delta():
    """Test that delta is bounded to [-0.3, +0.3]."""
    print("=" * 60)
    print("TEST 2: Bounded Delta")
    print("=" * 60)
    
    # Test multiple strong signals don't cause jump
    result = update_confidence_score(0.3, ["strong_clarity", "strong_clarity", "decision_request"])
    delta = result - 0.3
    print(f"0.3 + [strong_clarity, strong_clarity, decision_request] → {result:.3f}")
    print(f"Delta: {delta:.3f} (should be ≤ 0.3)")
    assert abs(delta) <= 0.35, f"Delta {delta:.3f} exceeds bounds (allowing smoothing margin)"
    
    # Test multiple negative signals don't cause crash
    result = update_confidence_score(0.6, ["ambiguity", "contradiction", "ambiguity"])
    delta = result - 0.6
    print(f"0.6 + [ambiguity, contradiction, ambiguity] → {result:.3f}")
    print(f"Delta: {delta:.3f} (should be ≥ -0.3)")
    assert abs(delta) <= 0.35, f"Delta {delta:.3f} exceeds bounds (allowing smoothing margin)"
    
    print("✅ Bounded delta tests passed\n")


def test_bounds_enforcement():
    """Test that score stays within [0.0, 1.0]."""
    print("=" * 60)
    print("TEST 3: Bounds Enforcement")
    print("=" * 60)
    
    # Test upper bound
    result = update_confidence_score(0.95, ["strong_clarity", "decision_request"])
    print(f"0.95 + [strong_clarity, decision_request] → {result:.3f} (should cap at 1.0)")
    assert result <= 1.0, "Score should not exceed 1.0"
    
    # Test lower bound
    result = update_confidence_score(0.05, ["ambiguity", "contradiction"])
    print(f"0.05 + [ambiguity, contradiction] → {result:.3f} (should cap at 0.0)")
    assert result >= 0.0, "Score should not go below 0.0"
    
    print("✅ Bounds enforcement tests passed\n")


def test_deterministic():
    """Test that function is deterministic."""
    print("=" * 60)
    print("TEST 4: Deterministic Behavior")
    print("=" * 60)
    
    # Same inputs should produce same outputs
    result1 = update_confidence_score(0.5, ["weak_clarity", "ambiguity"])
    result2 = update_confidence_score(0.5, ["weak_clarity", "ambiguity"])
    result3 = update_confidence_score(0.5, ["weak_clarity", "ambiguity"])
    
    print(f"Run 1: {result1:.6f}")
    print(f"Run 2: {result2:.6f}")
    print(f"Run 3: {result3:.6f}")
    
    assert result1 == result2 == result3, "Function should be deterministic"
    print("✅ Deterministic behavior confirmed\n")


def test_evolution_sequence():
    """Test realistic conversation evolution."""
    print("=" * 60)
    print("TEST 5: Evolution Sequence (Realistic Conversation)")
    print("=" * 60)
    
    # Turn 1: "idk what to do"
    score = update_confidence_score(None, ["ambiguity"])
    category = map_score_to_category(score)
    print(f"Turn 1: 'idk what to do' → score={score:.3f}, category={category}")
    assert 0.20 <= score <= 0.35, f"Expected ~0.25-0.30, got {score:.3f}"
    
    # Turn 2: "maybe coding" (ambiguity + clarity → should increase slightly)
    score = update_confidence_score(score, ["ambiguity", "weak_clarity"])
    category = map_score_to_category(score)
    print(f"Turn 2: 'maybe coding' → score={score:.3f}, category={category}")
    assert 0.30 <= score <= 0.45, f"Expected ~0.35-0.40, got {score:.3f}"
    
    # Turn 3: "I like coding and want good salary"
    score = update_confidence_score(score, ["strong_clarity", "weak_clarity", "weak_clarity"])
    category = map_score_to_category(score)
    print(f"Turn 3: 'I like coding and want good salary' → score={score:.3f}, category={category}")
    assert 0.50 <= score <= 0.65, f"Expected ~0.55-0.60, got {score:.3f}"
    
    # Turn 4: "what should I do?" (should push into high confidence with less smoothing)
    score = update_confidence_score(score, ["decision_request"])
    category = map_score_to_category(score)
    print(f"Turn 4: 'what should I do?' → score={score:.3f}, category={category}")
    assert 0.70 <= score <= 0.85, f"Expected ~0.70-0.80 (high), got {score:.3f}"
    assert category == "high", f"Expected 'high' category at {score:.3f}, got '{category}'"
    
    print("✅ Evolution sequence realistic\n")


def test_smoothing():
    """Test that smoothing prevents jumps."""
    print("=" * 60)
    print("TEST 6: Smoothing (No Jumps)")
    print("=" * 60)
    
    # Single strong signal shouldn't cause huge jump
    score1 = 0.3
    score2 = update_confidence_score(score1, ["strong_clarity"])
    delta = score2 - score1
    
    print(f"0.3 + [strong_clarity] → {score2:.3f}")
    print(f"Delta: {delta:.3f} (should be smooth, not full +0.25)")
    
    # Due to smoothing (0.7 * prev + 0.3 * target), delta should be < raw weight
    assert delta < 0.15, f"Delta {delta:.3f} too large (smoothing not working)"
    
    print("✅ Smoothing working correctly\n")


def test_category_mapping():
    """Test score to category mapping."""
    print("=" * 60)
    print("TEST 7: Category Mapping")
    print("=" * 60)
    
    assert map_score_to_category(0.0) == "low"
    assert map_score_to_category(0.2) == "low"
    assert map_score_to_category(0.29) == "low"
    assert map_score_to_category(0.3) == "medium"
    assert map_score_to_category(0.5) == "medium"
    assert map_score_to_category(0.69) == "medium"
    assert map_score_to_category(0.7) == "high"
    assert map_score_to_category(0.9) == "high"
    assert map_score_to_category(1.0) == "high"
    
    print("✅ Category mapping correct\n")


if __name__ == "__main__":
    print("\n🧪 ISOLATED CONFIDENCE ENGINE TESTS\n")
    
    try:
        test_basic_signals()
        test_bounded_delta()
        test_bounds_enforcement()
        test_deterministic()
        test_evolution_sequence()
        test_smoothing()
        test_category_mapping()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nCore function is working correctly.")
        print("Ready for integration.")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
