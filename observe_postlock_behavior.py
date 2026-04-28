#!/usr/bin/env python3
"""
Post-Lock Behavior Observation
Phase 2: Conversion friction AFTER course lock
Watch for:
- Locked → no apply action
- Locked → repetitive questions
- Locked → confusion about next step
"""

import sys
import json
from datetime import datetime

sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.orchestration.engine import run_counselor_pipeline
from app.services.counselor.memory import get_student_profile, SESSION_MEMORY

# Post-lock scenarios: user has decided, course is locked, what happens next?
POSTLOCK_SCENARIOS = [
    # Group 1: Smooth apply flow (baseline)
    {
        "name": "Lock → Immediate apply",
        "flow": [
            "I like coding",
            "I think BCA is good",  # LOCK happens here
            "How do I apply?",
            "What documents?"
        ],
        "expected": "smooth"
    },
    {
        "name": "Lock → One question → Apply",
        "flow": [
            "BCA interested me",
            "I'll go with BCA",  # LOCK
            "When can I start?",
            "I'm ready to apply"
        ],
        "expected": "smooth"
    },
    {
        "name": "Lock → Fees check → Apply",
        "flow": [
            "I think BCA",  # LOCK
            "What's the fee?",
            "That works",
            "Let's apply"
        ],
        "expected": "smooth"
    },
    # Group 2: Repetitive questions (friction signal)
    {
        "name": "Lock → Same question 3x",
        "flow": [
            "I think BCA",  # LOCK
            "Tell me about placements",
            "But what about placements specifically?",
            "Can you tell me placement stats again?",
            "When do I apply?"
        ],
        "expected": "friction"
    },
    {
        "name": "Lock → Fee confusion",
        "flow": [
            "I think BCA",  # LOCK
            "What's the fee?",
            "Is that total or per semester?",
            "Per semester fee again?",
            "How much total?"
        ],
        "expected": "friction"
    },
    {
        "name": "Lock → Unclear process",
        "flow": [
            "I'll do BCA",  # LOCK
            "How do I apply?",
            "What's the first step?",
            "Do I apply online or offline?",
            "What exactly do I need to do?"
        ],
        "expected": "friction"
    },
    # Group 3: Abandonment signals (drop risk)
    {
        "name": "Lock → No next step",
        "flow": [
            "I think BCA",  # LOCK
            "Okay",
            "...",
            "I'll come back"
        ],
        "expected": "abandon"
    },
    {
        "name": "Lock → Overwhelm",
        "flow": [
            "I'm thinking BCA",  # LOCK
            "How do I apply?",
            "What documents?",
            "When's the deadline?",
            "This is too much"
        ],
        "expected": "abandon"
    },
    {
        "name": "Lock → Distraction",
        "flow": [
            "I think BCA",  # LOCK
            "Tell me about hostel",
            "What about food?",
            "Campus location?",
            "Never mind the application"
        ],
        "expected": "abandon"
    },
    # Group 4: Hesitation after lock (reconsideration)
    {
        "name": "Lock → Doubt → Reaffirm",
        "flow": [
            "I'll do BCA",  # LOCK
            "Wait, is this right?",
            "Tell me about job prospects",
            "Okay, that's good",
            "I'm applying"
        ],
        "expected": "recovery"
    },
    {
        "name": "Lock → Alternative → Return",
        "flow": [
            "I think BCA",  # LOCK
            "What about BBA?",
            "Compare BCA vs BBA",
            "Actually BCA is better",
            "How to apply?"
        ],
        "expected": "recovery"
    },
    {
        "name": "Lock → Family check → Proceed",
        "flow": [
            "I'm going with BCA",  # LOCK
            "I need to ask my parents",
            "Tell me salary range",
            "My parents are okay",
            "I'm ready now"
        ],
        "expected": "recovery"
    },
    # Group 5: Clear apply intent progression
    {
        "name": "Lock → Eligibility → Apply",
        "flow": [
            "I think BCA",  # LOCK
            "Am I eligible?",
            "What are requirements?",
            "Great, I qualify",
            "Apply now"
        ],
        "expected": "smooth"
    },
    {
        "name": "Lock → Admission steps",
        "flow": [
            "I'll do BCA",  # LOCK
            "What's the admission process?",
            "How many steps?",
            "Got it",
            "Starting now"
        ],
        "expected": "smooth"
    },
    {
        "name": "Lock → Timeline check → Apply",
        "flow": [
            "BCA for me",  # LOCK
            "How long does it take?",
            "When can I start?",
            "Perfect timing",
            "I'm applying"
        ],
        "expected": "smooth"
    },
    # Group 6: Conversion-killing friction
    {
        "name": "Lock → Form confusion",
        "flow": [
            "I think BCA",  # LOCK
            "How do I fill the form?",
            "What's the application form?",
            "Where's the link?",
            "Can't find it"
        ],
        "expected": "abandon"
    },
    {
        "name": "Lock → Document confusion",
        "flow": [
            "I'll do BCA",  # LOCK
            "What documents needed?",
            "Do I need certificates?",
            "Original or copy?",
            "I need to get these"
        ],
        "expected": "abandon"
    },
    {
        "name": "Lock → Deadline panic",
        "flow": [
            "I think BCA",  # LOCK
            "When's the deadline?",
            "Is it soon?",
            "That's too soon",
            "I can't apply now"
        ],
        "expected": "abandon"
    },
    # Group 7: Smooth conversions
    {
        "name": "Lock → Clear action path",
        "flow": [
            "I think BCA",  # LOCK
            "What's next?",
            "Tell me steps",
            "I understand",
            "Starting application"
        ],
        "expected": "smooth"
    },
    {
        "name": "Lock → Direct to apply",
        "flow": [
            "I'll go with BCA",  # LOCK
            "Take me to apply",
            "Checking requirements",
            "I'm eligible",
            "Submitted"
        ],
        "expected": "smooth"
    },
]

# Detection keywords
APPLY_KEYWORDS = ["apply", "application", "form", "submit", "submitted", "starting", "beginning", "link"]
FRICTION_KEYWORDS = ["same", "again", "still", "confused", "unclear", "what", "how", "can't find", "where"]
ABANDON_KEYWORDS = ["too much", "too soon", "can't", "later", "need to get", "complicated", "i need time"]
REAFFIRM_KEYWORDS = ["okay", "good", "that helps", "convinced", "understand", "great", "perfect"]

def detect_action_taken(flow):
    """Did user take action towards apply?"""
    return any(keyword in flow[-1].lower() for keyword in APPLY_KEYWORDS)

def detect_friction(flow):
    """Are there repetitive or confused questions?"""
    questions = [q for q in flow if "?" in q]
    return len(questions) > len(flow) * 0.5  # >50% questions = friction

def detect_abandon(flow):
    """Did user show abandon signals?"""
    return any(keyword in flow[-1].lower() for keyword in ABANDON_KEYWORDS)

# ============================================================================
# Run Observations
# ============================================================================

print("=" * 80)
print("🔬 POST-LOCK BEHAVIOR OBSERVATION")
print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Scenarios: {len(POSTLOCK_SCENARIOS)}")
print("=" * 80)

observations = []
behavioral_classification = {
    "smooth": [],
    "friction": [],
    "recovery": [],
    "abandon": []
}

for scenario_idx, scenario in enumerate(POSTLOCK_SCENARIOS, 1):
    scenario_name = scenario["name"]
    flow = scenario["flow"]
    expected = scenario["expected"]
    
    session_id = f"postlock_{scenario_idx}"
    
    # Clear previous session
    if session_id in SESSION_MEMORY:
        del SESSION_MEMORY[session_id]
    
    context = {}
    locked_course = None
    lock_turn = None
    
    for turn_idx, query in enumerate(flow, 1):
        try:
            response = run_counselor_pipeline(query, session_id=session_id, context=context)
            if response is None:
                continue
        except Exception as e:
            continue
        
        profile = get_student_profile(session_id)
        
        # Track when lock happens
        if profile.get("locked_course") and not locked_course:
            locked_course = profile.get("locked_course")
            lock_turn = turn_idx
        
        # Update context
        context = {"locked_course": profile.get("locked_course")}
    
    # Classify outcome
    action_taken = detect_action_taken(flow)
    has_friction = detect_friction(flow)
    is_abandon = detect_abandon(flow)
    
    if action_taken and not has_friction:
        actual = "smooth"
    elif has_friction and not is_abandon:
        actual = "friction"
    elif is_abandon:
        actual = "abandon"
    else:
        actual = "recovery"  # continued but no action yet
    
    observation = {
        "scenario": scenario_idx,
        "name": scenario_name,
        "expected": expected,
        "actual": actual,
        "locked": locked_course is not None,
        "action_taken": action_taken,
        "has_friction": has_friction,
        "abandoned": is_abandon,
    }
    
    observations.append(observation)
    behavioral_classification[actual].append(scenario_idx)
    
    # Print summary
    icon = "✅" if actual == expected else "⚠️" if actual == "friction" else "❌" if actual == "abandon" else "➡️"
    match = "✓" if actual == expected else "✗"
    print(f"{icon} {match} Scenario {scenario_idx:2d}: {actual:10s} | Expected: {expected:10s} | {scenario_name}")

# ============================================================================
# Analysis
# ============================================================================

print("\n" + "=" * 80)
print("📊 POST-LOCK BEHAVIOR ANALYSIS")
print("=" * 80)

total = len(observations)
smooth = len(behavioral_classification["smooth"])
friction = len(behavioral_classification["friction"])
recovery = len(behavioral_classification["recovery"])
abandon = len(behavioral_classification["abandon"])

print(f"\nTotal post-lock scenarios: {total}")
print(f"  • Smooth → Apply:        {smooth} ({smooth/total*100:.1f}%)")
print(f"  • Friction (confused):   {friction} ({friction/total*100:.1f}%)")
print(f"  • Recovery (hesitate→go):{recovery} ({recovery/total*100:.1f}%)")
print(f"  • Abandon:               {abandon} ({abandon/total*100:.1f}%)")

print(f"\n🎯 CONVERSION RATE (smooth + recovery): {(smooth + recovery)/total*100:.1f}%")
print(f"🎯 FRICTION RATE: {friction/total*100:.1f}%")
print(f"🎯 ABANDON RATE: {abandon/total*100:.1f}%")

if abandon > friction:
    print(f"\n🔴 ISSUE: Abandonment dominates")
    print(f"   → Users are dropping after locking")
    print(f"   → Likely: unclear apply process / form complexity")
elif friction > smooth:
    print(f"\n🟡 ISSUE: Friction dominates smooth flow")
    print(f"   → Users confused even after deciding")
    print(f"   → Likely: unclear next steps / repetitive answering")
else:
    print(f"\n✅ HEALTHY: Smooth conversions dominate")
    print(f"   → Most users apply after deciding")

# Show friction patterns
if friction > 0:
    print(f"\n{'-'*80}")
    print("FRICTION SCENARIOS (repeated questions):")
    print(f"{'-'*80}")
    friction_scenarios = [o for o in observations if o["actual"] == "friction"]
    for scenario in friction_scenarios:
        print(f"  • {scenario['name']}")

# Show abandon patterns
if abandon > 0:
    print(f"\n{'-'*80}")
    print("ABANDON SCENARIOS (drop-off points):")
    print(f"{'-'*80}")
    abandon_scenarios = [o for o in observations if o["actual"] == "abandon"]
    for scenario in abandon_scenarios:
        print(f"  • {scenario['name']}")

print("\n" + "=" * 80)

# Save results
output = {
    "timestamp": datetime.now().isoformat(),
    "total_scenarios": total,
    "smooth_count": smooth,
    "friction_count": friction,
    "recovery_count": recovery,
    "abandon_count": abandon,
    "conversion_rate": f"{(smooth + recovery)/total*100:.1f}%",
    "friction_rate": f"{friction/total*100:.1f}%",
    "abandon_rate": f"{abandon/total*100:.1f}%",
    "observations": observations
}

with open("postlock_behavior_observations.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"📁 Results saved to: postlock_behavior_observations.json")
