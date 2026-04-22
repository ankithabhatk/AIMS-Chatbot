# backend/scripts/test_gated_gate.py

import sys
import os
import uuid

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.lead_handler import (
    get_or_create_session, update_session_on_query, 
    handle_gated_capture, get_gate_invitation, FEES_DISCLAIMER
)

def test_gated_flow():
    session_id = str(uuid.uuid4())
    print("\n" + "="*80)
    print(f"TESTING MANDATORY GATE FLOW (Session: {session_id})")
    print("="*80)
    
    # --- TURN 1 (Free) ---
    query1 = "What is AIMS Institutes?"
    print(f"\n[TURN 1] User: {query1}")
    update_session_on_query(session_id, query1)
    session = get_or_create_session(session_id)
    print(f"Status: count={session['query_count']}, gate={session['gate_active']}")
    print(f"UX: (RAG Answer) + \n{get_gate_invitation()}")

    # --- TURN 2 (Blocked) ---
    query2 = "Tell me about courses"
    print(f"\n[TURN 2] User: {query2}")
    update_session_on_query(session_id, query2)
    session = get_or_create_session(session_id)
    
    if session["gate_active"] and not session["has_lead"]:
        print("SYSTEM: [BLOCK] Gate is active. Intercepting input...")
        resp = handle_gated_capture(session_id, query2)
        print(f"Bot: {resp['answer']}")
    
    # --- TURN 3 (Validation Error) ---
    query3 = "John Doe, john@invalid, MBA"
    print(f"\n[TURN 3] User: {query3} (Invalid Email)")
    resp3 = handle_gated_capture(session_id, query3)
    print(f"Bot: {resp3['answer']}")

    # --- TURN 4 (Success) ---
    query4 = "John Doe, john@example.com, MBA, 9876543210"
    print(f"\n[TURN 4] User: {query4}")
    resp4 = handle_gated_capture(session_id, query4)
    print(f"Bot: {resp4['answer']}")
    
    session = get_or_create_session(session_id)
    print(f"Status: unlock={not session['gate_active']}, has_lead={session['has_lead']}")

def test_fees_intercept():
    session_id = str(uuid.uuid4())
    print("\n" + "="*80)
    print(f"TESTING FEES INTERCEPT (Session: {session_id})")
    print("="*80)
    
    query1 = "What are the MBA fees?"
    print(f"\n[TURN 1] User: {query1}")
    
    # This logic matches chat_phase4.py implementation
    if "fee" in query1.lower():
        update_session_on_query(session_id, query1)
        print(f"Bot: {FEES_DISCLAIMER}\n\n{get_gate_invitation()}")
    
    session = get_or_create_session(session_id)
    print(f"Status: gate_active={session['gate_active']}")

if __name__ == "__main__":
    test_gated_flow()
    test_fees_intercept()
