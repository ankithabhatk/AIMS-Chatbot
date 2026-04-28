#!/usr/bin/env python3
"""
CORRECTED: Structured input handling tests using the CORRECT functions.
Tests garbage inputs, short queries, mixed garbage+intent, and typos.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.input_handler import classify_intent
from app.services.orchestration.engine import (
    compute_intent_scores,
    detect_structured_intent,
    correct_query_typos
)
from app.services.structured_knowledge import detect_program

TEST_CASES = {
    "Garbage Inputs": ["asdfgh", "123456", "!!!@@@", "??"],
    "Short Queries": ["hi", "ok", "fees"],
    "Mixed Garbage + Intent": ["fees???", "bca!!!", "admission???"],
    "Typos": ["admisson", "feees", "plcement", "aims collge"],
}

def test_query(query: str) -> dict:
    """Test a single query using CORRECT functions."""
    result = {
        "query": query,
        "input_classification": None,
        "intent_detected": None,
        "intent_score": None,
        "structured_intent": None,
        "structured_score": None,
        "program_detected": None,
        "typo_corrected": None,
        "fallback": None,
        "notes": []
    }
    
    try:
        # 1. Input classification
        input_class = classify_intent(query)
        result["input_classification"] = input_class
        
        # 2. Intent detection using ENGINE.PY (correct one)
        scores = compute_intent_scores(query)
        max_intent = max(scores, key=scores.get) if scores else None
        max_score = scores.get(max_intent, 0.0) if max_intent else 0.0
        
        if max_score > 0.0:
            result["intent_detected"] = max_intent
            result["intent_score"] = round(max_score, 3)
        else:
            result["intent_detected"] = "unknown"
            result["intent_score"] = 0.0
        
        # 3. Structured intent detection
        struct_intent, struct_score = detect_structured_intent(query)
        result["structured_intent"] = struct_intent or "none"
        result["structured_score"] = round(struct_score, 3)
        
        # 4. Program detection
        program = detect_program(query)
        if program:
            result["program_detected"] = program
        
        # 5. Typo correction
        corrected, original = correct_query_typos(query)
        if corrected != original:
            result["typo_corrected"] = corrected
            result["notes"].append(f"Typo: '{original}' → '{corrected}'")
        
        # 6. Fallback decision
        result["fallback"] = (
            input_class == "NONSENSE" or 
            (result["intent_detected"] == "unknown" and 
             result["structured_intent"] == "none" and
             input_class == "QUESTION")
        )
        
        if input_class == "NONSENSE":
            result["notes"].append("NONSENSE detected")
        elif input_class == "GREETING":
            result["notes"].append("GREETING detected")
        
    except Exception as e:
        result["error"] = str(e)
        result["notes"].append(f"ERROR: {e}")
    
    return result

def main():
    """Run all tests and generate report."""
    print("\n" + "="*100)
    print("CORRECTED INPUT HANDLING TEST (Using engine.py functions)")
    print("="*100 + "\n")
    
    all_results = []
    
    for category, queries in TEST_CASES.items():
        print(f"\n### {category.upper()}")
        print("-" * 100)
        print("| Query | Input Class | Intent | Score | Struct Intent | Fallback? | Notes |")
        print("|-------|-------------|--------|-------|---------------|-----------|-------|")
        
        for query in queries:
            result = test_query(query)
            all_results.append(result)
            
            notes_str = " | ".join(result["notes"]) if result["notes"] else "-"
            
            print(
                f"| `{result['query']}` | "
                f"{result['input_classification']} | "
                f"{result['intent_detected']} | "
                f"{result['intent_score']} | "
                f"{result['structured_intent']} ({result['structured_score']}) | "
                f"{'YES' if result['fallback'] else 'NO'} | "
                f"{notes_str} |"
            )
        
        print()
    
    # Summary
    print("\n" + "="*100)
    print("SUMMARY STATISTICS")
    print("="*100)
    
    total = len(all_results)
    fallback_count = sum(1 for r in all_results if r["fallback"])
    intent_detected = sum(1 for r in all_results if r["intent_detected"] != "unknown")
    struct_detected = sum(1 for r in all_results if r["structured_intent"] != "none")
    
    print(f"\nTotal queries tested: {total}")
    print(f"Fallback triggered: {fallback_count} ({100*fallback_count/total:.1f}%)")
    print(f"Intent detected (router): {intent_detected} ({100*intent_detected/total:.1f}%)")
    print(f"Structured intent detected: {struct_detected} ({100*struct_detected/total:.1f}%)")
    
    # Save report
    report_path = Path(__file__).parent / "test_input_handling_FIXED_report.json"
    with open(report_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n✓ Report saved to: {report_path}")
    
    print("\n" + "="*100 + "\n")

if __name__ == "__main__":
    main()
