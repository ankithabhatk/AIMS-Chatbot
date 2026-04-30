#!/usr/bin/env python3
"""
Real Conversation Test - Multi-turn decision synthesis

Tests the decision synthesis layer with a realistic 4-turn conversation:
1. User: I like coding
2. User: I'm weak in math
3. User: I want good salary
4. User: what should I do?

Expected: Final recommendation combining all signals with reasoning and trade-offs.
"""

import requests
import json
from typing import Dict

API_URL = "http://127.0.0.1:8000/api/v1/chat"
SESSION_ID = "test-decision-synthesis"


def send_query(query: str) -> Dict:
    """Send query to API and return response"""
    payload = {
        "query": query,
        "session_id": SESSION_ID,
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def print_turn(turn_num: int, query: str, response: Dict):
    """Print formatted turn output"""
    print(f"\n{'='*80}")
    print(f"TURN {turn_num}: {query}")
    print(f"{'='*80}")
    
    if "error" in response:
        print(f"❌ ERROR: {response['error']}")
        return
    
    intent = response.get("intent", "unknown")
    confidence = response.get("confidence", 0.0)
    answer = response.get("answer", "")
    
    print(f"Intent: {intent} | Confidence: {confidence:.2f}")
    print(f"\n{'-'*80}")
    print(f"ANSWER:")
    print(f"{'-'*80}")
    print(answer)
    print(f"{'-'*80}")


def run_conversation_test():
    """Run the 4-turn conversation test"""
    print("\n" + "="*80)
    print("🧠 DECISION SYNTHESIS TEST - 5-Turn Conversation with Conflict")
    print("="*80)
    print("\nTesting multi-turn memory + conflict resolution...")
    
    # Turn 1: Interest
    turn1_query = "I like coding"
    turn1_response = send_query(turn1_query)
    print_turn(1, turn1_query, turn1_response)
    
    # Turn 2: Constraint
    turn2_query = "I'm weak in math"
    turn2_response = send_query(turn2_query)
    print_turn(2, turn2_query, turn2_response)
    
    # Turn 3: Goal 1
    turn3_query = "I want good salary"
    turn3_response = send_query(turn3_query)
    print_turn(3, turn3_query, turn3_response)
    
    # Turn 4: Goal 2 (CONFLICT)
    turn4_query = "but I want a job quickly"
    turn4_response = send_query(turn4_query)
    print_turn(4, turn4_query, turn4_response)
    
    # Turn 5: Decision request
    turn5_query = "what should I do?"
    turn5_response = send_query(turn5_query)
    print_turn(5, turn5_query, turn5_response)
    
    # Verification
    print(f"\n\n{'='*80}")
    print("📊 VERIFICATION")
    print(f"{'='*80}\n")
    
    if "error" in turn5_response:
        print("❌ FAILED: API error")
        return False
    
    answer = turn5_response.get("answer", "")
    intent = turn5_response.get("intent", "")
    
    # Check for decision synthesis with conflict resolution
    checks = {
        "Memory used (mentions coding)": "coding" in answer.lower() or "bca" in answer.lower(),
        "Memory used (mentions math constraint)": "math" in answer.lower(),
        "Memory used (mentions salary goal)": "salary" in answer.lower() or "lpa" in answer.lower(),
        "Memory used (mentions quick job goal)": "quick" in answer.lower() or "fast" in answer.lower(),
        "Detects conflict (competing goals)": "competing" in answer.lower() or "conflict" in answer.lower() or "two" in answer.lower() and "goal" in answer.lower(),
        "Provides multiple options": "option 1" in answer.lower() and "option 2" in answer.lower(),
        "Has final recommendation": "recommendation" in answer.lower() or "my recommendation" in answer.lower(),
        "Has reasoning (Why)": "why:" in answer.lower() or "why this works" in answer.lower() or "because" in answer.lower(),
        "Has trade-offs": "trade-off" in answer.lower() or "tradeoff" in answer.lower(),
        "Has personalization (math constraint addressed)": ("avoid" in answer.lower() and "data science" in answer.lower()) or ("focus on" in answer.lower() and ("web" in answer.lower() or "app" in answer.lower())),
        "No repetition (not asking more questions)": "let me ask you" not in answer.lower() and "tell me" not in answer.lower(),
        "Intent is decision synthesis": "decision" in intent or "synthesis" in intent,
    }
    
    passed = 0
    failed = 0
    
    for check_name, check_result in checks.items():
        status = "✅" if check_result else "❌"
        print(f"{status} {check_name}")
        if check_result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"RESULT: {passed}/{len(checks)} checks passed")
    print(f"{'='*80}\n")
    
    if failed == 0:
        print("✅ ALL CHECKS PASSED")
        print("Decision synthesis with conflict resolution working correctly!")
        return True
    elif passed >= len(checks) * 0.8:
        print(f"⚠️  {failed} CHECKS FAILED (but {passed}/{len(checks)} passed)")
        print("Decision synthesis mostly working, minor improvements needed")
        return True
    else:
        print(f"❌ {failed} CHECKS FAILED")
        print("Decision synthesis needs improvement")
        return False


if __name__ == "__main__":
    success = run_conversation_test()
    exit(0 if success else 1)
