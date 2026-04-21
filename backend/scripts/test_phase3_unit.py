#!/usr/bin/env python3
"""
Unit Test: Answer Synthesis and Confidence Pipeline

Tests the core logic without requiring FAISS data
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.response.filter import filter_results_by_relevance
from app.services.response.confidence import calculate_confidence, get_confidence_label
from app.services.llm.answer_generator import get_answer_generator


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def create_mock_chunks(scores: list, texts: list) -> list:
    """Create mock chunks with given scores and texts"""
    chunks = []
    for score, text in zip(scores, texts):
        chunk = (text, score, f"http://example.com/doc{len(chunks)}", f"Section {len(chunks)}")
        chunks.append(chunk)
    return chunks


def test_filter_and_confidence():
    """Test filtering and confidence calculation"""
    print_section("TEST 1: Filtering and Confidence")
    
    # Create mock chunks with varying similarity scores
    mock_chunks = create_mock_chunks(
        scores=[0.85, 0.75, 0.45, 0.25],
        texts=[
            "The admission process at AIMS involves submitting an application form with required documents including academic transcripts, entrance exam scores, and a personal statement. Interviews may be conducted to assess candidates' fit.",
            "Students must provide their previous academic records and standardized test scores as part of the admission requirements.",
            "Entrance exams are standardized tests used in many countries.",
            "Weather today is sunny and warm.",
        ]
    )
    
    print(f"Original chunks: {len(mock_chunks)}")
    for i, chunk in enumerate(mock_chunks):
        print(f"  {i+1}. Score: {chunk[1]:.2f}, Text: {chunk[0][:50]}...")
    
    # Filter by relevance (min_score=0.5)
    print("\nFiltering with min_score=0.5...")
    filtered = filter_results_by_relevance(mock_chunks, min_score=0.5)
    print(f"Filtered chunks: {len(filtered)}")
    for i, chunk in enumerate(filtered):
        print(f"  {i+1}. Score: {chunk[1]:.2f}, Text: {chunk[0][:50]}...")
    
    # Calculate confidence
    print("\nCalculating confidence...")
    confidence = calculate_confidence(filtered)
    label = get_confidence_label(confidence)
    print(f"Confidence: {confidence:.2f} ({label})")
    
    assert len(filtered) == 2, "Should have 2 chunks after filtering"
    assert confidence > 0.5, "Should have high confidence"
    print("✅ PASS: Filter and confidence working correctly")
    
    return confidence >= 0.5


def test_answer_synthesis():
    """Test answer synthesis from multiple chunks"""
    print_section("TEST 2: Answer Synthesis")
    
    query = "What is the admission process?"
    
    # Create mock chunks about admission
    mock_chunks = create_mock_chunks(
        scores=[0.85, 0.72],
        texts=[
            "The admission process at AIMS involves submitting an application form with required documents including academic transcripts and entrance exam scores. Interviews may be conducted to assess candidates' suitability for the program.",
            "Students are required to submit their previous academic records, standardized test scores, and a personal statement explaining their interest in the program. All materials should be submitted through the online portal.",
        ]
    )
    
    print(f"Query: '{query}'")
    print(f"Chunks provided: {len(mock_chunks)}\n")
    
    # Synthesize answer
    answer_gen = get_answer_generator()
    answer = answer_gen.synthesize(query, mock_chunks)
    
    print(f"Synthesized answer:\n  \"{answer}\"")
    print(f"\nAnswer length: {len(answer)} characters")
    
    # Validate
    assert len(answer) > 30, "Answer should have meaningful content"
    assert "admission" in answer.lower(), "Answer should contain query-related content"
    assert answer.endswith(('.', '!', '?')), "Answer should end with punctuation"
    
    print("✅ PASS: Answer synthesis working correctly")
    return True


def test_fallback_low_confidence():
    """Test that low confidence triggers fallback"""
    print_section("TEST 3: Fallback on Low Confidence")
    
    # Create mock chunks with low relevance
    mock_chunks = create_mock_chunks(
        scores=[0.25, 0.20],
        texts=[
            "Clear skies expected today with mild temperatures.",
            "Traffic in downtown areas may be heavier than usual.",
        ]
    )
    
    print("Low relevance chunks (unrelated to query)")
    for i, chunk in enumerate(mock_chunks):
        print(f"  {i+1}. Score: {chunk[1]:.2f}, Text: {chunk[0][:50]}...")
    
    # Filter by relevance
    print("\nFiltering with min_score=0.5...")
    filtered = filter_results_by_relevance(mock_chunks, min_score=0.5)
    print(f"Filtered chunks: {len(filtered)}")
    
    # Calculate confidence
    confidence = calculate_confidence(filtered) if filtered else 0.0
    label = get_confidence_label(confidence)
    print(f"Confidence: {confidence:.2f} ({label})")
    
    fallback_threshold = 0.4
    is_fallback = confidence < fallback_threshold or not filtered
    
    print(f"Fallback triggered: {is_fallback} (threshold={fallback_threshold})")
    
    assert is_fallback, "Should trigger fallback for low confidence"
    print("✅ PASS: Fallback correctly triggered")
    return True


def test_deduplication():
    """Test that synthesis removes duplicates"""
    print_section("TEST 4: Deduplication in Synthesis")
    
    query = "What are the requirements?"
    
    # Create chunks with duplicate content
    mock_chunks = create_mock_chunks(
        scores=[0.8, 0.75],
        texts=[
            "You need to submit academic transcripts and entrance exam scores. These documents are required for all applicants. Your transcripts should show your academic performance and your exam scores should be from recognized standardized tests.",
            "Academic transcripts and entrance exam scores must be submitted by all applicants. Your previous academic records and test scores are essential requirements.",
        ]
    )
    
    print(f"Query: '{query}'")
    print(f"Chunks with duplicate content:\n")
    for i, chunk in enumerate(mock_chunks):
        print(f"  Chunk {i+1}:\n    {chunk[0]}\n")
    
    # Synthesize
    answer_gen = get_answer_generator()
    answer = answer_gen.synthesize(query, mock_chunks)
    
    print(f"Synthesized answer (deduped):\n  \"{answer}\"")
    
    # Validate - answer should be shorter than concatenating both chunks
    total_length = sum(len(chunk[0]) for chunk in mock_chunks)
    assert len(answer) < total_length, "Answer should be shorter than raw concatenation"
    assert answer.count("transcripts") <= 2, "Duplicates should be reduced"
    
    print(f"\nOriginal total length: {total_length}")
    print(f"Synthesized length: {len(answer)} (compression ratio: {len(answer)/total_length:.1%})")
    print("✅ PASS: Deduplication working")
    return True


def test_full_pipeline():
    """Test complete pipeline: filter → confidence → synthesize"""
    print_section("TEST 5: Full Pipeline (Good Query)")
    
    query = "What is the admission process?"
    
    # Step 1: Start with mixed quality results
    raw_chunks = create_mock_chunks(
        scores=[0.88, 0.75, 0.45, 0.20],
        texts=[
            "AIMS admission process: Submit application with academic records, exam scores, and personal statement. Panel interviews assess candidate suitability. Final decision communicated within 30 days.",
            "Required documents include high school transcripts, standardized test scores (SAT/ACT), and letters of recommendation from teachers familiar with your academic work.",
            "Many universities require standardized tests for admission decisions.",
            "Coffee is popular in many countries around the world.",
        ]
    )
    
    print(f"Step 1: Retrieved {len(raw_chunks)} raw chunks")
    
    # Step 2: Filter
    filtered = filter_results_by_relevance(raw_chunks, min_score=0.5)
    print(f"Step 2: Filtered to {len(filtered)} relevant chunks")
    
    # Step 3: Calculate confidence
    confidence = calculate_confidence(filtered)
    conf_label = get_confidence_label(confidence)
    print(f"Step 3: Confidence = {confidence:.2f} ({conf_label})")
    
    # Step 4: Check fallback
    is_fallback = confidence < 0.4
    print(f"Step 4: Fallback needed = {is_fallback}")
    
    if not is_fallback:
        # Step 5: Synthesize
        answer_gen = get_answer_generator()
        answer = answer_gen.synthesize(query, filtered)
        print(f"Step 5: Generated answer ({len(answer)} chars)")
        print(f"  \"{answer}\"")
    
    print("\n✅ PASS: Full pipeline completed successfully")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  PHASE 3: VALIDATION - Core Logic Tests")
    print("="*70)
    
    tests = [
        ("Filter & Confidence", test_filter_and_confidence),
        ("Answer Synthesis", test_answer_synthesis),
        ("Fallback Trigger", test_fallback_low_confidence),
        ("Deduplication", test_deduplication),
        ("Full Pipeline", test_full_pipeline),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {len(tests)}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
