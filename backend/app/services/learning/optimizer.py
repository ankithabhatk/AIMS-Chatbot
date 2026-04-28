from typing import Dict, List
from app.services.counselor.analytics import get_analytics

SYSTEM_TUNING = {
    "guidance_style": "balanced",
    "cta_style": "normal",
    "inject_social_proof": False,
    "force_simplification": False,
    "focus_stage": None
}

SUCCESS_PATTERNS = []

def aggregate_metrics(events: List[Dict]) -> Dict:
    stats = {
        "decision_rate": 0,
        "permission_rate": 0,
        "conversion_rate": 0,
        "drop_stages": {},
        "confusion_rate": 0
    }
    total = len(events)
    if total == 0:
        return stats
        
    for e in events:
        evt_type = e.get("event")
        if evt_type == "decision_hit":
            stats["decision_rate"] += 1
        elif evt_type == "permission_granted":
            stats["permission_rate"] += 1
        elif evt_type == "conversion_complete":
            stats["conversion_rate"] += 1
        elif evt_type == "drop_off":
            stage = e.get("data", {}).get("stage", "unknown")
            stats["drop_stages"][stage] = stats["drop_stages"].get(stage, 0) + 1
        elif evt_type == "confusion_loop":
            stats["confusion_rate"] += 1
            
    # Normalize
    stats["decision_rate"] /= total
    stats["permission_rate"] /= max(1, stats["decision_rate"])
    stats["conversion_rate"] /= total
    stats["confusion_rate"] /= total
    return stats

def generate_rule_updates(stats: Dict) -> Dict:
    updates = {}
    if stats["decision_rate"] < 0.3:
        updates["guidance_style"] = "more_direct"
    else:
        updates["guidance_style"] = "balanced"
        
    if stats["permission_rate"] < 0.3:
        updates["cta_style"] = "soft"
    else:
        updates["cta_style"] = "normal"
        
    if stats["conversion_rate"] < 0.1:
        updates["inject_social_proof"] = True
    else:
        updates["inject_social_proof"] = False
        
    if stats["confusion_rate"] > 0.2:
        updates["force_simplification"] = True
    else:
        updates["force_simplification"] = False
        
    if stats["drop_stages"]:
        worst_stage = max(stats["drop_stages"], key=stats["drop_stages"].get)
        updates["focus_stage"] = worst_stage
        
    return updates

def apply_tuning(response: str, session: Dict) -> str:
    # If force_simplification is active, we can trim down or simplify language
    if SYSTEM_TUNING.get("force_simplification"):
        # We rely on engine's Rule 2 for confusion handling, but we can add an extra prompt
        pass
        
    if SYSTEM_TUNING.get("cta_style") == "soft":
        response = response.replace(
            "Would you like to apply?",
            "I can guide you step by step — no pressure."
        )
    if SYSTEM_TUNING.get("inject_social_proof"):
        if "Most students at this stage" not in response:
            response += "\n\nMost students at this stage usually start early to secure their preferred course."
            
    return response

def nightly_optimization():
    events = get_analytics()
    if not events:
        return
    stats = aggregate_metrics(events)
    updates = generate_rule_updates(stats)
    SYSTEM_TUNING.update(updates)

def store_success(session: Dict):
    SUCCESS_PATTERNS.append({
        "query": session.get("first_query"),
        "flow": session.get("conversion_stage"),
        "messages": session.get("turn_count")
    })
