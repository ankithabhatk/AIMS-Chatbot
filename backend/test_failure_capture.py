"""
Test Failure Capture Loop

This tests the 3 critical metrics:
1. Sentiment conflict tracking
2. Clarification response tracking
3. Locked → Apply dropoff tracking
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.counselor.production_analytics import (
    init_session, track_sentiment_conflict, track_clarification_response,
    track_locked_dropoff, get_analytics_dashboard, print_analytics_dashboard,
    ANALYTICS_STORE, analyze_sentiment_conflicts_by_outcome, 
    analyze_clarifications_by_outcome, analyze_locked_dropoffs_by_course
)

def test_sentiment_conflict_tracking():
    """Test sentiment conflict event logging"""
    print("\n" + "=" * 60)
    print("TEST 1: SENTIMENT CONFLICT TRACKING")
    print("=" * 60)
    
    session_id = "test_sentiment_001"
    init_session(session_id)
    
    # Test 1: Sentiment conflict without bypass → converted
    track_sentiment_conflict(session_id, "yeah but not sure", 0.75, "decision", bypassed=False, outcome="converted")
    
    # Test 2: Sentiment conflict with high confidence bypass → converted
    track_sentiment_conflict(session_id, "okay I guess", 0.95, "decision", bypassed=True, outcome="converted")
    
    # Test 3: Another conflict without bypass → dropped
    track_sentiment_conflict(session_id, "fine whatever", 0.70, "decision", bypassed=False, outcome="dropped")
    
    # Verify
    assert len(ANALYTICS_STORE["sentiment_conflicts"]) == 3
    assert ANALYTICS_STORE["metrics"]["sentiment_conflicts_total"] == 3
    assert ANALYTICS_STORE["metrics"]["sentiment_conflicts_bypassed"] == 1
    
    # Verify outcomes
    outcomes = analyze_sentiment_conflicts_by_outcome()
    assert outcomes["converted"] == 2
    assert outcomes["dropped"] == 1
    
    print("✅ Sentiment conflict tracking works!")
    print(f"   Total conflicts: {ANALYTICS_STORE['metrics']['sentiment_conflicts_total']}")
    print(f"   Bypassed: {ANALYTICS_STORE['metrics']['sentiment_conflicts_bypassed']}")
    print(f"   Converted: {outcomes['converted']}, Dropped: {outcomes['dropped']}")


def test_clarification_response_tracking():
    """Test clarification response tracking"""
    print("\n" + "=" * 60)
    print("TEST 2: CLARIFICATION RESPONSE TRACKING")
    print("=" * 60)
    
    session_id = "test_clarification_001"
    init_session(session_id)
    
    # Test 1: User responds to clarification → converted
    track_clarification_response(session_id, responded=True, turns_taken=1, outcome="converted")
    
    # Test 2: User responds after 2 turns → continued
    track_clarification_response(session_id, responded=True, turns_taken=2, outcome="continued")
    
    # Test 3: User drops off (no response)
    track_clarification_response(session_id, responded=False, turns_taken=None, outcome="dropped")
    
    # Verify
    assert len(ANALYTICS_STORE["clarification_responses"]) == 3
    assert ANALYTICS_STORE["metrics"]["clarification_responses_total"] == 3
    assert ANALYTICS_STORE["metrics"]["clarification_responses_responded"] == 2
    assert ANALYTICS_STORE["metrics"]["clarification_responses_dropped"] == 1
    
    # Verify outcomes
    outcomes = analyze_clarifications_by_outcome()
    assert outcomes["converted"] == 1
    assert outcomes["dropped"] == 1
    assert outcomes["continued"] == 1
    
    print("✅ Clarification response tracking works!")
    print(f"   Total responses: {ANALYTICS_STORE['metrics']['clarification_responses_total']}")
    print(f"   Responded: {ANALYTICS_STORE['metrics']['clarification_responses_responded']}")
    print(f"   Dropped: {ANALYTICS_STORE['metrics']['clarification_responses_dropped']}")
    print(f"   Converted: {outcomes['converted']}, Continued: {outcomes['continued']}, Dropped: {outcomes['dropped']}")


def test_locked_dropoff_tracking():
    """Test locked → apply dropoff tracking"""
    print("\n" + "=" * 60)
    print("TEST 3: LOCKED → APPLY DROPOFF TRACKING")
    print("=" * 60)
    
    session_id = "test_dropoff_001"
    init_session(session_id)
    
    # Test 1: User drops after locking BCA
    track_locked_dropoff(session_id, "BCA", turns_since_lock=3)
    
    # Test 2: User drops after locking BBA
    track_locked_dropoff(session_id, "BBA", turns_since_lock=5)
    
    # Verify
    assert len(ANALYTICS_STORE["locked_dropoffs"]) == 2
    assert ANALYTICS_STORE["metrics"]["locked_dropoffs_total"] == 2
    
    print("✅ Locked dropoff tracking works!")
    print(f"   Total dropoffs: {ANALYTICS_STORE['metrics']['locked_dropoffs_total']}")


def test_dashboard_metrics():
    """Test that dashboard shows failure capture metrics"""
    print("\n" + "=" * 60)
    print("TEST 4: DASHBOARD INTEGRATION")
    print("=" * 60)
    
    dashboard = get_analytics_dashboard()
    
    # Verify failure capture metrics exist
    assert "sentiment_conflict_rate" in dashboard
    assert "clarification_response_rate" in dashboard
    assert "locked_to_apply_rate" in dashboard
    assert "sentiment_conflicts_total" in dashboard
    assert "clarification_responses_total" in dashboard
    assert "locked_dropoffs_total" in dashboard
    
    print("✅ Dashboard integration works!")
    print(f"   Sentiment conflict rate: {dashboard['sentiment_conflict_rate']:.1f}%")
    print(f"   Clarification response rate: {dashboard['clarification_response_rate']:.1f}%")
    print(f"   Locked → Apply rate: {dashboard['locked_to_apply_rate']:.1f}%")


if __name__ == "__main__":
    print("\n🔥 TESTING FAILURE CAPTURE LOOP")
    print("=" * 60)
    
    # Clear analytics store
    ANALYTICS_STORE["sentiment_conflicts"] = []
    ANALYTICS_STORE["clarification_responses"] = []
    ANALYTICS_STORE["locked_dropoffs"] = []
    ANALYTICS_STORE["metrics"].clear()
    
    # Run tests
    test_sentiment_conflict_tracking()
    test_clarification_response_tracking()
    test_locked_dropoff_tracking()
    test_dashboard_metrics()
    
    print("\n" + "=" * 60)
    print("🎉 ALL FAILURE CAPTURE TESTS PASSED")
    print("=" * 60)
    
    # Show final dashboard
    print_analytics_dashboard()
