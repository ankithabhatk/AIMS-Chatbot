# app/services/analytics.py
import threading
from collections import defaultdict
from typing import Dict

_lock = threading.Lock()
_data: Dict = {
    "total_conversations": 0,
    "intent_counts": defaultdict(int),
    "leads_captured": 0,
    "flows_started": 0,
    "flow_starts": defaultdict(int),
}


def record_conversation(intent: str = "general") -> None:
    with _lock:
        _data["total_conversations"] += 1
        _data["intent_counts"][intent] += 1


def record_flow_start(flow: str) -> None:
    with _lock:
        _data["flows_started"] += 1
        _data["flow_starts"][flow] += 1


def record_lead_captured() -> None:
    with _lock:
        _data["leads_captured"] += 1


def get_conversion_rate() -> float:
    with _lock:
        started = _data["flows_started"]
        return round(_data["leads_captured"] / started, 4) if started else 0.0


def get_stats() -> dict:
    with _lock:
        return {
            "total_conversations": _data["total_conversations"],
            "intent_distribution": dict(_data["intent_counts"]),
            "leads_captured": _data["leads_captured"],
            "flows_started": _data["flows_started"],
            "flow_starts": dict(_data["flow_starts"]),
            "conversion_rate": get_conversion_rate(),
        }
