#!/usr/bin/env python3
"""
Soft Decision Outcome Tracking - REFINED MEASUREMENT
Only change: Detection logic (NOT system behavior)

Recovery = user continues asking relevant course questions
Drop = user stops or diverges
"""

import sys
import json
from datetime import datetime

sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.orchestration.engine import run_counselor_pipeline
from app.services.counselor.memory import get_student_profile, SESSION_MEMORY

# Recovery signals: course-related follow-ups
RECOVERY_KEYWORDS = [
    "fee", "cost", "price", "scholarship", "financial",
    "placement", "job", "salary", "career", "work",
    "duration", "course", "curriculum", "syllabus",
    "eligibility", "requirement", "admission", "apply",
    "hostel", "campus", "facilities", "infrastructure",
    "comparison", "difference", "vs", "better", "similar",
    "difficulty", "hard", "easy", "challenging",
    "batch", "start", "enrollment", "when",
    "location", "where", "university", "college",
    "internship", "experience", "practical", "project",
    "abroad", "placement", "opportunity"
]

# Drop signals: disengagement
DROP_KEYWORDS = [
    "i'll think", "come back", "later", "maybe later",
    "i need time", "decide later", "reconsider",
    "i'll come back", "not sure now", "can't decide",
    "complicated", "too much", "overwhelming",
    "my parents", "family", "need to ask",
    "i can't afford", "too expensive", "financial issue",
    "unsure", "unclear", "don't know", "confused"
]

def is_recovery_signal(query: str) -> bool:
    """User continues engaging with course-relevant questions"""
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in RECOVERY_KEYWORDS)

def is_drop_signal(query: str) -> bool:
    """User disengages or defers decision"""
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in DROP_KEYWORDS)

# 30 scenarios (same as before)
SCENARIOS = [
    {
        "name": "Soft → Compare → Recover",
        "flow": [
            "I'm interested in technology",
            "I think BCA is good",
            "Wait, what about BBA?",
            "Actually BCA seems better for coding",
            "How do I apply?"
        ]
    },
    {
        "name": "Soft → Doubt → Clarify → Proceed",
        "flow": [
            "Tell me about BCA",
            "I think I'll do BCA",
            "Hmm, but what if I regret it?",
            "Tell me about job prospects",
            "Okay, that sounds good"
        ]
    },
    {
        "name": "Soft → Question → Reassure → Commit",
        "flow": [
            "BCA seems right",
            "I'm thinking of going for it",
            "Is it really a good choice?",
            "Tell me about salary",
            "Great, I'll apply now"
        ]
    },
    {
        "name": "Soft → Explore Alt → Return → Commit",
        "flow": [
            "I like programming",
            "I think BCA is my choice",
            "But what about B.Tech?",
            "Tell me about B.Tech vs BCA",
            "Actually BCA is better, let's go"
        ]
    },
    {
        "name": "Soft → Comparison → Deeper → Commit",
        "flow": [
            "I think BCA",
            "How does it compare to other courses?",
            "Tell me about fees",
            "Tell me about placements",
            "I'm convinced, let's proceed"
        ]
    },
    {
        "name": "Soft → Price check → Hesitation → Proceed",
        "flow": [
            "I think BCA is good",
            "How much does it cost?",
            "That's more than I expected",
            "Is there financial aid?",
            "Okay, I can manage it"
        ]
    },
    {
        "name": "Soft → Slight doubt → Keep asking",
        "flow": [
            "BCA seems interesting",
            "I'm thinking about it",
            "Is the college good?",
            "What about hostel facilities?",
            "Okay I have what I need"
        ]
    },
    {
        "name": "Soft → Concern → Address → Proceed",
        "flow": [
            "I think BCA",
            "But I'm worried about placements",
            "Tell me your placement stats",
            "That's better than I thought",
            "When can I start?"
        ]
    },
    {
        "name": "Soft → Alternative thought → Reaffirm",
        "flow": [
            "I'm leaning towards BCA",
            "Or maybe BBA?",
            "Tell me BCA job market",
            "That's better actually",
            "Let's go with BCA"
        ]
    },
    {
        "name": "Soft → Question → Answer → Proceed",
        "flow": [
            "BCA could be good",
            "Is it hard?",
            "Tell me about difficulty level",
            "That's manageable",
            "I'm ready to apply"
        ]
    },
    {
        "name": "Soft → Doubt → Multiple questions → Fade",
        "flow": [
            "I think BCA",
            "Actually, I'm not sure",
            "What if I don't like coding?",
            "Tell me about alternatives",
            "I need to think about this"
        ]
    },
    {
        "name": "Soft → Indecision → No clear next step",
        "flow": [
            "Maybe BCA is right",
            "But I'm really unsure",
            "Tell me everything about it",
            "That's a lot to think about",
            "I'll come back later"
        ]
    },
    {
        "name": "Soft → Regret signals → Withdraw",
        "flow": [
            "I think I'll do BCA",
            "Actually, I'm having second thoughts",
            "What if I made a mistake?",
            "Is there a way to change later?",
            "Let me reconsider"
        ]
    },
    {
        "name": "Soft → Price shock → Withdraw",
        "flow": [
            "I think BCA",
            "How much is it?",
            "That's expensive",
            "Can I afford it?",
            "I don't think so"
        ]
    },
    {
        "name": "Soft → Overwhelm → Disengage",
        "flow": [
            "BCA seems good",
            "Tell me about fees",
            "Tell me about placements",
            "Tell me about admission",
            "This is too much right now"
        ]
    },
    {
        "name": "Soft → Immediate commit",
        "flow": [
            "I like coding",
            "I think BCA",
            "How do I apply?",
            "What documents needed?",
            "I'll apply today"
        ]
    },
    {
        "name": "Soft → One question → Proceed",
        "flow": [
            "I think BCA",
            "When does it start?",
            "Okay that works for me",
            "I'm ready",
            "Let's do this"
        ]
    },
    {
        "name": "Soft → Reassurance → Action",
        "flow": [
            "I'm thinking BCA",
            "Is it a good choice?",
            "Tell me about reputation",
            "Great, that helps",
            "I'll apply now"
        ]
    },
    {
        "name": "Soft → No hesitation → Direct to apply",
        "flow": [
            "Maybe BCA",
            "I think it's good",
            "How to apply?",
            "Got it",
            "Applying now"
        ]
    },
    {
        "name": "Soft → Question → Answer → Done",
        "flow": [
            "I think BCA",
            "How long is the course?",
            "That's perfect",
            "Great",
            "I'm in"
        ]
    },
    {
        "name": "Soft → Deep exploration → Convert",
        "flow": [
            "I think BCA",
            "Tell me more details",
            "What about internships?",
            "What about study abroad?",
            "Perfect, I'm convinced"
        ]
    },
    {
        "name": "Soft → Market research → Proceed",
        "flow": [
            "Maybe BCA",
            "What's the job market like?",
            "Salary trends?",
            "Okay that's promising",
            "I'll go for it"
        ]
    },
    {
        "name": "Soft → Career path → Commit",
        "flow": [
            "I think BCA",
            "What careers can I pursue?",
            "Tell me about startup opportunity",
            "That's interesting",
            "Alright, signing up"
        ]
    },
    {
        "name": "Soft → Comparison deep dive → Choose",
        "flow": [
            "I'm thinking BCA",
            "How is it different from B.Tech?",
            "Career prospects comparison?",
            "BCA seems better",
            "Let's proceed"
        ]
    },
    {
        "name": "Soft → Practical concerns → Resolved → Proceed",
        "flow": [
            "I think BCA",
            "Can I work part-time?",
            "Is there flexible timing?",
            "Yes, that works",
            "I'm applying"
        ]
    },
    {
        "name": "Soft → Comparison paralysis",
        "flow": [
            "Maybe BCA",
            "Or BBA?",
            "Or B.Com?",
            "Tell me all options",
            "I can't decide"
        ]
    },
    {
        "name": "Soft → Family concern → Stall",
        "flow": [
            "I think BCA",
            "But I need to ask my parents",
            "Tell me about reputation first",
            "I'll discuss at home",
            "I'll get back to you"
        ]
    },
    {
        "name": "Soft → External factor → Defer",
        "flow": [
            "BCA seems good",
            "But I need to check something",
            "Tell me about entrance exams",
            "I need to prepare for that",
            "I'll come back later"
        ]
    },
    {
        "name": "Soft → Timing issue → No commitment",
        "flow": [
            "I think BCA",
            "When is the next batch?",
            "That's far away",
            "I need time to think",
            "I'll decide later"
        ]
    },
    {
        "name": "Soft → Unclear process → Abandon",
        "flow": [
            "I think BCA",
            "How do I actually apply?",
            "What's the process?",
            "That sounds complicated",
            "Maybe later"
        ]
    },
]

# ============================================================================
# Run Observations with REFINED Detection
# ============================================================================

print("=" * 80)
print("🔬 SOFT DECISION OUTCOME TRACKING - REFINED")
print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Detection: User continues relevant questions = RECOVERY")
print("=" * 80)

observations = []
hesitation_with_outcome = []

for scenario_idx, scenario in enumerate(SCENARIOS, 1):
    scenario_name = scenario["name"]
    flow = scenario["flow"]
    
    session_id = f"outcome_refined_{scenario_idx}"
    
    # Clear previous session
    if session_id in SESSION_MEMORY:
        del SESSION_MEMORY[session_id]
    
    context = {}
    soft_detected = False
    soft_turn = None
    hesitation_detected = False
    final_outcome = None
    
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
        is_hesitation = any(w in query.lower() for w in ["not sure", "unsure", "doubt", "second thought", "reconsider", "actually", "wait", "what if"])
        if soft_detected and turn_idx > soft_turn and is_hesitation:
            hesitation_detected = True
        
        # Refined detection: After hesitation, what does user do?
        if soft_detected and hesitation_detected and turn_idx > soft_turn and final_outcome is None:
            if is_recovery_signal(query):
                final_outcome = "RECOVERY"  # User asks relevant follow-up
            elif is_drop_signal(query):
                final_outcome = "DROP"  # User shows disengagement
        
        # Update context
        context = {"locked_course": profile.get("locked_course")}
    
    # Classify outcome
    if soft_detected and hesitation_detected:
        observation = {
            "scenario": scenario_idx,
            "name": scenario_name,
            "soft_detected": True,
            "hesitation_detected": True,
            "outcome": final_outcome or "ONGOING",
        }
        hesitation_with_outcome.append(observation)
    else:
        observation = {
            "scenario": scenario_idx,
            "name": scenario_name,
            "soft_detected": soft_detected,
            "hesitation_detected": False,
            "outcome": "N/A",
        }
    
    observations.append(observation)
    
    # Print summary
    if hesitation_detected:
        outcome_str = final_outcome or "ONGOING"
        icon = "✅" if outcome_str == "RECOVERY" else "❌" if outcome_str == "DROP" else "➡️"
        print(f"{icon} Scenario {scenario_idx:2d}: {outcome_str:10s} | {scenario_name}")
    else:
        print(f"➡️ Scenario {scenario_idx:2d}: no_hesitation  | {scenario_name}")

# ============================================================================
# Analysis
# ============================================================================

print("\n" + "=" * 80)
print("📊 REFINED OUTCOME ANALYSIS")
print("=" * 80)

if hesitation_with_outcome:
    recovery_count = sum(1 for o in hesitation_with_outcome if o["outcome"] == "RECOVERY")
    drop_count = sum(1 for o in hesitation_with_outcome if o["outcome"] == "DROP")
    ongoing_count = sum(1 for o in hesitation_with_outcome if o["outcome"] == "ONGOING")
    total_with_hesitation = len(hesitation_with_outcome)
    
    print(f"\nTotal scenarios with soft decision + hesitation: {total_with_hesitation}")
    print(f"  • RECOVERY (continues relevant questions): {recovery_count} ({recovery_count/total_with_hesitation*100:.1f}%)")
    print(f"  • DROP (disengages):                       {drop_count} ({drop_count/total_with_hesitation*100:.1f}%)")
    print(f"  • ONGOING (not yet determined):            {ongoing_count} ({ongoing_count/total_with_hesitation*100:.1f}%)")
    
    print(f"\n🎯 KEY METRIC: Recovery Rate = {recovery_count}/{total_with_hesitation} = {recovery_count/total_with_hesitation*100:.1f}%")
    
    if recovery_count >= drop_count:
        print(f"\n✅ VERDICT: Hesitation usually leads to RECOVERY (healthy)")
        print(f"   → Users question but ultimately continue engagement")
        print(f"   → System does NOT create lasting friction")
    else:
        print(f"\n🔴 VERDICT: Hesitation more often leads to DROP (problem)")
        print(f"   → System is causing abandonment")

else:
    print("\n⚠️  No hesitation cases detected with this refined measure")

print("\n" + "=" * 80)

# Save results
output = {
    "timestamp": datetime.now().isoformat(),
    "measurement_type": "REFINED",
    "recovery_definition": "User continues asking relevant course questions",
    "drop_definition": "User shows disengagement signals",
    "total_scenarios": len(observations),
    "scenarios_with_hesitation": len(hesitation_with_outcome),
    "recovery_count": recovery_count if hesitation_with_outcome else 0,
    "drop_count": drop_count if hesitation_with_outcome else 0,
    "ongoing_count": ongoing_count if hesitation_with_outcome else 0,
    "recovery_rate": f"{recovery_count/total_with_hesitation*100:.1f}%" if hesitation_with_outcome else "N/A",
    "observations": observations
}

with open("soft_decision_outcomes_refined.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"📁 Results saved to: soft_decision_outcomes_refined.json")
