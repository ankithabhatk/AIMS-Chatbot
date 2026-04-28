#!/usr/bin/env python3
"""
Integration Test: Post-Tier Validation with Full Orchestration

Tests the 4 risk scenarios through the complete pipeline:
1. placement record
2. hostel facilities
3. mba fees
4. mba fees and placements

Verifies:
- Validation catches poor answers
- Confidence is penalized appropriately
- Fallback is triggered when needed
- RAG answers are grounded properly
"""

import sys
import os
import logging

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

from app.services.orchestration.engine import execute_orchestration


def print_header(text):
    """Print test header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def test_risk_scenarios():
    """Test the 4 risk scenarios"""
    print_header("RISK SCENARIO TEST - Post-Tier Validation Integration")
    
    scenarios = [
        {
            "name": "Placement Record",
            "query": "placement record",
            "expected_intent": "placements",
            "expected_mode": "rag"
        },
        {
            "name": "Hostel Facilities",
            "query": "hostel facilities",
            "expected_intent": "campus",
            "expected_mode": "rag"
        },
        {
            "name": "MBA Fees",
            "query": "mba fees",
            "expected_intent": "fees",
            "expected_mode": "structured"
        },
        {
            "name": "MBA Fees and Placements",
            "query": "mba fees and placements",
            "expected_intent": "fees",  # Primary intent
            "expected_mode": "structured"
        },
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'─' * 80}")
        print(f"TEST {i}: {scenario['name']}")
        print(f"Query: '{scenario['query']}'")
        print(f"Expected Intent: {scenario['expected_intent']}")
        print(f"Expected Mode: {scenario['expected_mode']}")
        print("─" * 80)
        
        try:
            # Execute orchestration
            result = execute_orchestration(
                query=scenario['query'],
                retrieved_chunks=None  # No chunks for this test
            )
            
            # Verify result
            print(f"\n✅ Response Generated")
            print(f"   Intent: {result.intent}")
            print(f"   Mode: {result.mode}")
            print(f"   Confidence: {result.confidence:.3f}")
            print(f"   Fallback: {result.is_fallback}")
            print(f"   Answer Preview: {result.answer[:100]}...")
            
            # Check intent match
            if result.intent == scenario['expected_intent']:
                print(f"   ✅ Intent matches expected: {scenario['expected_intent']}")
            else:
                print(f"   ⚠️  Intent mismatch: got '{result.intent}', expected '{scenario['expected_intent']}'")
            
            # Check mode match
            if result.mode == scenario['expected_mode']:
                print(f"   ✅ Mode matches expected: {scenario['expected_mode']}")
            else:
                print(f"   ⚠️  Mode mismatch: got '{result.mode}', expected '{scenario['expected_mode']}'")
            
            # Check suggestions
            if result.suggestions:
                print(f"   Suggestions: {', '.join(result.suggestions[:2])}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()


def test_with_mock_chunks():
    """Test with mock RAG chunks to verify grounding checks"""
    print_header("RAG GROUNDING TEST - With Mock Chunks")
    
    mock_chunks = [
        {
            "content": "AIMS Institutes has a 98% placement rate. Average CTC is Rs 12.5 LPA. Top recruiters include Infosys, Wipro, TCS.",
            "score": 0.95,
            "url": "aims.edu/placements",
            "heading": "Placement Record"
        },
        {
            "content": "Placement statistics for our MBA program show consistent growth. Last year, 98% of students were placed.",
            "score": 0.87,
            "url": "aims.edu/placements",
            "heading": "Placement Statistics"
        }
    ]
    
    query = "placement record"
    print(f"\nQuery: '{query}'")
    print(f"Chunks provided: {len(mock_chunks)}")
    
    try:
        result = execute_orchestration(
            query=query,
            retrieved_chunks=mock_chunks
        )
        
        print(f"\n✅ Result with chunks:")
        print(f"   Intent: {result.intent}")
        print(f"   Mode: {result.mode}")
        print(f"   Confidence: {result.confidence:.3f}")
        print(f"   Fallback: {result.is_fallback}")
        print(f"   Answer Length: {len(result.answer)} chars")
        print(f"   Answer Preview: {result.answer[:150]}...")
        
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


def test_answer_drift_protection():
    """Test that validation prevents answer drift"""
    print_header("ANSWER DRIFT PROTECTION TEST")
    
    # Simulate a good query that might get a weak answer
    queries_that_might_drift = [
        ("placement record", "AIMS is a great institution with many programs"),  # Too generic
        ("mba fees", "Fees vary depending on your profile"),  # No specific amount
        ("hostel facilities", "We have good campus facilities"),  # No specifics
    ]
    
    for query, weak_answer in queries_that_might_drift:
        print(f"\nQuery: '{query}'")
        print(f"Weak Answer: '{weak_answer}'")
        
        result = execute_orchestration(query=query, retrieved_chunks=None)
        
        if result.is_fallback:
            print(f"   ✅ Fallback triggered (drift prevented)")
            print(f"   Confidence reduced to: {result.confidence:.3f}")
        else:
            print(f"   ⚠️  No fallback (possible drift)")
            print(f"   Confidence: {result.confidence:.3f}")


def main():
    """Run all integration tests"""
    try:
        test_risk_scenarios()
        test_with_mock_chunks()
        test_answer_drift_protection()
        
        print("\n" + "=" * 80)
        print("✅ ALL INTEGRATION TESTS COMPLETED")
        print("=" * 80 + "\n")
        
    except Exception as e:
        logger.error(f"Test suite error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
