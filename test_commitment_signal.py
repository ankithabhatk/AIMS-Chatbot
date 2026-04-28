#!/usr/bin/env python3
"""Test commitment signal detection - exploration vs decision"""

import requests
import json

API_URL = "http://localhost:8000/api/v1/chat"

# Test cases: exploration (should NOT lock) vs decision (should lock)
test_cases = [
    # EXPLORATION - should NOT lock
    {"query": "Tell me about BCA", "expect_lock": False, "type": "exploration"},
    {"query": "BCA vs BBA", "expect_lock": False, "type": "exploration"},
    {"query": "Which is better BCA or BBA?", "expect_lock": False, "type": "exploration"},
    {"query": "What about BCA?", "expect_lock": False, "type": "exploration"},
    {"query": "Compare BCA and MCA", "expect_lock": False, "type": "exploration"},
    
    # DECISION - should lock
    {"query": "I want to do BCA", "expect_lock": True, "type": "decision"},
    {"query": "I'll go with BCA", "expect_lock": True, "type": "decision"},
    {"query": "I choose BCA", "expect_lock": True, "type": "decision"},
    {"query": "I think BCA is good for me", "expect_lock": True, "type": "decision"},
    {"query": "I've decided on BCA", "expect_lock": True, "type": "decision"},
]

def test_query(query, session_id):
    """Test a single query and check if course was locked"""
    response = requests.post(
        API_URL,
        json={"query": query, "session_id": session_id},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        return {"error": f"HTTP {response.status_code}"}
    
    data = response.json()
    
    # Check logs to see if course was locked
    answer = data.get("answer", "")
    mode = data.get("mode", "")
    
    # Heuristic: if answer contains "locked" or mode is "counselor" with decision stage
    is_locked = "locked" in answer.lower()
    
    return {
        "mode": mode,
        "is_locked": is_locked,
        "answer_preview": answer[:80]
    }

def main():
    print("🧪 Testing Commitment Signal Detection\n")
    print("=" * 70)
    
    exploration_correct = 0
    exploration_total = 0
    decision_correct = 0
    decision_total = 0
    
    for i, test in enumerate(test_cases, 1):
        query = test["query"]
        expect_lock = test["expect_lock"]
        test_type = test["type"]
        session_id = f"test-commit-{i}"
        
        print(f"\n{i}. [{test_type.upper()}] '{query}'")
        
        result = test_query(query, session_id)
        
        if "error" in result:
            print(f"   ❌ ERROR: {result['error']}")
            continue
        
        is_locked = result["is_locked"]
        mode = result["mode"]
        
        # Check if result matches expectation
        if test_type == "exploration":
            exploration_total += 1
            if not is_locked:
                print(f"   ✅ CORRECT - Not locked (mode: {mode})")
                exploration_correct += 1
            else:
                print(f"   ❌ WRONG - Locked when shouldn't be")
                print(f"   Answer: {result['answer_preview']}...")
        else:  # decision
            decision_total += 1
            if is_locked:
                print(f"   ✅ CORRECT - Locked (mode: {mode})")
                decision_correct += 1
            else:
                print(f"   ❌ WRONG - Not locked when should be")
                print(f"   Answer: {result['answer_preview']}...")
    
    print("\n" + "=" * 70)
    print(f"\n📊 Results:")
    print(f"   Exploration: {exploration_correct}/{exploration_total} correct ({exploration_correct/exploration_total*100:.0f}% NOT locked)")
    print(f"   Decision: {decision_correct}/{decision_total} correct ({decision_correct/decision_total*100:.0f}% locked)")
    
    # Calculate comparison → lock rate
    comparison_lock_rate = (exploration_total - exploration_correct) / exploration_total * 100 if exploration_total > 0 else 0
    print(f"\n🎯 Comparison → Lock Rate: {comparison_lock_rate:.0f}%")
    print(f"   (Target: ~0%)")
    
    if exploration_correct == exploration_total and decision_correct == decision_total:
        print("\n🎉 PERFECT! All tests passed!")
        return 0
    else:
        print(f"\n⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    exit(main())
