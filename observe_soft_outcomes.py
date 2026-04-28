#!/usr/bin/env python3
"""
Soft Decision Outcome Tracking
Metric: Of users with hesitation, how many recover → convert vs drop?
Sample: 30 scenarios with soft decisions + hesitation patterns
"""

import sys
import json
from datetime import datetime

sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.orchestration.engine import run_counselor_pipeline
from app.services.counselor.memory import get_student_profile, SESSION_MEMORY

# 30 scenarios focusing on soft decision → hesitation → recovery/drop
SCENARIOS = [
    # Group 1: Soft decision → Hesitation → Recovery (should convert)
    {
        "name": "Soft → Compare → Recover",
        "flow": [
            "I'm interested in technology",
            "I think BCA is good",
            "Wait, what about BBA?",
            "Actually BCA seems better for coding",
            "How do I apply?"
        ],
        "expected_outcome": "recover"
    },
    {
        "name": "Soft → Doubt → Clarify → Proceed",
        "flow": [
            "Tell me about BCA",
            "I think I'll do BCA",
            "Hmm, but what if I regret it?",
            "Tell me about job prospects",
            "Okay, that sounds good"
        ],
        "expected_outcome": "recover"
    },
    {
        "name": "Soft → Question → Reassure → Commit",
        "flow": [
            "BCA seems right",
            "I'm thinking of going for it",
            "Is it really a good choice?",
            "Tell me about salary",
            "Great, I'll apply now"
        ],
        "expected_outcome": "recover"
    },
    # Group 2: Soft decision → Hesitation → Exploration → Recovery
    {
        "name": "Soft → Explore Alt → Return → Commit",
        "flow": [
            "I like programming",
            "I think BCA is my choice",
            "But what about B.Tech?",
            "Tell me about B.Tech vs BCA",
            "Actually BCA is better, let's go"
        ],
        "expected_outcome": "recover"
    },
    {
        "name": "Soft → Comparison → Deeper → Commit",
        "flow": [
            "I think BCA",
            "How does it compare to other courses?",
            "Tell me about fees",
            "Tell me about placements",
            "I'm convinced, let's proceed"
        ],
        "expected_outcome": "recover"
    },
    {
        "name": "Soft → Price check → Hesitation → Proceed",
        "flow": [
            "I think BCA is good",
            "How much does it cost?",
            "That's more than I expected",
            "Is there financial aid?",
            "Okay, I can manage it"
        ],
        "expected_outcome": "recover"
    },
    # Group 3: Soft decision → Hesitation → Continue without explicit recovery
    {
        "name": "Soft → Slight doubt → Keep asking",
        "flow": [
            "BCA seems interesting",
            "I'm thinking about it",
            "Is the college good?",
            "What about hostel facilities?",
            "Okay I have what I need"
        ],
        "expected_outcome": "recover"
    },
    {
        "name": "Soft → Concern → Address → Proceed",
        "flow": [
            "I think BCA",
            "But I'm worried about placements",
            "Tell me your placement stats",
            "That's better than I thought",
            "When can I start?"
        ],
        "expected_outcome": "recover"
    },
    {
        "name": "Soft → Alternative thought → Reaffirm",
        "flow": [
            "I'm leaning towards BCA",
            "Or maybe BBA?",
            "Tell me BCA job market",
            "That's better actually",
            "Let's go with BCA"
        ],
        "expected_outcome": "recover"
    },
    {
        "name": "Soft → Question → Answer → Proceed",
        "flow": [
            "BCA could be good",
            "Is it hard?",
            "Tell me about difficulty level",
            "That's manageable",
            "I'm ready to apply"
        ],
        "expected_outcome": "recover"
    },
    # Group 4: Soft decision → Hesitation → Drop (user disengages)
    {
        "name": "Soft → Doubt → Multiple questions → Fade",
        "flow": [
            "I think BCA",
            "Actually, I'm not sure",
            "What if I don't like coding?",
            "Tell me about alternatives",
            "I need to think about this"
        ],
        "expected_outcome": "drop"
    },
    {
        "name": "Soft → Indecision → No clear next step",
        "flow": [
            "Maybe BCA is right",
            "But I'm really unsure",
            "Tell me everything about it",
            "That's a lot to think about",
            "I'll come back later"
        ],
        "expected_outcome": "drop"
    },
    {
        "name": "Soft → Regret signals → Withdraw",
        "flow": [
            "I think I'll do BCA",
            "Actually, I'm having second thoughts",
            "What if I made a mistake?",
            "Is there a way to change later?",
            "Let me reconsider"
        ],
        "expected_outcome": "drop"
    },
    {
        "name": "Soft → Price shock → Withdraw",
        "flow": [
            "I think BCA",
            "How much is it?",
            "That's expensive",
            "Can I afford it?",
            "I don't think so"
        ],
        "expected_outcome": "drop"
    },
    {
        "name": "Soft → Overwhelm → Disengage",
        "flow": [
            "BCA seems good",
            "Tell me about fees",
            "Tell me about placements",
            "Tell me about admission",
            "This is too much right now"
        ],
        "expected_outcome": "drop"
    },
    # Group 5: Soft decision → Quick commit (minimal hesitation)
    {
        "name": "Soft → Immediate commit",
        "flow": [
            "I like coding",
            "I think BCA",
            "How do I apply?",
            "What documents needed?",
            "I'll apply today"
        ],
        "expected_outcome": "recover"
    },
    {
        "name": "Soft → One question → Proceed",
        "flow": [
            "I think BCA",
            "When does it start?",
            "Okay that works for me",
            "I'm ready",
            "Let's do this"
        ],
        "expected_outcome": "recover"
    },
    {
        "name": "Soft → Reassurance → Action",
        "flow": [
            "I'm thinking BCA",
            "Is it a good choice?",
            "Tell me about reputation",
            "Great, that helps",
            "I'll apply now"
        ],
        "expected_outcome": "recover"
    },
    {
        "name": "Soft → No hesitation → Direct to apply",
        "flow": [
            "Maybe BCA",
            "I think it's good",
            "How to apply?",
            "Got it",
            "Applying now"
        ],
        "expected_outcome": "recover"
    },
    {
        "name": "Soft → Question → Answer → Done",
        "flow": [
            "I think BCA",
            "How long is the course?",
            "That's perfect",
            "Great",
            "I'm in"
        ],
        "expected_outcome": "recover"
    },
    # Group 6: Soft decision → More exploration
    {
        "name": "Soft → Deep exploration → Convert",
        "flow": [
            "I think BCA",
            "Tell me more details",
            "What about internships?",
            "What about study abroad?",
            "Perfect, I'm convinced"
        ],
        "expected_outcome": "recover"
    },
    {
        "name": "Soft → Market research → Proceed",
        "flow": [
            "Maybe BCA",
            "What's the job market like?",
            "Salary trends?",
            "Okay that's promising",
            "I'll go for it"
        ],
        "expected_outcome": "recover"
    },
    {
        "name": "Soft → Career path → Commit",
        "flow": [
            "I think BCA",
            "What careers can I pursue?",
            "Tell me about startup opportunity",
            "That's interesting",
            "Alright, signing up"
        ],
        "expected_outcome": "recover"
    },
    {
        "name": "Soft → Comparison deep dive → Choose",
        "flow": [
            "I'm thinking BCA",
            "How is it different from B.Tech?",
            "Career prospects comparison?",
            "BCA seems better",
            "Let's proceed"
        ],
        "expected_outcome": "recover"
    },
    {
        "name": "Soft → Practical concerns → Resolved → Proceed",
        "flow": [
            "I think BCA",
            "Can I work part-time?",
            "Is there flexible timing?",
            "Yes, that works",
            "I'm applying"
        ],
        "expected_outcome": "recover"
    },
    # Group 7: Soft → Drop variations
    {
        "name": "Soft → Comparison paralysis",
        "flow": [
            "Maybe BCA",
            "Or BBA?",
            "Or B.Com?",
            "Tell me all options",
            "I can't decide"
        ],
        "expected_outcome": "drop"
    },
    {
        "name": "Soft → Family concern → Stall",
        "flow": [
            "I think BCA",
            "But I need to ask my parents",
            "Tell me about reputation first",
            "I'll discuss at home",
            "I'll get back to you"
        ],
        "expected_outcome": "drop"
    },
    {
        "name": "Soft → External factor → Defer",
        "flow": [
            "BCA seems good",
            "But I need to check something",
            "Tell me about entrance exams",
            "I need to prepare for that",
            "I'll come back later"
        ],
        "expected_outcome": "drop"
    },
    {
        "name": "Soft → Timing issue → No commitment",
        "flow": [
            "I think BCA",
            "When is the next batch?",
            "That's far away",
            "I need time to think",
            "I'll decide later"
        ],
        "expected_outcome": "drop"
    },
    {
        "name": "Soft → Unclear process → Abandon",
        "flow": [
            "I think BCA",
            "How do I actually apply?",
            "What's the process?",
            "That sounds complicated",
            "Maybe later"
        ],
        "expected_outcome": "drop"
    },
]

# ============================================================================
# Run Observations
# ============================================================================

print("=" * 80)
print("🔬 SOFT DECISION OUTCOME TRACKING")
print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Scenarios: {len(SCENARIOS)}")
print("=" * 80)

observations = []
hesitation_cases = []

for scenario_idx, scenario in enumerate(SCENARIOS, 1):
    scenario_name = scenario["name"]
    flow = scenario["flow"]
    expected_outcome = scenario["expected_outcome"]
    
    session_id = f"outcome_test_{scenario_idx}"
    
    # Clear previous session
    if session_id in SESSION_MEMORY:
        del SESSION_MEMORY[session_id]
    
    context = {}
    soft_detected = False
    soft_turn = None
    hesitation_detected = False
    final_action = None
    
    for turn_idx, query in enumerate(flow, 1):
        try:
            response = run_counselor_pipeline(query, session_id=session_id, context=context)
            if response is None:
                continue
        except Exception as e:
            continue
        
        profile = get_student_profile(session_id)
        
        # Detect soft decision language
        is_soft = any(w in query.lower() for w in ["i think", "maybe", "seem", "probably", "leaning", "could"])
        if is_soft and not soft_detected:
            soft_detected = True
            soft_turn = turn_idx
        
        # Detect hesitation signals
        is_hesitation = any(w in query.lower() for w in ["not sure", "unsure", "doubt", "second thought", "reconsider", "actually", "wait", "but", "what if"])
        if soft_detected and turn_idx > soft_turn and is_hesitation:
            hesitation_detected = True
        
        # Detect final action/outcome
        query_lower = query.lower()
        if any(w in query_lower for w in ["apply", "signing up", "i'm in", "let's do", "i'm convinced", "perfect"]):
            final_action = "convert"
        elif any(w in query_lower for w in ["i'll think", "later", "decide", "reconsider", "need time", "i'll come back", "maybe later", "can't decide", "complicated"]):
            final_action = "drop"
        
        # Update context
        context = {"locked_course": profile.get("locked_course")}
    
    # Classify outcome
    if soft_detected and hesitation_detected:
        actual_outcome = final_action if final_action else "uncertain"
        observation = {
            "scenario": scenario_idx,
            "name": scenario_name,
            "expected": expected_outcome,
            "actual": actual_outcome,
            "soft_detected": True,
            "hesitation_detected": True,
            "match": (expected_outcome == actual_outcome)
        }
        hesitation_cases.append(observation)
    else:
        observation = {
            "scenario": scenario_idx,
            "name": scenario_name,
            "expected": expected_outcome,
            "actual": "no_hesitation",
            "soft_detected": soft_detected,
            "hesitation_detected": False,
            "match": None
        }
    
    observations.append(observation)
    
    # Print summary
    status = "✅" if (hesitation_detected and final_action) else "⚠️ " if hesitation_detected else "➡️ "
    print(f"{status} Scenario {scenario_idx:2d}: {scenario_name:40s} | Expected: {expected_outcome:8s} | Got: {final_action or 'no_action':10s}")

# ============================================================================
# Analysis
# ============================================================================

print("\n" + "=" * 80)
print("📊 OUTCOME ANALYSIS")
print("=" * 80)

if hesitation_cases:
    recovery_count = sum(1 for o in hesitation_cases if o["actual"] == "convert")
    drop_count = sum(1 for o in hesitation_cases if o["actual"] == "drop")
    uncertain_count = sum(1 for o in hesitation_cases if o["actual"] == "uncertain")
    total_hesitation = len(hesitation_cases)
    
    print(f"\nTotal scenarios with hesitation: {total_hesitation}")
    print(f"  • Recovered & converted:  {recovery_count} ({recovery_count/total_hesitation*100:.1f}%)")
    print(f"  • Dropped/disengaged:     {drop_count} ({drop_count/total_hesitation*100:.1f}%)")
    print(f"  • Uncertain/no_action:    {uncertain_count} ({uncertain_count/total_hesitation*100:.1f}%)")
    
    print(f"\n🎯 KEY METRIC: Recovery Rate = {recovery_count}/{total_hesitation} = {recovery_count/total_hesitation*100:.1f}%")
    
    if recovery_count > drop_count:
        print(f"\n✅ VERDICT: Hesitation usually leads to recovery (healthy)")
        print(f"   → Users question but ultimately convert")
    elif drop_count > recovery_count:
        print(f"\n🔴 VERDICT: Hesitation often leads to drop (problem)")
        print(f"   → System friction is causing abandonment")
    else:
        print(f"\n⚠️  VERDICT: Mixed outcomes")
    
    # Match accuracy
    correct_predictions = sum(1 for o in hesitation_cases if o["match"])
    print(f"\nPrediction accuracy: {correct_predictions}/{total_hesitation} ({correct_predictions/total_hesitation*100:.1f}%)")
else:
    print("\n⚠️  No hesitation cases detected in this run")

print("\n" + "=" * 80)

# Save results
output = {
    "timestamp": datetime.now().isoformat(),
    "total_scenarios": len(observations),
    "hesitation_cases": len(hesitation_cases),
    "recovery_count": recovery_count if hesitation_cases else 0,
    "drop_count": drop_count if hesitation_cases else 0,
    "recovery_rate": f"{recovery_count/total_hesitation*100:.1f}%" if hesitation_cases else "N/A",
    "observations": observations
}

with open("soft_decision_outcomes.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"📁 Results saved to: soft_decision_outcomes.json")
