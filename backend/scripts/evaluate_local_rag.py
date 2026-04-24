"""
Evaluate the local retrieval-first AIMS assistant on the generated dataset.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.intelligence_layer import get_intelligence_layer
from app.services.response.confidence import calculate_confidence
from app.services.retrieval.hybrid_retriever import get_hybrid_retriever
from app.services.taxonomy import keyword_set

DATASET_FILE = Path(__file__).with_name("eval_dataset_local.json")
RESULTS_FILE = Path(__file__).with_name("evaluation_log_local.json")
SUMMARY_FILE = Path(__file__).with_name("evaluation_report_local.json")

CONFIDENCE_THRESHOLD = 0.48
LOW_CONFIDENCE_THRESHOLD = 0.32
SAFE_GLUE = {
    "hi",
    "help",
    "aims",
    "could",
    "please",
    "found",
    "verified",
    "information",
    "current",
    "records",
}


def load_dataset() -> List[Dict]:
    return json.loads(DATASET_FILE.read_text(encoding="utf-8"))


def run_case(case: Dict) -> Dict:
    intel = get_intelligence_layer()
    retriever = get_hybrid_retriever()
    session_id = case["id"]

    for context_query in case.get("context_queries", []):
        intel.process_query(context_query, session_id)

    start = time.perf_counter()
    query_data = intel.process_query(case["query"], session_id)
    retrieval_results = retriever.search(query_data, k=5)
    confidence = calculate_confidence(query_data["query"], retrieval_results, query_data=query_data) if retrieval_results else 0.0
    chunk_tuples = retriever.to_chunk_tuples(retrieval_results)
    latency_ms = round((time.perf_counter() - start) * 1000, 2)

    if query_data.get("needs_clarification"):
        actual_behavior = "clarification"
        answer = query_data.get("clarification_message") or "Could you clarify the course or topic?"
    elif query_data.get("intent") in {"greeting", "exit"}:
        actual_behavior = "greeting"
        answer = intel.synthesize_response(query_data, [], 1.0)["answer"]
    elif not retrieval_results:
        actual_behavior = "fallback"
        answer = "I could not find a matching AIMS record."
    elif confidence < CONFIDENCE_THRESHOLD:
        actual_behavior = "snippet"
        answer = snippet_answer(retrieval_results)
    else:
        actual_behavior = "answer"
        answer = intel.synthesize_response(query_data, chunk_tuples, confidence)["answer"]

    retrieved_chunks = [
        {
            "heading": result.get("heading"),
            "url": result.get("url"),
            "score": result.get("score"),
            "course": result.get("course"),
            "topic": result.get("topic"),
        }
        for result in retrieval_results[:5]
    ]

    retrieval_match = evaluate_retrieval(case, retrieval_results)
    answer_match = evaluate_answer(case, answer)
    behavior_match = evaluate_behavior(case, actual_behavior)
    grounded = is_grounded(answer, retrieval_results)

    return {
        "id": case["id"],
        "query": case["query"],
        "context_queries": case.get("context_queries", []),
        "expected_course": case.get("expected_course"),
        "expected_topic": case.get("expected_topic"),
        "expected_behavior": case.get("expected_behavior"),
        "actual_behavior": actual_behavior,
        "original_query": query_data.get("original_query"),
        "corrected_query": query_data.get("corrected_query"),
        "resolved_query": query_data.get("query"),
        "retrieval_match": retrieval_match,
        "answer_match": answer_match,
        "behavior_match": behavior_match,
        "grounded": grounded,
        "confidence": confidence,
        "latency_ms": latency_ms,
        "retrieved_chunks": retrieved_chunks,
        "final_answer": answer,
        "overall_pass": retrieval_match and behavior_match and (answer_match or case.get("expected_behavior") in {"clarification", "greeting"}),
    }


def snippet_answer(results: List[Dict]) -> str:
    if not results:
        return ""
    text = results[0].get("content", "")
    sentences = [part.strip() for part in text.replace("\n", " ").split(".") if len(part.strip()) >= 18]
    return "\n".join(f"- {sentence}." for sentence in sentences[:3])


def evaluate_retrieval(case: Dict, results: List[Dict]) -> bool:
    expected_behavior = case.get("expected_behavior")
    if expected_behavior in {"clarification", "greeting"}:
        return True
    if not results:
        return False

    expected_course = case.get("expected_course")
    expected_topic = case.get("expected_topic")

    course_ok = not expected_course or any(result.get("course") == expected_course for result in results[:5])
    topic_ok = not expected_topic or any(result.get("topic") == expected_topic for result in results[:5])
    return course_ok and topic_ok


def evaluate_answer(case: Dict, answer: str) -> bool:
    expected_keywords = [keyword.lower() for keyword in case.get("expected_keywords", [])]
    if not expected_keywords:
        return True
    answer_lower = answer.lower()
    return any(keyword in answer_lower for keyword in expected_keywords)


def evaluate_behavior(case: Dict, actual_behavior: str) -> bool:
    expected = case.get("expected_behavior")
    if expected == "answer":
        return actual_behavior in {"answer", "snippet"}
    return actual_behavior == expected


def is_grounded(answer: str, results: List[Dict]) -> bool:
    if not answer:
        return True

    answer_terms = keyword_set([answer]) - SAFE_GLUE
    source_terms = keyword_set([result.get("content", "") for result in results[:5]])
    if not answer_terms:
        return True

    overlap = len(answer_terms & source_terms)
    ratio = overlap / max(len(answer_terms), 1)
    return ratio >= 0.55


def summarize(results: List[Dict]) -> Dict:
    total = len(results)
    retrieval_accuracy = sum(1 for result in results if result["retrieval_match"]) / max(total, 1)
    answer_correctness = sum(1 for result in results if result["answer_match"]) / max(total, 1)
    fallback_correctness = sum(1 for result in results if result["behavior_match"]) / max(total, 1)
    grounded_rate = sum(1 for result in results if result["grounded"]) / max(total, 1)
    overall_accuracy = sum(1 for result in results if result["overall_pass"]) / max(total, 1)
    avg_confidence = sum(result["confidence"] for result in results) / max(total, 1)
    avg_latency = sum(result["latency_ms"] for result in results) / max(total, 1)

    typo_cases = [
        result
        for result in results
        if any(fragment in result["query"].lower() for fragment in ["feees", "plcements", "hostl", "curriculm", "addmission"])
    ]
    typo_success = sum(1 for result in typo_cases if result["retrieval_match"]) / max(len(typo_cases), 1)

    return {
        "total_cases": total,
        "retrieval_accuracy": round(retrieval_accuracy, 3),
        "answer_correctness": round(answer_correctness, 3),
        "fallback_correctness": round(fallback_correctness, 3),
        "typo_handling_success": round(typo_success, 3),
        "grounded_answer_rate": round(grounded_rate, 3),
        "hallucination_rate": round(1.0 - grounded_rate, 3),
        "overall_accuracy": round(overall_accuracy, 3),
        "avg_confidence": round(avg_confidence, 3),
        "avg_latency_ms": round(avg_latency, 2),
    }


def main() -> int:
    dataset = load_dataset()
    results = [run_case(case) for case in dataset]
    summary = summarize(results)

    RESULTS_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Detailed log: {RESULTS_FILE}")
    print(f"Summary: {SUMMARY_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
