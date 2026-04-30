"""
Test script to verify confidence persistence across multi-turn conversations.
Run from: cd backend && python test_confidence_flow.py
"""
import requests
import json

BASE = "http://localhost:8000/api/v1/chat"
SESSION = "confidence-verify-001"

turns = [
    ("I like coding", "Initial interest → should start moderate ~0.45"),
    ("actually I hate coding", "Strong contradiction → should drop significantly"),
    ("maybe business is better for me", "Uncertain pivot → recovery with ambiguity"),
    ("I decided, I want BBA, what should I do?", "Decision + strong clarity → should spike high"),
]

prev_conf = None
print("\n" + "="*60)
print("CONFIDENCE PERSISTENCE FLOW TEST")
print("="*60)

for i, (query, note) in enumerate(turns, 1):
    r = requests.post(BASE, json={"query": query, "session_id": SESSION})
    d = r.json()
    
    api_conf = d.get("confidence")
    profile_conf = d.get("meta", {}).get("profile_confidence_score", "N/A")
    intent = d.get("intent", "N/A")
    
    print(f"\nTurn {i}: {query!r}")
    print(f"  Note    : {note}")
    print(f"  Intent  : {intent}")
    print(f"  API conf: {api_conf}")
    print(f"  Profile : {profile_conf}")
    
    # Check: API confidence should match profile confidence (the main bug)
    if api_conf is not None and profile_conf != "N/A":
        match = abs(float(api_conf) - float(profile_conf)) < 0.001
        print(f"  Match?  : {'✅ YES' if match else '❌ NO (BUG!)'}")
    
    # Check monotonicity expectations
    if prev_conf is not None and i == 2:
        dropped = float(api_conf) < float(prev_conf)
        print(f"  Drop?   : {'✅ Dropped correctly' if dropped else '❌ Did NOT drop (BUG!)'}")
    
    prev_conf = api_conf

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
