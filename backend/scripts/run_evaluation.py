#!/usr/bin/env python
"""scripts/run_evaluation.py — run offline RAG evaluation and print report."""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure backend root is on PYTHONPATH when run directly
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.services.evaluator import load_dataset, run_evaluation, generate_dataset_candidates

_DEFAULT_DATASET = os.path.join(_ROOT, "tests", "eval_dataset.json")


def _bar(value: float, width: int = 20) -> str:
    filled = int(round(value * width))
    return "[" + "█" * filled + "░" * (width - filled) + f"] {value * 100:.1f}%"


def main(dataset_path: str = _DEFAULT_DATASET) -> None:
    print(f"\n🔍 Loading dataset: {dataset_path}")
    dataset = load_dataset(dataset_path)
    print(f"   {len(dataset)} test cases found\n")

    print("⚙️  Running evaluation pipeline …")
    report = run_evaluation(dataset)

    print("\n🔍 Generating dataset candidates from low-confidence logs …")
    candidates = generate_dataset_candidates()
    print(f"   {len(candidates)} new candidate(s) saved to tests/eval_candidates.json")

    print("\n" + "=" * 54)
    print("  EVALUATION REPORT")
    print("=" * 54)
    print(f"  Total queries   : {report['total']}")
    print(f"  Correct  (1.0)  : {report['correct']}")
    print(f"  Partial  (0.5)  : {report['partial']}")
    print(f"  Incorrect(0.0)  : {report['incorrect']}")
    print(f"  Accuracy        : {_bar(report['accuracy'])}")
    print(f"  Fallback rate   : {_bar(report['fallback_rate'])}")
    print(f"  Avg confidence  : {report['avg_confidence']:.4f}")
    print(f"  Weighted Accuracy: {_bar(report['weighted_accuracy'])}")
    print("=" * 54)
    print(f"  High-confidence errors : {report['high_conf_wrong']}")
    print(f"  Low-confidence correct : {report['low_conf_correct']}")
    print(f"  New dataset candidates : {len(candidates)}")
    print("=" * 54)

    cat_acc  = report.get("category_accuracy", {})
    wcat_acc = report.get("weighted_category_accuracy", {})
    if cat_acc:
        print("\n📂 Category-wise accuracy (raw | weighted):")
        for cat in sorted(cat_acc):
            raw = cat_acc[cat]
            wgt = wcat_acc.get(cat, raw)
            print(f"   {cat:<18} {_bar(raw, width=12)}  weighted={wgt*100:.1f}%")

    if report["failed_queries"]:
        print("\n❌ Failed queries (score=0):")
        for q in report["failed_queries"]:
            print(f"   • {q}")

    print("\n📋 Per-query details:")
    _SCORE_ICON = {1.0: "✅", 0.5: "🟡", 0.0: "❌"}
    for d in report["details"]:
        icon    = _SCORE_ICON.get(d["score"], "❓")
        fb_tag  = " [FB]" if d["fallback"] else ""
        err_tag = f" [ERR]" if d["error"] else ""
        print(f"  {icon} [{d['score']:.1f}|{d['confidence']:.2f}] {d['query'][:55]}{fb_tag}{err_tag}")

    print()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_DATASET
    main(path)
