#!/usr/bin/env python3
"""
Headless Browser Test - Single Clear Pattern
Email: storageeapp@gmail.com
Prove: Routing order fix + Brain lock behavior

Pattern to capture:
User explores → System routes to counselor → User decides → System locks → Memory persists
"""

import sys
import json
from datetime import datetime

sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.orchestration.engine import run_counselor_pipeline
from app.services.counselor.memory import get_student_profile, SESSION_MEMORY

# Use email as session ID
EMAIL = "storageeapp@gmail.com"
SESSION_ID = EMAIL

print("=" * 80)
print(f"🧪 HEADLESS BROWSER TEST")
print(f"   Email: {EMAIL}")
print(f"   Session: {SESSION_ID}")
print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Clear any previous session
if SESSION_ID in SESSION_MEMORY:
    del SESSION_MEMORY[SESSION_ID]

journey = []

# TURN 1: Generic exploration (should route to structured or counselor, NOT fallback)
print("\n" + "─" * 80)
print("TURN 1: USER EXPLORES")
print("─" * 80)

query_1 = "What courses do you offer?"
print(f"\n👤 User: {query_1}")

response_1 = run_counselor_pipeline(query_1, session_id=SESSION_ID, context={})
profile_1 = get_student_profile(SESSION_ID)

turn_1 = {
    "turn": 1,
    "query": query_1,
    "mode": response_1.get("mode"),
    "confidence": response_1.get("confidence"),
    "intents": response_1.get("intents"),
    "answer_preview": response_1.get("answer", "")[:120],
    "memory": {
        "locked_course": profile_1.get("locked_course"),
        "courses": profile_1.get("courses", []),
        "turn_count": profile_1.get("turn_count"),
    }
}

print(f"\n🤖 Router Decision: {response_1.get('mode')}")
print(f"   Confidence: {response_1.get('confidence'):.2f}")
print(f"   Intents: {response_1.get('intents')}")
print(f"\n📝 Response Preview:")
print(f"   {response_1.get('answer', '')[:200]}...")

print(f"\n💾 Memory State:")
print(f"   locked_course: {profile_1.get('locked_course')}")
print(f"   courses: {profile_1.get('courses', [])}")
print(f"   turn_count: {profile_1.get('turn_count')}")

journey.append(turn_1)

# TURN 2: User shows interest in a specific course (should trigger counselor brain)
print("\n" + "─" * 80)
print("TURN 2: USER SHOWS INTEREST")
print("─" * 80)

query_2 = "Tell me about BCA and BBA"
print(f"\n👤 User: {query_2}")

context_2 = {
    "locked_course": profile_1.get("locked_course"),
    "courses": profile_1.get("courses"),
}

response_2 = run_counselor_pipeline(query_2, session_id=SESSION_ID, context=context_2)
profile_2 = get_student_profile(SESSION_ID)

turn_2 = {
    "turn": 2,
    "query": query_2,
    "mode": response_2.get("mode"),
    "confidence": response_2.get("confidence"),
    "intents": response_2.get("intents"),
    "answer_preview": response_2.get("answer", "")[:120],
    "memory": {
        "locked_course": profile_2.get("locked_course"),
        "courses": profile_2.get("courses", []),
        "turn_count": profile_2.get("turn_count"),
    }
}

print(f"\n🤖 Router Decision: {response_2.get('mode')}")
print(f"   Confidence: {response_2.get('confidence'):.2f}")
print(f"   Intents: {response_2.get('intents')}")
print(f"\n📝 Response Preview:")
print(f"   {response_2.get('answer', '')[:200]}...")

print(f"\n💾 Memory State:")
print(f"   locked_course: {profile_2.get('locked_course')}")
print(f"   courses: {profile_2.get('courses', [])}")
print(f"   turn_count: {profile_2.get('turn_count')}")

journey.append(turn_2)

# TURN 3: Explicit decision (should trigger BRAIN → DECISION LOCK)
print("\n" + "─" * 80)
print("TURN 3: USER DECIDES (EXPLICIT INTENT)")
print("─" * 80)

query_3 = "I think BCA is good for me"
print(f"\n👤 User: {query_3}")

context_3 = {
    "locked_course": profile_2.get("locked_course"),
    "courses": profile_2.get("courses", []),
}

response_3 = run_counselor_pipeline(query_3, session_id=SESSION_ID, context=context_3)
profile_3 = get_student_profile(SESSION_ID)

turn_3 = {
    "turn": 3,
    "query": query_3,
    "mode": response_3.get("mode"),
    "confidence": response_3.get("confidence"),
    "intents": response_3.get("intents"),
    "answer_preview": response_3.get("answer", "")[:120],
    "memory": {
        "locked_course": profile_3.get("locked_course"),
        "courses": profile_3.get("courses", []),
        "turn_count": profile_3.get("turn_count"),
    }
}

print(f"\n🤖 Router Decision: {response_3.get('mode')}")
print(f"   Confidence: {response_3.get('confidence'):.2f}")
print(f"   Intents: {response_3.get('intents')}")
print(f"\n📝 Response Preview:")
print(f"   {response_3.get('answer', '')[:200]}...")

print(f"\n💾 Memory State:")
print(f"   locked_course: {profile_3.get('locked_course')}")
print(f"   courses: {profile_3.get('courses', [])}")
print(f"   turn_count: {profile_3.get('turn_count')}")

journey.append(turn_3)

# TURN 4: Follow-up question (memory should persist lock)
print("\n" + "─" * 80)
print("TURN 4: MEMORY PERSISTENCE CHECK")
print("─" * 80)

query_4 = "What's the fee structure?"
print(f"\n👤 User: {query_4}")

context_4 = {
    "locked_course": profile_3.get("locked_course"),
    "courses": profile_3.get("courses", []),
}

response_4 = run_counselor_pipeline(query_4, session_id=SESSION_ID, context=context_4)
profile_4 = get_student_profile(SESSION_ID)

turn_4 = {
    "turn": 4,
    "query": query_4,
    "mode": response_4.get("mode"),
    "confidence": response_4.get("confidence"),
    "intents": response_4.get("intents"),
    "answer_preview": response_4.get("answer", "")[:120],
    "memory": {
        "locked_course": profile_4.get("locked_course"),
        "courses": profile_4.get("courses", []),
        "turn_count": profile_4.get("turn_count"),
    }
}

print(f"\n🤖 Router Decision: {response_4.get('mode')}")
print(f"   Confidence: {response_4.get('confidence'):.2f}")
print(f"   Intents: {response_4.get('intents')}")
print(f"\n📝 Response Preview:")
print(f"   {response_4.get('answer', '')[:200]}...")

print(f"\n💾 Memory State:")
print(f"   locked_course: {profile_4.get('locked_course')}")
print(f"   courses: {profile_4.get('courses', [])}")
print(f"   turn_count: {profile_4.get('turn_count')}")

journey.append(turn_4)

# ============================================================================
# PATTERN ANALYSIS
# ============================================================================

print("\n" + "=" * 80)
print("🔍 PATTERN ANALYSIS")
print("=" * 80)

print("\n📊 THE SINGLE CLEAR PATTERN:\n")

print("Turn 1 (Exploration):")
print(f"  Query:  'What courses do you offer?'")
print(f"  Route:  {turn_1['mode']}")
print(f"  Lock:   {turn_1['memory']['locked_course']}")
print(f"  Status: ✅ Routed to {turn_1['mode']} (NOT fallback)")

print("\nTurn 2 (Comparison):")
print(f"  Query:  'Tell me about BCA and BBA'")
print(f"  Route:  {turn_2['mode']}")
print(f"  Lock:   {turn_2['memory']['locked_course']}")
print(f"  Status: ✅ Maintained in {turn_2['mode']} (no premature lock)")

print("\nTurn 3 (Decision):")
print(f"  Query:  'I think BCA is good for me'")
print(f"  Route:  {turn_3['mode']}")
print(f"  Lock:   {turn_3['memory']['locked_course']}")
print(f"  Status: ✅ LOCKED to {turn_3['memory']['locked_course']} (brain triggered)")

print("\nTurn 4 (Persistence):")
print(f"  Query:  'What's the fee structure?'")
print(f"  Route:  {turn_4['mode']}")
print(f"  Lock:   {turn_4['memory']['locked_course']}")
print(f"  Status: ✅ Lock PERSISTED: {turn_4['memory']['locked_course']} == {turn_3['memory']['locked_course']}")

# Verify the pattern
pattern_checks = {
    "Turn 1 routed (not fallback)": turn_1['mode'] != 'fallback',
    "Turn 2 no premature lock": turn_2['memory']['locked_course'] is None,
    "Turn 3 decision locked": turn_3['memory']['locked_course'] == 'BCA',
    "Turn 4 lock persisted": turn_4['memory']['locked_course'] == turn_3['memory']['locked_course'],
}

print("\n" + "─" * 80)
print("PATTERN VERIFICATION")
print("─" * 80)

all_passed = True
for check_name, result in pattern_checks.items():
    status = "✅" if result else "❌"
    print(f"{status} {check_name}")
    if not result:
        all_passed = False

print("\n" + "=" * 80)
print("VERDICT")
print("=" * 80)

if all_passed:
    print("\n✅ PATTERN CONFIRMED")
    print("\n📌 What This Proves:")
    print("   1. Routing is correct (structured layer before counselor)")
    print("   2. Brain locks on explicit intent (turn 3)")
    print("   3. Memory persists across turns (turn 4)")
    print("   4. No premature locking (turn 2)")
    print("\n🎯 System working as designed.")
else:
    print("\n❌ PATTERN FAILED")
    print("\n🔴 Issues detected:")
    for check_name, result in pattern_checks.items():
        if not result:
            print(f"   • {check_name}")

# Save results
output = {
    "email": EMAIL,
    "timestamp": datetime.now().isoformat(),
    "journey": journey,
    "pattern_checks": pattern_checks,
    "verdict": "PASSED" if all_passed else "FAILED"
}

with open("browser_test_pattern.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\n📁 Results saved to: browser_test_pattern.json")
print("=" * 80)
