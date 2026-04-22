# backend/scripts/test_lead_capture_flow.py

import sys
import os
import uuid

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.lead_handler import handle_lead_capture, should_trigger_capture, initiate_capture, LEAD_SESSIONS

def test_conversational_flow():
    session_id = str(uuid.uuid4())
    print("\n" + "="*80)
    print(f"TESTING LEAD CAPTURE FLOW (Session: {session_id})")
    print("="*80)
    
    # 1. Turn 1 - Question 1 (General)
    query1 = "What programs do you offer?"
    print(f"\n[TURN 1] User: {query1}")
    trigger1 = should_trigger_capture(session_id, query1)
    print(f"Trigger: {trigger1} (Expected: False because query_count=1)")
    
    # 2. Turn 2 - Question 2 (High Intent)
    query2 = "What is the fee for MBA?"
    print(f"\n[TURN 2] User: {query2}")
    trigger2 = should_trigger_capture(session_id, query2) # This is 2nd question + high intent
    print(f"Trigger: {trigger2} (Expected: True)")
    
    if trigger2:
        hook = initiate_capture(session_id)
        print(f"Bot appends: '{hook}'")
    
    # 3. Turn 3 - Provide Name
    name = "John Doe"
    print(f"\n[TURN 3] User: {name}")
    resp3 = handle_lead_capture(session_id, name)
    print(f"Bot: '{resp3['answer']}'")
    
    # 4. Turn 4 - Provide Phone
    phone = "9876543210"
    print(f"\n[TURN 4] User: {phone}")
    resp4 = handle_lead_capture(session_id, phone)
    print(f"Bot: '{resp4['answer']}'")
    
    # 5. Turn 5 - Provide Email
    email = "john@example.com"
    print(f"\n[TURN 5] User: {email}")
    resp5 = handle_lead_capture(session_id, email)
    print(f"Bot: '{resp5['answer']}'")
    
    if resp5.get("lead_ready"):
        print("\n✅ SUCCESS: Lead ready for saving!")
        print(f"Final Data: {resp5['data']}")
    else:
        print("\n❌ FAILURE: Lead capture not completed.")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    test_conversational_flow()
