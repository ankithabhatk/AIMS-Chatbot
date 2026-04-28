"""
Course Boundary Tests - MANDATORY

These tests ensure the system NEVER recommends courses not offered by the college.
If any of these fail, the system will break user trust.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.counselor.interest_mapper import map_interest_to_course
from app.services.counselor.guidance_engine import run_guidance_engine
from app.config.college_courses import get_college_courses, enforce_course_boundary


def test_hard_blocks():
    """Test that unavailable courses are hard-blocked"""
    print("\n=== Testing Hard Blocks ===")
    
    test_cases = [
        ("I want MBBS", None, "medical not offered"),
        ("I want to be a doctor", None, "medical not offered"),
        ("interested in pilot training", None, "aviation not offered"),
        ("I want to study law", None, "law not offered"),
        ("nursing course", None, "nursing not offered"),
    ]
    
    for query, expected_course, reason in test_cases:
        result = map_interest_to_course(query)
        
        assert result["course"] == expected_course, \
            f"FAILED: {reason} | Query: '{query}' | Got: {result['course']}"
        assert result["type"] == "hard_block", \
            f"FAILED: Should be hard_block | Query: '{query}' | Got: {result['type']}"
        
        print(f"✅ '{query}' → Hard Block (Correct)")
    
    print("✅ All hard block tests passed")


def test_soft_redirects():
    """Test that related interests redirect to closest course"""
    print("\n=== Testing Soft Redirects ===")
    
    test_cases = [
        ("I want psychology", "BBA", "redirect to BBA-HR"),
        ("interested in design", "BCA", "redirect to BCA-UI/UX"),
        ("I like graphics", "BCA", "redirect to BCA-design"),
        ("want to study engineering", "BCA", "redirect to BCA-tech"),
    ]
    
    for query, expected_course, reason in test_cases:
        result = map_interest_to_course(query)
        
        assert result["course"] == expected_course, \
            f"FAILED: {reason} | Query: '{query}' | Expected: {expected_course} | Got: {result['course']}"
        assert result["type"] == "soft_redirect", \
            f"FAILED: Should be soft_redirect | Query: '{query}' | Got: {result['type']}"
        assert result["redirect_message"] is not None, \
            f"FAILED: Missing redirect message | Query: '{query}'"
        
        print(f"✅ '{query}' → {expected_course} (Redirect)")
    
    print("✅ All soft redirect tests passed")


def test_direct_matches():
    """Test that offered courses match directly"""
    print("\n=== Testing Direct Matches ===")
    
    test_cases = [
        ("I like coding", "BCA", "tech interest"),
        ("interested in business", "BBA", "business interest"),
        ("I want to study finance", "B.Com", "finance interest"),
        ("hotel management", "BHM", "hospitality interest"),
        ("programming and software", "BCA", "tech signals"),
        ("marketing and sales", "BBA", "business signals"),
    ]
    
    for query, expected_course, reason in test_cases:
        result = map_interest_to_course(query)
        
        assert result["course"] == expected_course, \
            f"FAILED: {reason} | Query: '{query}' | Expected: {expected_course} | Got: {result['course']}"
        assert result["is_direct_match"] == True, \
            f"FAILED: Should be direct match | Query: '{query}'"
        
        print(f"✅ '{query}' → {expected_course} (Direct Match)")
    
    print("✅ All direct match tests passed")


def test_guidance_engine_boundary():
    """Test that guidance engine only recommends college courses"""
    print("\n=== Testing Guidance Engine Boundary ===")
    
    college_courses = set(get_college_courses())
    
    test_queries = [
        "I got 70% and like coding",
        "I got 60% and interested in business",
        "I got 55% and want finance career",
        "I got 65% marks after 12th",
    ]
    
    for query in test_queries:
        result = run_guidance_engine(query, {})
        
        top_course = result.get("top_course")
        recommended = result.get("recommended_courses", [])
        
        # Check top course is within boundary
        assert top_course in college_courses, \
            f"FAILED: Top course '{top_course}' not in college offerings | Query: '{query}'"
        
        # Check all recommended courses are within boundary
        for course in recommended:
            assert course in college_courses, \
                f"FAILED: Recommended course '{course}' not in college offerings | Query: '{query}'"
        
        print(f"✅ '{query}' → {top_course} (Within Boundary)")
    
    print("✅ All guidance engine boundary tests passed")


def test_course_boundary_enforcement():
    """Test the enforce_course_boundary function"""
    print("\n=== Testing Course Boundary Enforcement ===")
    
    test_cases = [
        (["BCA", "BBA", "MBBS"], ["BCA", "BBA"]),
        (["Psychology", "BCA"], ["BCA"]),
        (["MBA", "Law", "B.Com"], ["MBA", "B.Com"]),
        (["MBBS", "Pilot", "Law"], []),
    ]
    
    for input_courses, expected_output in test_cases:
        result = enforce_course_boundary(input_courses)
        
        assert result == expected_output, \
            f"FAILED: Input: {input_courses} | Expected: {expected_output} | Got: {result}"
        
        print(f"✅ {input_courses} → {expected_output}")
    
    print("✅ All boundary enforcement tests passed")


def test_multiple_interests():
    """Test handling of multiple interests"""
    print("\n=== Testing Multiple Interests ===")
    
    test_cases = [
        ("I like business and coding", ["BBA", "BCA"], "should match both"),
        ("interested in finance and technology", ["B.Com", "BCA"], "should match both"),
    ]
    
    for query, possible_courses, reason in test_cases:
        result = map_interest_to_course(query)
        
        assert result["course"] in possible_courses, \
            f"FAILED: {reason} | Query: '{query}' | Expected one of: {possible_courses} | Got: {result['course']}"
        
        print(f"✅ '{query}' → {result['course']} (Multiple Interests)")
    
    print("✅ All multiple interest tests passed")


if __name__ == "__main__":
    print("=" * 60)
    print("COURSE BOUNDARY TESTS - MANDATORY")
    print("=" * 60)
    
    try:
        test_hard_blocks()
        test_soft_redirects()
        test_direct_matches()
        test_guidance_engine_boundary()
        test_course_boundary_enforcement()
        test_multiple_interests()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - SYSTEM BOUNDARY IS SECURE")
        print("=" * 60)
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        sys.exit(1)
