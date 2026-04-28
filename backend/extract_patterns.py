"""
Extract Top 5 Patterns for Analysis

This extracts the critical patterns from real chat logs:
1. Top 5 drop-off queries
2. Top 5 sentiment conflict (but converted)
3. Top 5 clarification → drop
4. Top 5 fast conversions
5. Top 5 engaged_no_conversion (hidden failure)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.counselor.production_analytics import ANALYTICS_STORE
from collections import Counter

def extract_top_dropoff_queries(limit=5):
    """
    Extract queries that led to drops.
    
    These indicate real confusion or frustration.
    """
    dropoff_queries = [
        event["query"] for event in ANALYTICS_STORE["sentiment_conflicts"]
        if event["outcome"] in ["dropped", "engaged_no_conversion"]
    ]
    
    return Counter(dropoff_queries).most_common(limit)


def extract_top_converted_despite_conflict(limit=5):
    """
    Extract queries that had sentiment conflict but converted.
    
    These are high-intent users we're blocking.
    Shows outcome journey to see if they struggled first.
    """
    converted_queries = []
    
    for event in ANALYTICS_STORE["sentiment_conflicts"]:
        if event["outcome"] == "converted":
            outcome_journey = " → ".join(event.get("outcome_history", [event["outcome"]]))
            converted_queries.append({
                "query": event["query"],
                "journey": outcome_journey,
                "bypassed": event.get("bypassed", False)
            })
    
    # Group by query and count
    from collections import defaultdict
    query_counts = defaultdict(list)
    for item in converted_queries:
        query_counts[item["query"]].append(item)
    
    # Sort by count
    sorted_queries = sorted(query_counts.items(), key=lambda x: len(x[1]), reverse=True)
    
    return sorted_queries[:limit]


def extract_top_clarification_drops(limit=5):
    """
    Extract clarifications that led to drops.
    
    These clarifications killed momentum.
    """
    clarification_drops = []
    
    for event in ANALYTICS_STORE["clarification_responses"]:
        if event["outcome"] in ["dropped", "engaged_no_conversion"]:
            # Find the corresponding clarification event
            session_id = event["session_id"]
            clarification_drops.append(session_id)
    
    return Counter(clarification_drops).most_common(limit)


def extract_top_fast_conversions(limit=5):
    """
    Extract sessions that converted quickly (<5 turns).
    
    These users knew what they wanted.
    """
    fast_conversions = []
    
    for session_id, session in ANALYTICS_STORE["sessions"].items():
        if session.get("applied") and session["turn_count"] < 5:
            fast_conversions.append({
                "session_id": session_id,
                "turns": session["turn_count"],
                "course": session.get("locked_course", "unknown")
            })
    
    return sorted(fast_conversions, key=lambda x: x["turns"])[:limit]


def extract_top_engaged_no_conversion(limit=5):
    """
    Extract sessions with high engagement but no conversion.
    
    These are hidden failures (UX problem, not logic problem).
    """
    engaged_no_conversion = []
    
    for session_id, session in ANALYTICS_STORE["sessions"].items():
        if not session.get("applied") and session["turn_count"] > 3:
            engaged_no_conversion.append({
                "session_id": session_id,
                "turns": session["turn_count"],
                "last_stage": session["stages"][-1]["stage"] if session["stages"] else "unknown"
            })
    
    return sorted(engaged_no_conversion, key=lambda x: x["turns"], reverse=True)[:limit]


def print_analysis():
    """Print formatted analysis for human review"""
    print("\n" + "=" * 60)
    print("TOP 5 PATTERN ANALYSIS")
    print("=" * 60)
    
    print("\n🔴 TOP 5 DROP-OFF QUERIES:")
    print("(These indicate real confusion or frustration)")
    dropoffs = extract_top_dropoff_queries()
    for i, (query, count) in enumerate(dropoffs, 1):
        print(f"  {i}. \"{query}\" ({count} times)")
    
    print("\n✅ TOP 5 SENTIMENT CONFLICT (BUT CONVERTED):")
    print("(High-intent users we're blocking)")
    converted = extract_top_converted_despite_conflict()
    for i, (query, events) in enumerate(converted, 1):
        count = len(events)
        # Show outcome journey for first event
        journey = events[0]["journey"] if events else "unknown"
        bypassed = events[0]["bypassed"] if events else False
        print(f"  {i}. \"{query}\" ({count} times)")
        print(f"      Journey: {journey}")
        print(f"      Bypassed: {bypassed}")
    
    print("\n⚠️  TOP 5 CLARIFICATION → DROP:")
    print("(Clarifications that killed momentum)")
    clarification_drops = extract_top_clarification_drops()
    for i, (session_id, count) in enumerate(clarification_drops, 1):
        print(f"  {i}. Session {session_id} ({count} clarifications)")
    
    print("\n⚡ TOP 5 FAST CONVERSIONS:")
    print("(Users who knew what they wanted)")
    fast = extract_top_fast_conversions()
    for i, conv in enumerate(fast, 1):
        print(f"  {i}. {conv['turns']} turns → {conv['course']} (session: {conv['session_id']})")
    
    print("\n🚨 TOP 5 ENGAGED (NO CONVERSION):")
    print("(Hidden failures - UX problem, not logic problem)")
    engaged = extract_top_engaged_no_conversion()
    for i, eng in enumerate(engaged, 1):
        print(f"  {i}. {eng['turns']} turns, stopped at {eng['last_stage']} (session: {eng['session_id']})")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print_analysis()
