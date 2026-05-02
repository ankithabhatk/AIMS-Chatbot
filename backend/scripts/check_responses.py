import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.abspath("."))
from app.services.evaluator import _run_pipeline

queries = [
    "What companies recruit from AIMS?",
    "How to apply for admission?",
    "What are the placement statistics?",
    "What is the MCA fee?",
    "Is AIMS accredited?",
]
for q in queries:
    r = _run_pipeline(q)
    resp = r["response"]
    print(f"Q: {q}")
    print(f"A: {resp[:400]}")
    print()
