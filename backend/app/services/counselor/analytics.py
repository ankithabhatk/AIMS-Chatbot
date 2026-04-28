import time
from typing import Dict, List

ANALYTICS_LOG = []
LAST_ACTIVITY = {}

def log_event(event: str, data: Dict = None):
    data = data or {}
    record = {
        "event": event,
        "timestamp": time.time(),
        "data": data
    }
    ANALYTICS_LOG.append(record)

def track_event(event_type: str, data: Dict):
    log_event(event_type, data)
    
    # Track activity for drop-offs
    session_id = data.get("session_id")
    if session_id:
        update_activity(session_id)

def get_analytics() -> List[Dict]:
    return ANALYTICS_LOG

# -------------------------
# DROP-OFF DETECTION
# -------------------------
def update_activity(session_id: str):
    LAST_ACTIVITY[session_id] = time.time()

def detect_drop_offs(threshold: int = 300) -> List[str]:  # 5 min
    now = time.time()
    dropped = []
    for session_id, last_time in LAST_ACTIVITY.items():
        if now - last_time > threshold:
            dropped.append(session_id)
            log_event("drop_off", {"session_id": session_id})
            # avoid repeat logging
            LAST_ACTIVITY[session_id] = now + 999999
    return dropped
