#!/usr/bin/env python3
"""
QUICK VALIDATION TEST - Verify all 3 modules work before integration

Run this to make sure the modules are correctly implemented:
    python backend/app/services/test_integration_modules.py
"""

import sys
import sys as system
from pathlib import Path

# Setup path BEFORE any logging imports to avoid shadowing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Now import logging from standard library explicitly
import logging as stdlib_logging
stdlib_logging.basicConfig(level=stdlib_logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')
logger = stdlib_logging.getLogger(__name__)


def test_response_transformer():
    """Test response_transformer module"""
    logger.info("=" * 60)
    logger.info("TEST 1: Response Transformer")
    logger.info("=" * 60)
    
    try:
        from app.services.response_transformer import (
            detect_intent_from_answer,
            extract_fees_data,
            extract_placement_data,
            extract_facilities_data,
            transform_to_card,
            format_response_for_ui
        )
        logger.info("✅ Imports successful")
        
        # Test 1: Detect fees
        fees_answer = "MBA fees range from ₹15,00,000 – ₹25,00,000 per year"
        card_type = detect_intent_from_answer(fees_answer)
        assert card_type == "fees_card", f"Expected fees_card, got {card_type}"
        logger.info(f"✅ Fees detection: {card_type}")
        
        # Test 2: Extract fees
        fees_data = extract_fees_data(fees_answer)
        assert fees_data["range"] is not None, "Fee range not extracted"
        logger.info(f"✅ Fees extraction: {fees_data['range']}")
        
        # Test 3: Detect placement
        placement_answer = "Highest package: ₹23 LPA, Average: ₹8 LPA, Placement rate: 84%"
        card_type = detect_intent_from_answer(placement_answer)
        assert card_type == "placement_card", f"Expected placement_card, got {card_type}"
        logger.info(f"✅ Placement detection: {card_type}")
        
        # Test 4: Extract placement
        placement_data = extract_placement_data(placement_answer)
        assert placement_data["highest_package"] is not None
        logger.info(f"✅ Placement extraction: {placement_data['highest_package']}")
        
        # Test 5: Transform to card
        card = transform_to_card(placement_answer, "placements")
        assert card["type"] == "placement_card"
        logger.info(f"✅ Card transformation: {card['type']}")
        
        # Test 6: Format for UI
        ui_response = format_response_for_ui(
            answer="Test answer",
            confidence=0.85,
            intent="test",
            mode="rag"
        )
        assert "message" in ui_response
        assert "meta" in ui_response
        logger.info(f"✅ UI formatting: {list(ui_response.keys())}")
        
        logger.info("✅ ALL TRANSFORMER TESTS PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ TRANSFORMER TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_router():
    """Test query_router module"""
    logger.info("=" * 60)
    logger.info("TEST 2: Query Router")
    logger.info("=" * 60)
    
    try:
        from app.services.query_router import (
            QueryProfile,
            select_execution_path,
            optimize_retrieval_config,
            should_skip_layer,
            estimate_latency
        )
        logger.info("✅ Imports successful")
        
        # Test 1: Query profile - simple
        profile = QueryProfile("MBA")
        assert profile.is_simple == True
        logger.info(f"✅ Simple query profile: is_simple={profile.is_simple}")
        
        # Test 2: Query profile - complex
        profile = QueryProfile("Is MBA worth the cost compared to BCA?")
        assert profile.is_complex == True
        assert profile.is_reasoning == True
        logger.info(f"✅ Complex query profile: is_complex={profile.is_complex}, is_reasoning={profile.is_reasoning}")
        
        # Test 3: Select fast path
        config = select_execution_path("MBA fees", base_confidence=0.85)
        assert config["path"] == "fast"
        assert config["use_debate"] == False
        logger.info(f"✅ Fast path selected: {config['path']}")
        
        # Test 4: Select deep path
        config = select_execution_path("Why should I choose MBA?", base_confidence=0.5)
        assert config["path"] == "deep"
        assert config["use_debate"] == True
        logger.info(f"✅ Deep path selected: {config['path']}, debate={config['use_debate']}")
        
        # Test 5: Retrieval optimization
        retrieval_config = optimize_retrieval_config("MBA", base_confidence=0.7)
        assert "top_k" in retrieval_config
        logger.info(f"✅ Retrieval config: top_k={retrieval_config['top_k']}")
        
        # Test 6: Layer skipping
        should_skip = should_skip_layer("verification", base_confidence=0.9)
        assert should_skip == True
        logger.info(f"✅ Skip verification at 0.9 confidence: {should_skip}")
        
        # Test 7: Latency estimate
        config = {"latency_target_ms": 200}
        latency = estimate_latency(config)
        assert latency == 200
        logger.info(f"✅ Latency estimate: {latency}ms")
        
        logger.info("✅ ALL ROUTER TESTS PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ ROUTER TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_response_debate():
    """Test response_debate module"""
    logger.info("=" * 60)
    logger.info("TEST 3: Response Debate")
    logger.info("=" * 60)
    
    try:
        from app.services.response_debate import (
            is_reasoning_query,
            should_use_debate,
            extract_claims,
            critique_answer,
            score_answer,
            debate_gate
        )
        logger.info("✅ Imports successful")
        
        # Test 1: Detect reasoning
        is_reasoning = is_reasoning_query("Is MBA worth it?")
        assert is_reasoning == True
        logger.info(f"✅ Reasoning detection: {is_reasoning}")
        
        # Test 2: Should use debate
        should_debate = should_use_debate("Compare MBA and BCA", confidence=0.5, query_length=4)
        assert should_debate == True
        logger.info(f"✅ Debate gate (low confidence): {should_debate}")
        
        should_debate = should_use_debate("MBA", confidence=0.9, query_length=1)
        assert should_debate == False
        logger.info(f"✅ Debate gate (high confidence): {should_debate}")
        
        # Test 3: Extract claims
        answer = "MBA has highest package of ₹23 LPA and average of ₹8 LPA"
        claims = extract_claims(answer)
        assert len(claims) > 0
        logger.info(f"✅ Claims extracted: {len(claims)} claims")
        
        # Test 4: Critique answer
        mock_chunks = [(answer, 0.8, "", "", "", "", 1)]
        issues = critique_answer(answer, mock_chunks)
        assert isinstance(issues, list)
        logger.info(f"✅ Critique performed: {len(issues)} issues found")
        
        # Test 5: Score answer
        score = score_answer(answer, issues=[], base_score=0.7)
        assert 0 <= score <= 1.0
        logger.info(f"✅ Answer scored: {score:.2f}")
        
        # Test 6: Debate gate (wrapper)
        mock_chunks = [(answer, 0.8, "", "", "", "", 1)]
        def mock_generate(q, c, **kw):
            return "Generated answer"
        
        result_answer, result_conf = debate_gate(
            "Is MBA worth it?",
            "Initial answer about MBA",
            0.6,
            mock_chunks,
            mock_generate
        )
        assert isinstance(result_answer, str)
        assert isinstance(result_conf, float)
        logger.info(f"✅ Debate gate: answer_len={len(result_answer)}, conf={result_conf:.2f}")
        
        logger.info("✅ ALL DEBATE TESTS PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ DEBATE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_example_orchestration():
    """Test that example orchestration doesn't have syntax errors"""
    logger.info("=" * 60)
    logger.info("TEST 4: Example Orchestration")
    logger.info("=" * 60)
    
    try:
        from app.services import example_orchestration
        logger.info("✅ Example orchestration module imports successfully")
        
        # Check function exists
        assert hasattr(example_orchestration, 'execute_orchestration_optimized')
        logger.info("✅ execute_orchestration_optimized function found")
        
        logger.info("✅ ALL ORCHESTRATION TESTS PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ ORCHESTRATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "="*60)
    logger.info("INTEGRATION MODULE VALIDATION TEST SUITE")
    logger.info("="*60 + "\n")
    
    results = []
    
    # Run all tests
    results.append(("Response Transformer", test_response_transformer()))
    results.append(("Query Router", test_query_router()))
    results.append(("Response Debate", test_response_debate()))
    results.append(("Example Orchestration", test_example_orchestration()))
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        logger.info("\n🚀 ALL TESTS PASSED - Ready to integrate!")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} test(s) failed - Fix errors before integrating")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
