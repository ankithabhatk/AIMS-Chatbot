# app/services/intent_classifier.py
import re
from typing import Dict

# Matches "MBA or MCA", "BCA or BBA" etc — program-vs-program via "or"
_OR_COMPARE_PAT = re.compile(
    r"\b(mba|mca|bba|bca|bcom|pgdm|b\.sc|msc)\s+or\s+(mba|mca|bba|bca|bcom|pgdm|b\.sc|msc)\b",
    re.IGNORECASE,
)

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

# Strong comparison markers
_COMPARISON_KW = [
    "vs", "versus", "compare",
    "difference between", "confused between",
    "which is better", "which one is better",
    "which should i choose",
]


def _is_comparison(q: str) -> bool:
    if any(kw in q for kw in _COMPARISON_KW) or _OR_COMPARE_PAT.search(q):
        return True
    # "confused ... X and Y" or "difference ... X and Y"
    if ("confused" in q or "difference" in q) and " and " in q:
        return True
    return False


def classify(query: str) -> Dict[str, object]:
    q = query.lower()
    # Comparison takes priority — checked before topic rules
    if _is_comparison(q):
        return {"intent": "comparison", "confidence": 0.9}
    for intent, keywords, confidence in _RULES[:-1]:
        if any(kw in q for kw in keywords):
            return {"intent": intent, "confidence": confidence}
    return {"intent": "general", "confidence": 0.4}
