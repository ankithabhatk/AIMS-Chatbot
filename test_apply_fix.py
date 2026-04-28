#!/usr/bin/env python3
"""
Post-Fix Measurement: "How do I apply?" Response Clarity
Test: 5-10 post-lock apply queries
Measure: Does improved response clarity reduce confusion?
"""

import sys
import json
from datetime import datetime

sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.orchestration.engine import run_counselor_pipeline
from app.services.counselor.memory import get_student_profile, SESSION_MEMORY

# Test scenarios: Lock course, then ask "How do I apply?"
TEST_SCENARIOS = [
    {
        "name": "BCA Apply Query",
        "flow": [
            "I like coding",
            "I think BCA",  # LOCK
            "How do I apply?"
        ]
    },
    {
        "name": "BBA Apply Query",
        "flow": [
            "I'm interested in business",
            "I'll go with BBA",  # LOCK
            "What's the process to apply?"
        ]
    },
    {
        "name": "B.Com Apply Query",
        "flow": [
            "Commerce interests me",
            "I think B.Com is good",  # LOCK
            "How to apply for B.Com?"
        ]
    },
    {
        "name": "Apply Steps Query",
        "flow": [
            "I want engineering",
            "I think BTech",  # LOCK
            "Tell me the steps to apply"
        ]
    },
    {
        "name": "Application Process Query",
        "flow": [
            "I'm thinking about MBA",
            "I'll do MBA",  # LOCK
            "What's the application procedure?"
        ]
    },
    {
        "name": "Direct Apply Query",
        "flow": [
            "Tell me about BCA",
            "I think BCA is my choice",  # LOCK
            "I'm ready to apply"
        ]
    },
    {
        "name": "Immediate Apply Query",
        "flow": [
            "What courses",
            "I think BBA",  # LOCK
            "How do I start applying?"
        ]
    },
    {
        "name": "Apply Guidance Query",
        "flow": [
            "BCA interests me",
            "I'll go with BCA",  # LOCK
            "I need guidance to apply"
        ]
    },
    {
        "name": "Apply Steps Detailed",
        "flow": [
            "I like technology",
            "I think BCA is good",  # LOCK
            "Walk me through the apply process"
        ]
    },
    {
        "name": "How to Start Apply",
        "flow": [
            "Interested in coding",
            "I think BCA",  # LOCK
            "Where do I start the application?"
        ]
    },
]

print("=" * 80)
print("📊 POST-FIX MEASUREMENT: Apply Response Clarity")
print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Scenarios: {len(TEST_SCENARIOS)}")
print("=" * 80)

measurements = []

for scenario_idx, scenario in enumerate(TEST_SCENARIOS, 1):
    scenario_name = scenario["name"]
    flow = scenario["flow"]
    
    session_id = f"apply_test_{scenario_idx}"
    
    # Clear previous session
    if session_id in SESSION_MEMORY:
        del SESSION_MEMORY[session_id]
    
    context = {}
    
    for turn_idx, query in enumerate(flow, 1):
        try:
            response = run_counselor_pipeline(query, session_id=session_id, context=context)
            if response is None:
                continue
        except Exception as e:
            continue
        
        profile = get_student_profile(session_id)
        
        # Capture final apply response
        if turn_idx == len(flow):  # Last turn - the apply question
            final_response = response.get("answer", "")
            mode = response.get("mode")
            
            # Measure: Is response action-first?
            has_clear_cta = "👉" in final_response or "start" in final_response.lower() or "next" in final_response.lower()
            has_time_estimate = "10 minute" in final_response.lower() or "~10" in final_response
            has_doc_list = "mark" in final_response.lower() or "id" in final_response.lower()
            has_support = "help" in final_response.lower() or "question" in final_response.lower()
            
            measurement = {
                "scenario": scenario_idx,
                "name": scenario_name,
                "mode": mode,
                "has_clear_cta": has_clear_cta,
                "has_time_estimate": has_time_estimate,
                "has_doc_list": has_doc_list,
                "has_support": has_support,
                "clarity_score": sum([has_clear_cta, has_time_estimate, has_doc_list, has_support]) / 4,
                "response_preview": final_response[:150]
            }
            
            measurements.append(measurement)
        
        # Update context
        context = {"locked_course": profile.get("locked_course")}
    
    # Print result
    clarity = measurements[-1]["clarity_score"] if measurements else 0
    icon = "✅" if clarity >= 0.75 else "⚠️" if clarity >= 0.5 else "❌"
    print(f"{icon} Scenario {scenario_idx:2d}: {scenario_name:30s} | Clarity: {clarity:.1%} | Mode: {measurements[-1]['mode']}")

# Analysis
print("\n" + "=" * 80)
print("📊 CLARITY ANALYSIS")
print("=" * 80)

avg_clarity = sum(m["clarity_score"] for m in measurements) / len(measurements) if measurements else 0
cta_count = sum(1 for m in measurements if m["has_clear_cta"])
time_count = sum(1 for m in measurements if m["has_time_estimate"])
doc_count = sum(1 for m in measurements if m["has_doc_list"])
support_count = sum(1 for m in measurements if m["has_support"])

print(f"\nAverage Clarity Score: {avg_clarity:.1%}")
print(f"\nComponent Presence:")
print(f"  • Clear CTA (👉 / Start):      {cta_count}/{len(measurements)}")
print(f"  • Time estimate (~10 min):     {time_count}/{len(measurements)}")
print(f"  • Document requirements:        {doc_count}/{len(measurements)}")
print(f"  • Support/help offered:         {support_count}/{len(measurements)}")

if avg_clarity >= 0.75:
    print(f"\n✅ VERDICT: Responses have high clarity")
    print(f"   → Users should understand next action")
    print(f"   → Should reduce repetitive questions")
elif avg_clarity >= 0.5:
    print(f"\n⚠️  VERDICT: Responses have medium clarity")
    print(f"   → Some elements missing from structure")
else:
    print(f"\n❌ VERDICT: Responses lack clarity")
    print(f"   → May still cause confusion")

print("\n" + "=" * 80)

# Save results
output = {
    "timestamp": datetime.now().isoformat(),
    "test_type": "post-fix_apply_clarity",
    "total_tests": len(measurements),
    "average_clarity": avg_clarity,
    "cta_presence": cta_count,
    "time_estimate_presence": time_count,
    "doc_list_presence": doc_count,
    "support_presence": support_count,
    "measurements": measurements
}

with open("postfix_apply_clarity.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"📁 Results saved to: postfix_apply_clarity.json")
