#!/usr/bin/env python3
"""Controlled evaluation harness for the production chat API."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests


DEFAULT_API_URL = "http://localhost:8000/api/v1/chat"
DEFAULT_DATASET = Path("scripts/evaluate_queries_100.json")
DEFAULT_OUTPUT_DIR = Path("scripts/eval_runs")
DEFAULT_PASS_THRESHOLD = 0.75


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the 100-query controlled evaluation suite.")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--pass-threshold", type=float, default=DEFAULT_PASS_THRESHOLD)
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def normalize(text: Any) -> str:
    if not isinstance(text, str):
        return ""
    lowered = text.lower()
    cleaned = []
    for char in lowered:
        if char.isalnum() or char.isspace():
            cleaned.append(char)
        else:
            cleaned.append(" ")
    return " ".join("".join(cleaned).split())


def load_dataset(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    payload = json.loads(path.read_text())
    if not isinstance(payload, list) or not payload:
        raise ValueError("Dataset must be a non-empty JSON array.")
    return payload


def validate_dataset(dataset: List[Dict[str, Any]]) -> None:
    ids = set()
    sequence_turns: Dict[str, List[int]] = defaultdict(list)
    category_counts = Counter()

    for index, case in enumerate(dataset, start=1):
        if not isinstance(case, dict):
            raise ValueError(f"Case #{index} must be an object.")

        case_id = case.get("id")
        query = case.get("query")
        category = case.get("category")

        if not case_id or not isinstance(case_id, str):
            raise ValueError(f"Case #{index} is missing a valid 'id'.")
        if case_id in ids:
            raise ValueError(f"Duplicate case id: {case_id}")
        ids.add(case_id)

        if not query or not isinstance(query, str):
            raise ValueError(f"Case '{case_id}' is missing a valid 'query'.")
        if not category or not isinstance(category, str):
            raise ValueError(f"Case '{case_id}' is missing a valid 'category'.")

        category_counts[category] += 1

        sequence_id = case.get("sequence_id")
        turn = case.get("turn")
        if sequence_id is not None:
            if not isinstance(sequence_id, str):
                raise ValueError(f"Case '{case_id}' has an invalid 'sequence_id'.")
            if not isinstance(turn, int) or turn < 1:
                raise ValueError(f"Case '{case_id}' must define a positive integer 'turn'.")
            sequence_turns[sequence_id].append(turn)

    for sequence_id, turns in sequence_turns.items():
        ordered = sorted(turns)
        expected = list(range(1, len(turns) + 1))
        if ordered != expected:
            raise ValueError(
                f"Sequence '{sequence_id}' has non-contiguous turns: {ordered}, expected {expected}"
            )

    expected_categories = {"structured", "rag", "messy", "follow_up", "edge"}
    missing = expected_categories - set(category_counts)
    if missing:
        raise ValueError(f"Dataset is missing categories: {sorted(missing)}")

    if len(dataset) != 100:
        raise ValueError(f"Dataset must contain exactly 100 cases, found {len(dataset)}.")

    for category in sorted(category_counts):
        print(f"{category:10s}: {category_counts[category]}")


def build_payload(case: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "query": case["query"],
        "context": {"session_id": session_id},
    }
    if case.get("user"):
        payload["user"] = case["user"]
    if case.get("user_context"):
        payload["user_context"] = case["user_context"]
    return payload


def score_case(case: Dict[str, Any], data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    answer = data.get("answer", "")
    normalized_answer = normalize(answer)
    checks: List[Tuple[str, float]] = []
    detail: Dict[str, Any] = {}

    expected_mode = case.get("expected_mode")
    actual_mode = data.get("meta", {}).get("source") or data.get("mode")
    if expected_mode is not None:
        passed = actual_mode == expected_mode
        checks.append(("mode", 1.0 if passed else 0.0))
        detail["mode"] = {"expected": expected_mode, "actual": actual_mode, "passed": passed}

    expected_fallback = case.get("expected_fallback")
    actual_fallback = bool(data.get("is_fallback", data.get("fallback", False)))
    if expected_fallback is not None:
        passed = actual_fallback == expected_fallback
        checks.append(("fallback", 1.0 if passed else 0.0))
        detail["fallback"] = {"expected": expected_fallback, "actual": actual_fallback, "passed": passed}

    expected_status = case.get("expected_status")
    actual_status = data.get("status")
    if expected_status is not None:
        passed = actual_status == expected_status
        checks.append(("status", 1.0 if passed else 0.0))
        detail["status"] = {"expected": expected_status, "actual": actual_status, "passed": passed}

    must_contain_any = case.get("must_contain_any") or []
    if must_contain_any:
        matches = [token for token in must_contain_any if normalize(token) in normalized_answer]
        score = 1.0 if matches else 0.0
        checks.append(("must_contain_any", score))
        detail["must_contain_any"] = {
            "expected": must_contain_any,
            "matched": matches,
            "passed": bool(matches),
        }

    must_contain_all = case.get("must_contain_all") or []
    if must_contain_all:
        matches = [token for token in must_contain_all if normalize(token) in normalized_answer]
        score = len(matches) / len(must_contain_all)
        checks.append(("must_contain_all", score))
        detail["must_contain_all"] = {
            "expected": must_contain_all,
            "matched": matches,
            "missing": [token for token in must_contain_all if token not in matches],
            "passed": len(matches) == len(must_contain_all),
        }

    must_not_contain = case.get("must_not_contain") or []
    if must_not_contain:
        violations = [token for token in must_not_contain if normalize(token) in normalized_answer]
        score = 0.0 if violations else 1.0
        checks.append(("must_not_contain", score))
        detail["must_not_contain"] = {
            "expected": must_not_contain,
            "violations": violations,
            "passed": not violations,
        }

    if not checks:
        raise ValueError(f"Case '{case['id']}' has no scoring checks configured.")

    overall = sum(score for _, score in checks) / len(checks)
    detail["overall"] = round(overall, 3)
    detail["checks"] = checks
    return overall, detail


def aggregate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals = len(results)
    by_category: Dict[str, Dict[str, Any]] = {}
    source_counter = Counter(result["source"] for result in results)
    fallback_count = sum(1 for result in results if result["fallback"])
    broken_sessions = sum(1 for result in results if result["status"] == "request_error")
    avg_score = sum(result["score"] for result in results) / totals if totals else 0.0
    avg_latency_ms = sum(result["latency_ms"] for result in results) / totals if totals else 0.0
    pass_count = sum(1 for result in results if result["passed"])

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for result in results:
        grouped[result["category"]].append(result)

    for category, items in grouped.items():
        by_category[category] = {
            "count": len(items),
            "pass_rate": round(sum(1 for item in items if item["passed"]) / len(items), 3),
            "avg_score": round(sum(item["score"] for item in items) / len(items), 3),
            "fallback_rate": round(sum(1 for item in items if item["fallback"]) / len(items), 3),
            "avg_latency_ms": round(sum(item["latency_ms"] for item in items) / len(items), 1),
        }

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "totals": {
            "queries": totals,
            "passed": pass_count,
            "pass_rate": round(pass_count / totals, 3) if totals else 0.0,
            "avg_score": round(avg_score, 3),
            "avg_latency_ms": round(avg_latency_ms, 1),
            "fallback_rate": round(fallback_count / totals, 3) if totals else 0.0,
            "structured_rate": round(source_counter.get("structured", 0) / totals, 3) if totals else 0.0,
            "rag_rate": round(source_counter.get("rag", 0) / totals, 3) if totals else 0.0,
            "fallback_source_rate": round(source_counter.get("fallback", 0) / totals, 3) if totals else 0.0,
            "broken_sessions": broken_sessions,
        },
        "sources": dict(source_counter),
        "categories": by_category,
    }


def write_report(summary: Dict[str, Any], results: List[Dict[str, Any]], output_dir: Path) -> Tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    json_path = output_dir / f"controlled_eval_{stamp}.json"
    md_path = output_dir / f"controlled_eval_{stamp}.md"

    payload = {"summary": summary, "results": results}
    json_path.write_text(json.dumps(payload, indent=2))

    totals = summary["totals"]
    lines = [
        "# Controlled Evaluation Report",
        "",
        f"- Generated: `{summary['generated_at']}`",
        f"- Queries: `{totals['queries']}`",
        f"- Pass rate: `{totals['pass_rate']:.1%}`",
        f"- Average score: `{totals['avg_score']:.3f}`",
        f"- Average latency: `{totals['avg_latency_ms']:.1f} ms`",
        f"- Fallback rate: `{totals['fallback_rate']:.1%}`",
        f"- Structured rate: `{totals['structured_rate']:.1%}`",
        f"- RAG rate: `{totals['rag_rate']:.1%}`",
        f"- Broken sessions: `{totals['broken_sessions']}`",
        "",
        "## Category Breakdown",
        "",
        "| Category | Count | Pass Rate | Avg Score | Fallback Rate | Avg Latency |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for category, metrics in sorted(summary["categories"].items()):
        lines.append(
            f"| {category} | {metrics['count']} | {metrics['pass_rate']:.1%} | {metrics['avg_score']:.3f} | "
            f"{metrics['fallback_rate']:.1%} | {metrics['avg_latency_ms']:.1f} ms |"
        )

    failures = [result for result in results if not result["passed"]]
    if failures:
        lines.extend(
            [
                "",
                "## Failures",
                "",
                "| ID | Category | Score | Source | Fallback | Query |",
                "|---|---|---:|---|---|---|",
            ]
        )
        for result in failures:
            lines.append(
                f"| {result['id']} | {result['category']} | {result['score']:.3f} | {result['source']} | "
                f"{result['fallback']} | {result['query']} |"
            )

    md_path.write_text("\n".join(lines) + "\n")
    return json_path, md_path


def run_suite(args: argparse.Namespace) -> int:
    dataset = load_dataset(Path(args.dataset))
    validate_dataset(dataset)
    if args.validate_only:
        print("Dataset validation passed.")
        return 0

    sequence_sessions: Dict[str, str] = {}
    results: List[Dict[str, Any]] = []

    print(f"Running controlled evaluation against {args.api_url}")
    for index, case in enumerate(sorted(dataset, key=lambda item: (item.get("sequence_id", item["id"]), item.get("turn", 0), item["id"])), start=1):
        sequence_id = case.get("sequence_id")
        if sequence_id:
            session_id = sequence_sessions.setdefault(sequence_id, f"eval-{sequence_id}")
        else:
            session_id = f"eval-{case['id']}"

        payload = build_payload(case, session_id)
        started = time.time()
        try:
            response = requests.post(args.api_url, json=payload, timeout=args.timeout)
            latency_ms = (time.time() - started) * 1000
            response.raise_for_status()
            data = response.json()
            score, detail = score_case(case, data)
            threshold = float(case.get("pass_threshold", args.pass_threshold))
            source = data.get("meta", {}).get("source") or data.get("mode") or "unknown"
            confidence = data.get("meta", {}).get("score", data.get("confidence", data.get("confidence_score", 0.0)))
            fallback = bool(data.get("is_fallback", data.get("fallback", False)))
            result = {
                "id": case["id"],
                "category": case["category"],
                "query": case["query"],
                "sequence_id": sequence_id,
                "turn": case.get("turn"),
                "session_id": session_id,
                "source": source,
                "confidence": round(float(confidence or 0.0), 3),
                "fallback": fallback,
                "status": data.get("status", "unlock"),
                "used_rag": bool(data.get("meta", {}).get("used_rag", False)),
                "latency_ms": round(latency_ms, 1),
                "score": round(score, 3),
                "passed": score >= threshold,
                "threshold": threshold,
                "answer": data.get("answer", ""),
                "meta": data.get("meta", {}),
                "evaluation": detail,
            }
            print(
                f"[{index:03d}/100] {'PASS' if result['passed'] else 'FAIL'} "
                f"{case['id']:12s} score={result['score']:.3f} source={source:10s} "
                f"fallback={str(fallback):5s} latency={result['latency_ms']:.1f}ms"
            )
        except Exception as exc:
            latency_ms = (time.time() - started) * 1000
            result = {
                "id": case["id"],
                "category": case["category"],
                "query": case["query"],
                "sequence_id": sequence_id,
                "turn": case.get("turn"),
                "session_id": session_id,
                "source": "request_error",
                "confidence": 0.0,
                "fallback": True,
                "status": "request_error",
                "used_rag": False,
                "latency_ms": round(latency_ms, 1),
                "score": 0.0,
                "passed": False,
                "threshold": float(case.get("pass_threshold", args.pass_threshold)),
                "answer": "",
                "meta": {"error": str(exc)},
                "evaluation": {"overall": 0.0, "error": str(exc)},
            }
            print(f"[{index:03d}/100] FAIL {case['id']:12s} request_error={exc}")

        results.append(result)

    summary = aggregate(results)
    json_path, md_path = write_report(summary, results, Path(args.output_dir))

    totals = summary["totals"]
    print("\nSummary")
    print(f"Pass rate       : {totals['pass_rate']:.1%}")
    print(f"Average score   : {totals['avg_score']:.3f}")
    print(f"Fallback rate   : {totals['fallback_rate']:.1%}")
    print(f"Structured rate : {totals['structured_rate']:.1%}")
    print(f"RAG rate        : {totals['rag_rate']:.1%}")
    print(f"Broken sessions : {totals['broken_sessions']}")
    print(f"JSON report     : {json_path}")
    print(f"Markdown report : {md_path}")

    return 0 if totals["broken_sessions"] == 0 else 1


def main() -> int:
    args = parse_args()
    try:
        return run_suite(args)
    except Exception as exc:
        print(f"Evaluation harness failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
