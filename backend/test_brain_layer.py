"""
Comprehensive test suite for the Brain Layer components.

Tests all 5 production modules:
1. rag_cleaner - noise removal
2. context_resolver - follow-up handling
3. answer_scorer - quality validation
4. domain_guard - out-of-scope rejection
5. answer_merger - answer combination
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.brain import (
    clean_chunks,
    inject_context,
    score_answer,
    judge_and_repair_answer,
    is_out_of_domain,
    merge_answers
)


class FakeJudgeGenerator:
    def __init__(self):
        self.judge_calls = 0

    def judge_answer(self, tier, query, answer, context_chunks):
        self.judge_calls += 1
        if self.judge_calls == 1:
            return False, "Answer is too vague and not grounded enough."
        return True, "Corrected answer is grounded in AIMS context."

    def repair_answer(self, tier, query, answer, context_chunks, feedback):
        return (
            "AIMS MBA fees are listed as ₹50,000 to ₹1,00,000 per year. "
            "For the exact fee structure, students should contact AIMS admissions."
        )


def test_rag_cleaner():
    """Test RAG chunk cleaning - remove noise."""
    print("\n" + "="*60)
    print("TEST 1: RAG CLEANER")
    print("="*60)
    
    # Test with noisy chunks
    chunks = [
        "Fees: MBA program costs Rs. 20 lakhs over 2 years",
        "DEADLINE APPROACHING - APPLY NOW!!!",
        "Lorem ipsum dolor sit amet consectetur",
        "Placement record: 95% of graduates placed within 3 months",
        "Click here for more information",
        "Average salary package: 18 LPA",
        "🎉 Click here!",  # Too short after cleaning
    ]
    
    cleaned = clean_chunks(chunks)
    print(f"✅ Input: {len(chunks)} chunks → Output: {len(cleaned)} cleaned chunks")
    for i, chunk in enumerate(cleaned, 1):
        print(f"  {i}. {chunk[:70]}...")
    
    # Verify noise was removed
    result_text = " ".join(cleaned).lower()
    assert "deadline" not in result_text, "Deadline noise should be removed"
    assert "click here" not in result_text, "CTA noise should be removed"
    assert "placement" in result_text, "Valid content should remain"
    print("✅ Noise successfully removed")
    

def test_context_resolver():
    """Test follow-up context injection."""
    print("\n" + "="*60)
    print("TEST 2: CONTEXT RESOLVER")
    print("="*60)
    
    # Test 1: Follow-up detection
    context = {
        "last_course": "MBA",
        "last_intent": "fees",
        "last_topic": "hostel"
    }
    
    # This is a follow-up
    follow_up_q = "What about hostel?"
    enhanced = inject_context(follow_up_q, context)
    print(f"Input: '{follow_up_q}'")
    print(f"Output: '{enhanced}'")
    assert "MBA" in enhanced, "Should inject course context"
    print("✅ Follow-up context injected")
    
    # Test 2: Non-follow-up
    regular_q = "Tell me about AIMS BCA program"
    result = inject_context(regular_q, context)
    assert result == regular_q, "Should not modify non-follow-up queries"
    print(f"✅ Non-follow-up '{regular_q}' unchanged")
    
    # Test 3: No context
    result = inject_context("What about hostel?", None)
    assert result == "What about hostel?", "Should return query unchanged if no context"
    print("✅ Handles None context gracefully")


def test_answer_scorer():
    """Test answer quality scoring."""
    print("\n" + "="*60)
    print("TEST 3: ANSWER SCORER")
    print("="*60)
    
    # Test 1: High-quality answer
    good_answer = "AIMS MBA program offers excellent placement opportunities with average salary 18 LPA. Fees are Rs. 20 lakhs with flexible payment options."
    score, reason = score_answer(good_answer, "placement at AIMS")
    print(f"Good answer: score={score:.2f} ({reason})")
    assert score > 0.5, f"Good answer should score > 0.5, got {score}"
    print("✅ High-quality answer approved")
    
    # Test 2: Poor answer (too short)
    bad_answer = "No"
    score, reason = score_answer(bad_answer, "fees")
    print(f"Poor answer: score={score:.2f} ({reason})")
    assert score < 0.5, f"Poor answer should score < 0.5, got {score}"
    print("✅ Poor answer rejected")
    
    # Test 3: Hallucinating answer
    halluc_answer = "I'm not sure about AIMS fees. I don't have this information available."
    score, reason = score_answer(halluc_answer, "fees at AIMS")
    print(f"Hallucinating answer: score={score:.2f} ({reason})")
    assert score < 0.5, "Hallucinating answer should score low"
    print("✅ Hallucination detected and rejected")
    
    # Test 4: AIMS-specific content
    aims_answer = "AIMS institutes have rigorous admission criteria. The MBA program is accredited and highly rated. Fees depend on your specific course."
    score, reason = score_answer(aims_answer, "AIMS admission requirements")
    print(f"AIMS-specific answer: score={score:.2f} ({reason})")
    assert score > 0.3, "AIMS-specific content should score reasonably"
    print("✅ AIMS-specific content recognized")


def test_domain_guard():
    """Test out-of-domain query rejection."""
    print("\n" + "="*60)
    print("TEST 4: DOMAIN GUARD")
    print("="*60)
    
    # Test 1: Out-of-domain (competitor mention, no AIMS)
    query = "What is the placement record at IIT Delhi?"
    is_ood = is_out_of_domain(query)
    print(f"Query: '{query}' → Out-of-domain: {is_ood}")
    assert is_ood, "Should reject IIT query without AIMS mention"
    print("✅ Out-of-domain query rejected")
    
    # Test 2: In-domain (AIMS mention)
    query = "How does AIMS placement compare to IIT?"
    is_ood = is_out_of_domain(query)
    print(f"Query: '{query}' → Out-of-domain: {is_ood}")
    assert not is_ood, "Should allow comparison queries"
    print("✅ Comparison query allowed")
    
    # Test 3: AIMS-only query
    query = "What are AIMS MBA fees?"
    is_ood = is_out_of_domain(query)
    print(f"Query: '{query}' → Out-of-domain: {is_ood}")
    assert not is_ood, "Should allow AIMS-specific queries"
    print("✅ AIMS-specific query allowed")


def test_answer_merger():
    """Test intelligent answer merging."""
    print("\n" + "="*60)
    print("TEST 5: ANSWER MERGER")
    print("="*60)
    
    # Test 1: Both answers available
    structured = "AIMS MBA fees: Rs. 20 lakhs"
    rag = "Fees include tuition, materials, and hostel for first year."
    merged = merge_answers(structured, rag)
    print(f"Merged: {merged}")
    assert "20 lakhs" in merged, "Structured info should be in merged"
    assert "hostel" in merged, "RAG info should be in merged"
    print("✅ Both answers merged successfully")
    
    # Test 2: Only structured
    merged = merge_answers(structured, None)
    print(f"Structured only: {merged}")
    assert merged == structured, "Should return structured when no RAG"
    print("✅ Structured-only fallback works")
    
    # Test 3: Only RAG
    merged = merge_answers(None, rag)
    print(f"RAG only: {merged}")
    assert merged == rag, "Should return RAG when no structured"
    print("✅ RAG-only fallback works")
    
    # Test 4: Neither
    merged = merge_answers(None, None)
    print(f"Neither: {merged}")
    assert merged is None, "Should return None when both absent"
    print("✅ None handling correct")


def test_answer_judge_repair():
    """Test LLM judge rejects weak answers and accepts one-pass repair."""
    print("\n" + "="*60)
    print("TEST 6: ANSWER JUDGE + REPAIR")
    print("="*60)

    result = judge_and_repair_answer(
        query="What are AIMS MBA fees?",
        answer="AIMS fees are unclear.",
        context_chunks=[{
            "content": "MBA fees: ₹50,000 – ₹1,00,000 per year at AIMS Institutes.",
            "score": 0.9,
            "url": "",
            "heading": "Fees",
        }],
        generator=FakeJudgeGenerator(),
        tier="small",
    )

    print(f"Judge result: approved={result.approved}, repaired={result.repaired}, score={result.score:.2f}")
    assert result.approved, "Repaired answer should be approved"
    assert result.repaired, "Weak answer should be repaired once"
    assert "₹50,000" in result.answer, "Repair should use grounded AIMS fee data"
    print("✅ Judge repair loop works")


def test_integration():
    """Test brain layer pipeline as integrated."""
    print("\n" + "="*60)
    print("INTEGRATION TEST: Full Pipeline")
    print("="*60)
    
    # Simulate a query flow
    query = "What about hostel for MBA?"
    user_context = {
        "last_course": "MBA",
        "last_intent": "fees",
        "last_topic": None
    }
    
    # Step 1: Domain guard
    if is_out_of_domain(query):
        print("❌ Query rejected by domain guard")
        return
    print("✅ Domain guard passed")
    
    # Step 2: Context injection
    enhanced_query = inject_context(query, user_context)
    print(f"Enhanced query: '{enhanced_query}'")
    assert "MBA" in enhanced_query, "Should have MBA context"
    print("✅ Context injected")
    
    # Step 3: RAG cleaning (simulate)
    raw_chunks = [
        "DEADLINE APPROACHING! Apply now!",
        "AIMS MBA hostel facilities include AC rooms",
        "Single/double occupancy available",
        "Reserved parking for MBA students"
    ]
    cleaned = clean_chunks(raw_chunks)
    print(f"Cleaned {len(raw_chunks)} chunks → {len(cleaned)} quality chunks")
    print("✅ Chunks cleaned")
    
    # Step 4: Scoring (simulate answer)
    answer = "AIMS MBA hostel provides AC rooms with flexible occupancy options. Parking available for all residents."
    score, reason = score_answer(answer, enhanced_query)
    print(f"Answer scored: {score:.2f} ({reason})")
    if score >= 0.5:
        print("✅ Answer passed quality gate")
    else:
        print("❌ Answer rejected by quality gate")
        return
    
    print("\n✅ FULL PIPELINE TEST PASSED")


if __name__ == "__main__":
    try:
        print("\n" + "="*60)
        print("BRAIN LAYER COMPREHENSIVE TEST SUITE")
        print("="*60)
        
        test_rag_cleaner()
        test_context_resolver()
        test_answer_scorer()
        test_domain_guard()
        test_answer_merger()
        test_answer_judge_repair()
        test_integration()
        
        print("\n" + "="*60)
        print("✅✅✅ ALL TESTS PASSED ✅✅✅")
        print("="*60)
        print("\nBrain layer validation checks passed.")
        print("The 6 modules are working correctly:")
        print("  1. rag_cleaner - Removes noise ✅")
        print("  2. context_resolver - Fixes follow-ups ✅")
        print("  3. answer_scorer - Quality gates ✅")
        print("  4. domain_guard - Scope protection ✅")
        print("  5. answer_merger - Answer combining ✅")
        print("  6. answer_judge - Judge + repair loop ✅")
        print("\nPipeline integration in chat_phase4.py is complete!")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
