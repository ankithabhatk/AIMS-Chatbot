# app/services/intent_classifier.py
import re
from typing import Dict

_RULES: list[tuple[str, list[str], float]] = [
    ("admissions",  ["apply", "application", "enroll", "admission", "how to join",
                     "register", "last date", "deadline", "eligib", "entrance"],      0.9),
    ("fees",        ["fee", "fees", "cost", "tuition", "scholarship", "emi",
                     "loan", "payment", "amount", "charges", "price"],                0.9),
    ("courses",     ["course", "program", "mba", "bba", "bca", "mca", "pgdm",
                     "specializ", "stream", "subject", "degree", "offer"],            0.85),
    ("hostel",      ["hostel", "accommodation", "stay", "dormitor", "room",
                     "resident", "campus life", "mess", "canteen"],                   0.9),
    ("placements",  ["placement", "recruit", "company", "package", "salary",
                     "lpa", "ctc", "job", "hire", "campus placement", "career"],      0.9),
    ("general",     [],                                                                0.4),
]


def classify(query: str) -> Dict[str, object]:
    q = query.lower()
    for intent, keywords, confidence in _RULES[:-1]:
        if any(kw in q for kw in keywords):
            return {"intent": intent, "confidence": confidence}
    return {"intent": "general", "confidence": 0.4}
