import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.abspath("."))
from app.services.evaluator import _run_pipeline, compute_similarity, load_dataset

dataset = load_dataset(os.path.join(os.path.abspath("."), "tests", "eval_dataset.json"))
partial_queries = [
    "Does AIMS have hostel facility?",
    "What are the placement statistics?",
    "What specializations are offered in MBA?",
    "What is the MCA fee?",
    "How to apply for admission?",
]
for item in dataset:
    if item["query"] not in partial_queries:
        continue
    result = _run_pipeline(item["query"])
    resp = result["response"]
    ea = item.get("expected_answer", "")
    sim = compute_similarity(resp, ea)
    print(f"Q: {item['query']}")
    print(f"sim={sim:.4f}  expected: {ea[:80]}")
    print(f"bot: {resp[:150]}")
    print()
