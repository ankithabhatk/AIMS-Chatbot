#!/usr/bin/env python3
"""Test fallback escalation - engaged users only"""

import requests

API_URL = "http://localhost:8000/api/v1/chat"

def test_fallback_escalation():
    """Test that fallback escalates after 2 attempts for engaged users"""
    
    print("🧪 Testing Fallback Escalation\n")
    print("=" * 70)
    
    # Test 1: Engaged user (3+ words) - should escalate
    print("\n1. ENGAGED USER TEST (should escalate)")
    session_id = "test-escalation-engaged"
    
    queries = [
        "tell me something",  # Fallback 1
        "what can you do",    # Fallback 2
        "help me please"      # Should escalate
    ]
    
    for i, query in enumerate(queries, 1):
        response = requests.post(
            API_URL,
            json={"query": query, "session_id": session_id},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"   ❌ ERROR: HTTP {response.status_code}")
            continue
        
        data = response.json()
        mode = data.get("mode")
        answer = data.get("answer", "")[:80]
        
        print(f"   Turn {i}: '{query}'")
        print(f"   Mode: {mode}")
        print(f"   Answer: {answer}...")
        
        if i == 3:
            if mode == "escalation" and "narrow this down" in answer.lower():
                print(f"   ✅ ESCALATION TRIGGERED")
            else:
                print(f"   ❌ ESCALATION FAILED - Mode: {mode}")
    
    # Test 2: Noise user (1-2 words) - should NOT escalate
    print("\n2. NOISE USER TEST (should NOT escalate)")
    session_id = "test-escalation-noise"
    
    queries = [
        "hi",      # Fallback 1
        "hello",   # Fallback 2
        "hey"      # Should still be fallback (not escalate)
    ]
    
    for i, query in enumerate(queries, 1):
        response = requests.post(
            API_URL,
            json={"query": query, "session_id": session_id},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"   ❌ ERROR: HTTP {response.status_code}")
            continue
        
        data = response.json()
        mode = data.get("mode")
        answer = data.get("answer", "")[:80]
        
        print(f"   Turn {i}: '{query}'")
        print(f"   Mode: {mode}")
        
        if i == 3:
            if mode == "fallback":
                print(f"   ✅ CORRECTLY STAYED IN FALLBACK (noise filtered)")
            else:
                print(f"   ❌ INCORRECTLY ESCALATED - Mode: {mode}")
    
    # Test 3: Recovery after escalation
    print("\n3. RECOVERY TEST (escalation should not loop)")
    session_id = "test-escalation-recovery"
    
    queries = [
        "tell me something",  # Fallback 1
        "what can you do",    # Fallback 2
        "help me please",     # Escalation
        "what else"           # Should be fallback (not escalate again)
    ]
    
    for i, query in enumerate(queries, 1):
        response = requests.post(
            API_URL,
            json={"query": query, "session_id": session_id},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"   ❌ ERROR: HTTP {response.status_code}")
            continue
        
        data = response.json()
        mode = data.get("mode")
        
        print(f"   Turn {i}: '{query}' → Mode: {mode}")
        
        if i == 4:
            if mode == "fallback":
                print(f"   ✅ CORRECTLY PREVENTED ESCALATION LOOP")
            elif mode == "escalation":
                print(f"   ❌ ESCALATION LOOP DETECTED")
    
    print("\n" + "=" * 70)
    print("\n✅ Fallback escalation test complete")

if __name__ == "__main__":
    test_fallback_escalation()
