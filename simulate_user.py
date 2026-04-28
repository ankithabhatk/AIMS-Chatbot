#!/usr/bin/env python3
"""
User Experience Simulator - Real conversation flows
Tests system from USER perspective, not internal perspective
No debug inspection - only user-visible behavior
"""

import requests
import time

API_URL = "http://localhost:8000/api/v1/chat"

def chat(session_id, query):
    """Simulate user sending a message"""
    try:
        res = requests.post(
            API_URL,
            json={"query": query, "session_id": session_id},
            headers={"Content-Type": "application/json"},
            timeout=10
        ).json()
        
        print(f"\n👤 USER: {query}")
        print(f"🤖 BOT: {res['answer'][:200]}{'...' if len(res['answer']) > 200 else ''}")
        print(f"   [mode: {res.get('mode')}]")
        print("-" * 70)
        
        time.sleep(0.5)  # Simulate human typing delay
        return res
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return None

def run_flow(name, session_id, queries):
    """Run a complete conversation flow"""
    print(f"\n{'='*70}")
    print(f"FLOW: {name}")
    print(f"{'='*70}")
    
    for query in queries:
        chat(session_id, query)
    
    print(f"\n✅ Flow complete: {name}\n")

# Real user conversation flows
FLOWS = [
    {
        "name": "Exploration → Decision → Apply",
        "session": "user-flow-1",
        "queries": [
            "I got 75% in 12th",
            "Tell me about BCA",
            "What are the fees?",
            "I think BCA is good for me",
            "How do I apply?"
        ]
    },
    {
        "name": "Direct Decision → Apply",
        "session": "user-flow-2",
        "queries": [
            "I want to do MBA",
            "What are the fees?",
            "How to apply for MBA?"
        ]
    },
    {
        "name": "Vague → Confused → Escalation",
        "session": "user-flow-3",
        "queries": [
            "Tell me something",
            "What can you help with",
            "I need help"
        ]
    },
    {
        "name": "Locked → Repeated Question",
        "session": "user-flow-4",
        "queries": [
            "I got 80% and like business",
            "BBA sounds good",
            "What about fees?",
            "Fees?",
            "Tell me the fees"
        ]
    },
    {
        "name": "Exploration → Comparison → Decision",
        "session": "user-flow-5",
        "queries": [
            "I like coding",
            "Tell me about BCA",
            "What about MCA?",
            "Which is better?",
            "I'll go with BCA"
        ]
    }
]

def main():
    """Run user experience simulation"""
    print("\n🎭 USER EXPERIENCE SIMULATOR")
    print("Testing system from USER perspective (no debug inspection)")
    print(f"\nRunning {len(FLOWS)} conversation flows...\n")
    
    for flow in FLOWS:
        run_flow(flow["name"], flow["session"], flow["queries"])
        time.sleep(1)  # Pause between flows
    
    print("\n" + "="*70)
    print("✅ All flows complete")
    print("="*70)
    print("\n📝 REFLECTION QUESTIONS:")
    print("1. Did conversations feel natural?")
    print("2. Any friction moments (confusion, repetition)?")
    print("3. Did system move user toward action?")
    print("4. Any hesitation points?")
    print("\n👉 Identify ONE pattern that felt wrong\n")

if __name__ == "__main__":
    main()
