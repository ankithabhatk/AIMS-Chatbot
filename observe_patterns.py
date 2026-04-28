#!/usr/bin/env python3
"""
Pattern Observer - Automated behavioral trace extraction
Runs conversations → captures debug → summarizes patterns
NO behavior changes, only observation
"""

import requests
import json

API_URL = "http://localhost:8000/api/v1/chat"

# Test conversation flows (simulated user behavior)
CONVERSATION_FLOWS = [
    # Flow 1: Exploration → Decision → Lock
    {
        "name": "exploration_to_decision",
        "queries": [
            "I got 75%",
            "tell me about BCA",
            "what about fees",
            "I think BCA is good"
        ]
    },
    # Flow 2: Vague → Fallback → Escalation
    {
        "name": "vague_to_escalation",
        "queries": [
            "tell me something",
            "what can you do",
            "help me please"
        ]
    },
    # Flow 3: Direct decision
    {
        "name": "direct_decision",
        "queries": [
            "I want to do MBA",
            "what are the fees",
            "how to apply"
        ]
    },
    # Flow 4: Locked → Repeated question
    {
        "name": "locked_repeated_question",
        "queries": [
            "I got 80% and like business",
            "BBA sounds good",
            "what about fees",
            "fees?",
            "tell me fees"
        ]
    },
    # Flow 5: Apply intent
    {
        "name": "apply_intent",
        "queries": [
            "I want BCA",
            "how to apply",
            "what documents needed"
        ]
    }
]

def run_conversation(flow):
    """Run a single conversation flow and capture debug traces"""
    session_id = f"observe-{flow['name']}"
    trace = []
    
    for query in flow["queries"]:
        try:
            response = requests.post(
                API_URL,
                json={"query": query, "session_id": session_id},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                debug = data.get("debug", {})
                
                trace.append({
                    "query": query,
                    "stage": debug.get("stage"),
                    "action": debug.get("action"),
                    "mode": debug.get("mode"),
                    "locked": debug.get("locked_course"),
                    "fallback_count": debug.get("fallback_count", 0),
                    "turn": debug.get("turn_count", 0)
                })
            else:
                trace.append({
                    "query": query,
                    "error": f"HTTP {response.status_code}"
                })
        except Exception as e:
            trace.append({
                "query": query,
                "error": str(e)
            })
    
    return trace

def summarize_trace(trace):
    """Extract behavioral pattern from trace"""
    stages = []
    locked_at = None
    escalated = False
    
    for i, turn in enumerate(trace, 1):
        if "error" in turn:
            continue
            
        stage = turn.get("stage") or "unknown"
        mode = turn.get("mode") or "unknown"
        locked = turn.get("locked")
        
        # Track when lock happens
        if locked and not locked_at:
            locked_at = i
        
        # Track escalation
        if mode == "escalation":
            escalated = True
        
        stages.append(stage)
    
    return {
        "flow": " → ".join(stages),
        "locked_at_turn": locked_at,
        "escalated": escalated,
        "total_turns": len(trace)
    }

def print_pattern_summary(flow_name, trace, summary):
    """Print human-readable pattern summary"""
    print(f"\n{'='*70}")
    print(f"FLOW: {flow_name}")
    print(f"{'='*70}")
    print(f"Pattern: {summary['flow']}")
    
    if summary['locked_at_turn']:
        print(f"Locked: Turn {summary['locked_at_turn']}")
    
    if summary['escalated']:
        print(f"Escalated: Yes")
    
    print(f"\nDetailed trace:")
    for turn in trace:
        if "error" in turn:
            print(f"  Turn: '{turn['query']}' → ERROR: {turn['error']}")
        else:
            locked_indicator = f" [LOCKED: {turn['locked']}]" if turn['locked'] else ""
            fallback_indicator = f" [FB:{turn['fallback_count']}]" if turn['fallback_count'] > 0 else ""
            print(f"  Turn {turn['turn']}: '{turn['query']}'")
            print(f"    → stage={turn['stage']}, action={turn['action']}, mode={turn['mode']}{locked_indicator}{fallback_indicator}")

def main():
    """Run observer - collect behavioral patterns"""
    print("🔍 Pattern Observer - Starting automated observation")
    print(f"Running {len(CONVERSATION_FLOWS)} conversation flows...\n")
    
    all_patterns = []
    
    for flow in CONVERSATION_FLOWS:
        trace = run_conversation(flow)
        summary = summarize_trace(trace)
        all_patterns.append({
            "name": flow["name"],
            "trace": trace,
            "summary": summary
        })
        
        print_pattern_summary(flow["name"], trace, summary)
    
    # Print aggregate summary
    print(f"\n{'='*70}")
    print("AGGREGATE PATTERNS")
    print(f"{'='*70}")
    
    for pattern in all_patterns:
        print(f"{pattern['name']:30} → {pattern['summary']['flow']}")
    
    print(f"\n✅ Observation complete - {len(all_patterns)} flows analyzed")

if __name__ == "__main__":
    main()
