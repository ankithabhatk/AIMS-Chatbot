#!/usr/bin/env python3
"""
Structured input handling tests for the AIMS chatbot.
Tests garbage inputs, short queries, mixed garbage+intent, and typos.
Logs: query, detected intent, response, fallback status.
"""

import sys
import json
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.input_handler import classify_intent
from app.services.orchestration.engine import (
    detect_intents,
    compute_intent_scores,
    correct_query_typos
)
from app.services.structured_knowledge import is_structured_intent, detect_program

# Test data organized by category
TEST_CASES = {
    "Garbage Inputs": [
        "asdfgh",
        "123456",
        "!!!@@@",
        "??",
    ],
    "Short Queries": [
        "hi",
        "ok",
        "fees",
    ],
    "Mixed Garbage + Intent": [
        "fees???",
        "bca!!!",
        "admission???",
    ],
    "Typos": [
        "admisson",
        "feees",
        "plcement",
        "aims collge",
    ],
}

def test_query(query: str) -> dict:
    """Test a single query and return results."""
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
        # 1. Input classification (GREETING/EXIT/NONSENSE/QUESTION)
        input_class = classify_intent(query)
        result["input_classification"] = input_class
        
        # 2. Intent detection (if not nonsense)
        if input_class != "NONSENSE":
            intents = detect_intents(query, threshold=0.6)
            if intents:
                result["intent_detected"] = intents[0][0]
                result["intent_score"] = round(intents[0][1], 3)
            else:
                result["intent_detected"] = "unknown"
                result["intent_score"] = 0.0
        else:
            result["intent_detected"] = "nonsense"
            result["intent_score"] = 0.0
        
        # 3. Structured intent detection
        struct_intent, struct_score = is_structured_intent(query)
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
            result["notes"].append(f"Typo correction: '{original}' → '{corrected}'")
        
        # 6. Fallback detection
        # Fallback if: NONSENSE or no intent detected
        result["fallback"] = (
            input_class == "NONSENSE" or 
            (result["intent_detected"] == "unknown" and input_class == "QUESTION")
        )
        
        # Add classification notes
        if input_class == "NONSENSE":
            result["notes"].append("Classified as NONSENSE")
        elif input_class == "GREETING":
            result["notes"].append("Classified as GREETING")
        elif input_class == "EXIT":
            result["notes"].append("Classified as EXIT")
        
    except Exception as e:
        result["error"] = str(e)
        result["notes"].append(f"ERROR: {e}")
    
    return result

def main():
    """Run all tests and generate report."""
    print("\n" + "="*100)
    print("STRUCTURED INPUT HANDLING TEST REPORT")
    print("="*100 + "\n")
    
    all_results = []
    
    for category, queries in TEST_CASES.items():
        print(f"\n### {category.upper()}")
        print("-" * 100)
        
        # Print markdown table header
        print("| Query | Input Class | Intent | Score | Struct Intent | Fallback? | Notes |")
        print("|-------|-------------|--------|-------|---------------|-----------|-------|")
        
        for query in queries:
            result = test_query(query)
            all_results.append(result)
            
            # Format for markdown table
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
    
    # Summary statistics
    print("\n" + "="*100)
    print("SUMMARY STATISTICS")
    print("="*100)
    
    total = len(all_results)
    fallback_count = sum(1 for r in all_results if r["fallback"])
    nonsense_count = sum(1 for r in all_results if r["input_classification"] == "NONSENSE")
    intent_detected = sum(1 for r in all_results if r["intent_detected"] != "unknown" and r["intent_detected"] != "nonsense")
    typo_corrected = sum(1 for r in all_results if r["typo_corrected"])
    
    print(f"\nTotal queries tested: {total}")
    print(f"Fallback triggered: {fallback_count} ({100*fallback_count/total:.1f}%)")
    print(f"Classified as NONSENSE: {nonsense_count} ({100*nonsense_count/total:.1f}%)")
    print(f"Intent detected: {intent_detected} ({100*intent_detected/total:.1f}%)")
    print(f"Typos corrected: {typo_corrected} ({100*typo_corrected/total:.1f}%)")
    
    # Detailed breakdown by category
    print("\n### Breakdown by Category:")
    for category, queries in TEST_CASES.items():
        category_results = [r for r in all_results if r["query"] in queries]
        fallback_in_cat = sum(1 for r in category_results if r["fallback"])
        print(f"  - {category}: {fallback_in_cat}/{len(category_results)} fallbacks")
    
    # Save detailed JSON report
    report_path = Path(__file__).parent / "test_input_handling_report.json"
    with open(report_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n✓ Detailed report saved to: {report_path}")
    
    print("\n" + "="*100 + "\n")

if __name__ == "__main__":
    main()
