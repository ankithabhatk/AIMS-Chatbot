#!/usr/bin/env python3
"""
Real Chat Simulation - Soft Decision Pattern Observation
Run: 20-30 conversations with soft decision language
Capture: Query | Stage | Locked? | Outcome (hesitation/drop vs continuation)
"""

import sys
import json
from datetime import datetime

sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.orchestration.engine import run_counselor_pipeline
from app.services.counselor.memory import get_student_profile, SESSION_MEMORY

# Soft decision language patterns to test
SOFT_DECISIONS = [
    "I think BCA might be good",
    "maybe BCA is the right choice",
    "BCA seems interesting",
    "probably BCA",
    "I'm leaning towards BCA",
    "BCA could work",
    "I think BCA",
]

# Real chat flows (each is a conversation journey)
CHAT_SCENARIOS = [
    # Scenario 1: Soft commitment, then asks more questions (continuation)
    {
        "name": "Soft commit + deepening",
        "flow": [
            "What courses do you offer?",
            "Tell me about BCA and BBA",
            "I think BCA might be good",
            "What's the placement record?",
            "How much does it cost?"
        ]
    },
    # Scenario 2: Soft commitment, then comparison (continuation)
    {
        "name": "Soft commit + comparison",
        "flow": [
            "I'm interested in coding",
            "Tell me more about BCA",
            "I think BCA could work",
            "But how does it compare to B.Tech?",
            "When can I apply?"
        ]
    },
    # Scenario 3: Generic → soft commit (continuation)
    {
        "name": "Generic to soft commit",
        "flow": [
            "I want to study engineering",
            "What's the best course?",
            "I'm leaning towards BCA",
            "Tell me about fees",
            "Can I apply online?"
        ]
    },
    # Scenario 4: Multiple soft decisions (pattern watch)
    {
        "name": "Hesitant progression",
        "flow": [
            "I like business and coding",
            "Maybe BCA is right",
            "Or should I do BBA?",
            "I think BCA might be better",
            "Let me think about it"
        ]
    },
    # Scenario 5: Soft commit with doubt reversal
    {
        "name": "Soft commit then backtrack",
        "flow": [
            "BCA seems interesting",
            "I think I'll do BCA",
            "Actually, tell me about MBA",
            "Is MBA better than BCA?",
            "I'm not sure now"
        ]
    },
    # Scenario 6: Quick soft decision
    {
        "name": "Quick soft decision",
        "flow": [
            "What's your top course?",
            "I think BCA is good",
            "How do I apply?",
            "What documents do I need?"
        ]
    },
    # Scenario 7: Interest → soft decision → action
    {
        "name": "Interest to action",
        "flow": [
            "I like coding",
            "Which course teaches that?",
            "I think BCA is probably the one",
            "Okay, how do I get started?"
        ]
    },
    # Scenario 8: Cautious exploration
    {
        "name": "Cautious with soft commit",
        "flow": [
            "I'm not sure what to study",
            "Tell me about your options",
            "Maybe BCA could work for me",
            "What's the duration?",
            "Is it worth it?"
        ]
    },
    # Scenario 9: Multiple interests + soft choice
    {
        "name": "Multiple + soft decision",
        "flow": [
            "I like both finance and coding",
            "Which course fits?",
            "I think BCA might be better for coding",
            "Tell me more about placements",
            "I'm ready to apply"
        ]
    },
    # Scenario 10: Soft decision with price sensitivity
    {
        "name": "Cost-conscious soft commit",
        "flow": [
            "What courses are available?",
            "I think BCA is good",
            "But how much does it cost?",
            "Is there financial aid?",
            "Okay, I can manage that"
        ]
    },
]

# ============================================================================
# Run Observations
# ============================================================================

print("=" * 80)
print("🔬 SOFT DECISION PATTERN OBSERVATION")
print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Scenarios: {len(CHAT_SCENARIOS)}")
print("=" * 80)

observations = []

for scenario_idx, scenario in enumerate(CHAT_SCENARIOS, 1):
    scenario_name = scenario["name"]
    flow = scenario["flow"]
    
    print(f"\n{'─' * 80}")
    print(f"SCENARIO {scenario_idx}: {scenario_name}")
    print(f"{'─' * 80}")
    
    session_id = f"soft_decision_{scenario_idx}"
    
    # Clear previous session
    if session_id in SESSION_MEMORY:
        del SESSION_MEMORY[session_id]
    
    scenario_observation = {
        "scenario_id": scenario_idx,
        "scenario_name": scenario_name,
        "flow": flow,
        "turns": [],
        "soft_decision_detected": False,
        "soft_decision_index": None,
        "locked_after_soft": None,
        "hesitation_after_soft": None,
        "final_outcome": None
    }
    
    context = {}
    
    for turn_idx, query in enumerate(flow, 1):
        try:
            response = run_counselor_pipeline(query, session_id=session_id, context=context)
            if response is None:
                print(f"  Turn {turn_idx}: {query}")
                print(f"    → ERROR: Engine returned None (skip this turn)")
                continue
        except Exception as e:
            print(f"  Turn {turn_idx}: {query}")
            print(f"    → ERROR: {str(e)[:80]} (skip this turn)")
            continue
            
        profile = get_student_profile(session_id)
        
        # Check if this is a soft decision query
        is_soft_decision = any(
            pattern.lower() in query.lower() 
            for pattern in ["i think", "maybe", "seem", "probably", "leaning", "could work"]
        )
        
        turn_data = {
            "turn": turn_idx,
            "query": query,
            "is_soft_decision": is_soft_decision,
            "mode": response.get("mode") if response else "error",
            "confidence": response.get("confidence") if response else 0,
            "locked_course": profile.get("locked_course"),
            "intents": response.get("intents") if response else [],
        }
        
        # Log detection of soft decision
        if is_soft_decision and not scenario_observation["soft_decision_detected"]:
            scenario_observation["soft_decision_detected"] = True
            scenario_observation["soft_decision_index"] = turn_idx
            scenario_observation["locked_after_soft"] = profile.get("locked_course")
        
        # Check for hesitation after soft decision
        if scenario_observation["soft_decision_detected"] and turn_idx > scenario_observation["soft_decision_index"]:
            query_lower = query.lower()
            if any(word in query_lower for word in ["not sure", "maybe not", "actually", "reconsider", "change", "different", "doubt"]):
                scenario_observation["hesitation_after_soft"] = True
        
        scenario_observation["turns"].append(turn_data)
        
        print(f"\n  Turn {turn_idx}: {query}")
        print(f"    → Mode: {response.get('mode')}")
        print(f"    → Locked: {profile.get('locked_course')}")
        if is_soft_decision:
            print(f"    ⚠️  SOFT DECISION DETECTED")
        
        # Update context
        context = {
            "locked_course": profile.get("locked_course"),
            "courses": profile.get("courses", []),
        }
    
    # Determine final outcome
    if scenario_observation["soft_decision_detected"]:
        if scenario_observation["hesitation_after_soft"]:
            scenario_observation["final_outcome"] = "PATTERN_A"  # soft decision → hesitation → drop
            outcome_label = "⚠️  PATTERN A (Soft → Hesitation → Drop)"
        else:
            scenario_observation["final_outcome"] = "PATTERN_B"  # soft decision → continues
            outcome_label = "✅ PATTERN B (Soft → Continues)"
    else:
        scenario_observation["final_outcome"] = "NO_SOFT_DECISION"
        outcome_label = "N/A (No soft decision in flow)"
    
    print(f"\n  Final Outcome: {outcome_label}")
    print(f"  Soft decision locked to: {scenario_observation['locked_after_soft']}")
    
    observations.append(scenario_observation)

# ============================================================================
# Analysis
# ============================================================================

print("\n" + "=" * 80)
print("📊 PATTERN ANALYSIS")
print("=" * 80)

pattern_a_count = sum(1 for o in observations if o["final_outcome"] == "PATTERN_A")
pattern_b_count = sum(1 for o in observations if o["final_outcome"] == "PATTERN_B")
no_soft_count = sum(1 for o in observations if o["final_outcome"] == "NO_SOFT_DECISION")

print(f"\nPattern A (Soft → Hesitation): {pattern_a_count}/{len(observations)}")
print(f"Pattern B (Soft → Continues): {pattern_b_count}/{len(observations)}")
print(f"No soft decision: {no_soft_count}/{len(observations)}")

if pattern_a_count > pattern_b_count:
    print(f"\n🔴 DOMINANT PATTERN: A (Hesitation occurs {pattern_a_count}x)")
    print("   → System is causing user doubt after soft decisions")
elif pattern_b_count >= pattern_a_count:
    print(f"\n🟢 DOMINANT PATTERN: B (Continuation occurs {pattern_b_count}x)")
    print("   → System handles soft decisions without pushing hesitation")

# Show which scenarios had issues
print("\n" + "─" * 80)
print("PATTERN A SCENARIOS (requiring attention):")
print("─" * 80)

pattern_a_scenarios = [o for o in observations if o["final_outcome"] == "PATTERN_A"]
if pattern_a_scenarios:
    for scenario in pattern_a_scenarios:
        print(f"  • {scenario['scenario_name']}")
        print(f"    Soft decision: Turn {scenario['soft_decision_index']}")
        print(f"    Hesitation appeared: Turn {scenario['soft_decision_index'] + 1}+")
else:
    print("  (None detected - healthy)")

# Save results
output = {
    "timestamp": datetime.now().isoformat(),
    "total_scenarios": len(observations),
    "pattern_a_count": pattern_a_count,
    "pattern_b_count": pattern_b_count,
    "no_soft_count": no_soft_count,
    "dominant_pattern": "A" if pattern_a_count > pattern_b_count else "B",
    "observations": observations
}

with open("soft_decision_observations.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\n📁 Results saved to: soft_decision_observations.json")
print("=" * 80)
