#!/usr/bin/env python3
"""
Test Post-Tier Validation Layer

Tests the validation layer against risk scenarios:
1. placement record
2. hostel facilities
3. mba fees
4. mba fees and placements

Verifies:
- Intent anchoring works
- RAG grounding checks work
- Structured protection works
- Validation logs properly
"""

import sys
import os
import logging
from typing import List, Tuple

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s - %(message)s'
)

from app.services.validation.post_tier_validator import validate_tier_output, INTENT_KEYWORDS
from app.services.orchestration.self_healing_engine import OrchestrationResult


# Sample chunks for testing
SAMPLE_CHUNKS = {
    "placements": [
        (
            "AIMS Institutes has an excellent placement record with 98% of MBA students placed within 6 months. "
            "Average package is Rs 12.5 LPA with highest package reaching Rs 28 LPA. "
            "Top recruiters include Infosys, Wipro, TCS, Cognizant, and Goldman Sachs.",
            0.92,
            "https://theaims.ac.in/placements",
            "Placement Statistics"
        ),
    ],
    "fees": [
        (
            "MBA fees structure: Total fees for 2-year program is Rs 24 Lakhs. "
            "Can be paid as annual installments of Rs 12 Lakhs or semester installments. "
            "Scholarships available up to 50% for merit and need-based criteria.",
            0.88,
            "https://theaims.ac.in/fees",
            "MBA Fees"
        ),
    ],
    "admission": [
        (
            "AIMS admission process: 1) Online application 2) Entrance exam 3) Personal interview. "
            "Eligibility: Bachelor's degree with 50% marks from recognized university. "
            "Application deadline is June 30 each year.",
            0.85,
            "https://theaims.ac.in/admission",
            "Admission Process"
        ),
    ],
    "campus": [
        (
            "Campus facilities include modern hostel with furnished rooms, "
            "Wi-Fi connectivity, mess facilities, CCTV security, and laundry services. "
            "Separate hostels for boys and girls with biometric access.",
            0.80,
            "https://theaims.ac.in/campus",
            "Campus Facilities"
        ),
    ],
}

# Test cases
TEST_CASES = [
    {
        "name": "Placement Record Query",
        "query": "placement record",
        "intent": "placements",
        "good_answer": "AIMS has a 98% placement rate with average package of Rs 12.5 LPA and highest of Rs 28 LPA. Top recruiters are Infosys, Wipro, TCS, and Cognizant.",
        "bad_answer": "AIMS is a great institution for students. We offer many programs and facilities.",
        "chunks": SAMPLE_CHUNKS["placements"],
    },
    {
        "name": "Hostel Facilities Query",
        "query": "hostel facilities",
        "intent": "campus",
        "good_answer": "Hostel provides furnished rooms, Wi-Fi, mess, CCTV security, and laundry services. Separate hostels for boys and girls with biometric access.",
        "bad_answer": "We have good facilities at our campus for students.",
        "chunks": SAMPLE_CHUNKS["campus"],
    },
    {
        "name": "MBA Fees Query",
        "query": "mba fees",
        "intent": "fees",
        "good_answer": "MBA fees is Rs 24 Lakhs for 2-year program. Can be paid as annual (Rs 12L/year) or semester installments. Scholarships up to 50% available.",
        "bad_answer": "The fees vary depending on the program and your profile.",
        "chunks": SAMPLE_CHUNKS["fees"],
    },
    {
        "name": "Admission Process Query",
        "query": "admission process",
        "intent": "admission",
        "good_answer": "Admission requires: 1) Online application 2) Entrance exam 3) Interview. Eligibility is bachelor's degree with 50% marks. Deadline is June 30.",
        "bad_answer": "We have a competitive admission process for all programs.",
        "chunks": SAMPLE_CHUNKS["admission"],
    },
]


def create_result(answer: str, intent: str, mode: str = "rag", confidence: float = 0.70, fallback: bool = False) -> OrchestrationResult:
    """Create a test result object."""
    return OrchestrationResult(
        answer=answer,
        intent=intent,
        mode=mode,
        confidence=confidence,
        self_score={"relevance": 0.7, "clarity": 0.7, "completeness": 0.7},
        fallback=fallback,
        chunks_used=0,
        sources=None,
    )


def print_test_header(test_name: str):
    """Print test header."""
    print("\n" + "=" * 80)
    print(f"TEST: {test_name}")
    print("=" * 80)


def test_good_answers():
    """Test that good answers pass validation."""
    print_test_header("GOOD ANSWERS (Should Pass)")
    
    for test in TEST_CASES:
        print(f"\n📝 Query: '{test['query']}'")
        print(f"   Intent: {test['intent']}")
        print(f"   Answer: {test['good_answer'][:80]}...")
        
        result = create_result(
            answer=test["good_answer"],
            intent=test["intent"],
            confidence=0.75
        )
        
        validated = validate_tier_output(
            result=result,
            original_intent=test["intent"],
            original_query=test["query"],
            chunks=test["chunks"],
        )
        
        status = "✅ PASS" if not validated.fallback else "❌ FAIL"
        print(f"   Result: {status} (fallback={validated.fallback}, conf={validated.confidence:.3f})")


def test_bad_answers():
    """Test that bad answers trigger fallback."""
    print_test_header("BAD ANSWERS (Should Trigger Fallback)")
    
    for test in TEST_CASES:
        print(f"\n📝 Query: '{test['query']}'")
        print(f"   Intent: {test['intent']}")
        print(f"   Answer: {test['bad_answer'][:80]}...")
        
        result = create_result(
            answer=test["bad_answer"],
            intent=test["intent"],
            confidence=0.50
        )
        
        validated = validate_tier_output(
            result=result,
            original_intent=test["intent"],
            original_query=test["query"],
            chunks=test["chunks"],
        )
        
        status = "✅ CORRECT" if validated.fallback else "❌ ERROR"
        print(f"   Result: {status} (fallback={validated.fallback}, conf={validated.confidence:.3f})")


def test_edge_cases():
    """Test edge cases."""
    print_test_header("EDGE CASES")
    
    # Test 1: Very short answer
    print("\n1️⃣  Very Short Answer")
    result = create_result(
        answer="fees",
        intent="fees",
        confidence=0.60
    )
    validated = validate_tier_output(
        result=result,
        original_intent="fees",
        original_query="mba fees",
        chunks=SAMPLE_CHUNKS["fees"],
    )
    print(f"   Result: fallback={validated.fallback} (expected: True)")
    
    # Test 2: Low confidence structured intent
    print("\n2️⃣  Low Confidence on Fees")
    result = create_result(
        answer="MBA fees is Rs 24 Lakhs with scholarships available.",
        intent="fees",
        confidence=0.35  # Too low for structured
    )
    validated = validate_tier_output(
        result=result,
        original_intent="fees",
        original_query="fees structure",
        chunks=SAMPLE_CHUNKS["fees"],
    )
    print(f"   Result: fallback={validated.fallback} (expected: True, conf={validated.confidence:.3f})")
    
    # Test 3: Missing financial details in fees answer
    print("\n3️⃣  Fees Answer Without Currency/Amount")
    result = create_result(
        answer="We offer MBA program with flexible payment options available for students.",
        intent="fees",
        confidence=0.65
    )
    validated = validate_tier_output(
        result=result,
        original_intent="fees",
        original_query="fees",
        chunks=SAMPLE_CHUNKS["fees"],
    )
    print(f"   Result: fallback={validated.fallback} (expected: True)")
    
    # Test 4: Admission answer without process details
    print("\n4️⃣  Admission Answer Without Process")
    result = create_result(
        answer="AIMS is a great institution with selective admission.",
        intent="admission",
        confidence=0.70
    )
    validated = validate_tier_output(
        result=result,
        original_intent="admission",
        original_query="how to apply",
        chunks=SAMPLE_CHUNKS["admission"],
    )
    print(f"   Result: fallback={validated.fallback} (expected: True)")


def test_confidence_penalty():
    """Test confidence penalty on validation failure."""
    print_test_header("CONFIDENCE PENALTY")
    
    result = create_result(
        answer="General answer about AIMS",
        intent="fees",
        confidence=0.80
    )
    
    print(f"Before validation: confidence = {result.confidence:.3f}")
    
    validated = validate_tier_output(
        result=result,
        original_intent="fees",
        original_query="fees",
        chunks=SAMPLE_CHUNKS["fees"],
    )
    
    print(f"After validation: confidence = {validated.confidence:.3f}")
    print(f"Penalty applied: {result.confidence - validated.confidence:.3f}")
    print(f"Fallback triggered: {validated.fallback}")


def run_all_tests():
    """Run all validation tests."""
    print("\n" + "🧪" * 40)
    print("POST-TIER VALIDATION LAYER TEST SUITE")
    print("🧪" * 40)
    
    try:
        test_good_answers()
        test_bad_answers()
        test_edge_cases()
        test_confidence_penalty()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
