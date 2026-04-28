#!/usr/bin/env python3
"""
Test multi-intent handling with real API calls.
Tests query order preservation and course context handling.
"""

import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot')
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

import json
from app.services.orchestration.engine import execute_orchestration

def test_multi_intent_queries():
    """Test multi-intent queries with different course contexts."""
    
    test_cases = [
        {
            "query": "What is AIMS and fees for BCA",
            "course": "BCA",
            "expected_intents": ["about_aims", "fees"],
            "description": "Institution + course fees"
        },
        {
            "query": "Tell me about AIMS, placement for MBA, and hostel facilities",
            "course": "MBA",
            "expected_intents": ["about_aims", "placements", "aims_features"],
            "description": "Institution + course placement + facilities"
        },
        {
            "query": "BCA fees and admission process",
            "course": "BCA",
            "expected_intents": ["fees", "admission"],
            "description": "Course fees + admission"
        },
        {
            "query": "Why AIMS and what courses are available",
            "course": None,
            "expected_intents": ["why_aims", "courses"],
            "description": "Why AIMS + courses (no course context)"
        },
        {
            "query": "Fees, placements, and scholarships",
            "course": "BCA",
            "expected_intents": ["fees", "placements", "scholarship"],
            "description": "Multiple course-related intents"
        },
    ]
    
    print("\n" + "="*100)
    print("MULTI-INTENT QUERY TESTING")
    print("="*100)
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        query = test["query"]
        course = test["course"]
        expected_intents = test["expected_intents"]
        description = test["description"]
        
        print(f"\n{'='*100}")
        print(f"Test {i}: {description}")
        print(f"{'='*100}")
        print(f"Query: '{query}'")
        print(f"Course: {course if course else 'None (no context)'}")
        print(f"Expected intents: {expected_intents}")
        
        # Build context
        context = {}
        if course:
            context["course"] = course
        
        try:
            # Execute orchestration
            result = execute_orchestration(query, context=context)
            
            print(f"\nResponse:")
            print(f"  Mode: {getattr(result, 'mode', 'unknown')}")
            answer = getattr(result, 'answer', '')
            print(f"  Answer preview: {answer[:150]}...")
            
            # Extract detected intents from response
            # This is a heuristic - in real system, we'd log this
            response_text = answer.lower()
            
            detected_intents = []
            intent_keywords = {
                "about_aims": ["about aims", "aims institutes", "institution"],
                "fees": ["fee", "cost", "charges", "structure"],
                "placements": ["placement", "salary", "package", "job"],
                "admission": ["admission", "apply", "eligibility"],
                "aims_features": ["facilities", "campus", "infrastructure"],
                "why_aims": ["why aims", "why choose", "benefits"],
                "courses": ["course", "program", "degree"],
                "scholarship": ["scholarship", "financial aid"],
            }
            
            for intent, keywords in intent_keywords.items():
                if any(kw in response_text for kw in keywords):
                    detected_intents.append(intent)
            
            print(f"\nDetected intents (from response): {detected_intents}")
            
            # Check if all expected intents are answered
            all_answered = all(intent in detected_intents for intent in expected_intents)
            print(f"All expected intents answered: {'✅ YES' if all_answered else '❌ NO'}")
            
            # Check order (heuristic - check if intents appear in query order)
            query_lower = query.lower()
            intent_positions = {}
            for intent in detected_intents:
                keywords = intent_keywords.get(intent, [])
                min_pos = len(query)
                for kw in keywords:
                    pos = query_lower.find(kw.lower())
                    if pos != -1 and pos < min_pos:
                        min_pos = pos
                intent_positions[intent] = min_pos
            
            # Sort by position
            sorted_intents = sorted(detected_intents, key=lambda x: intent_positions.get(x, len(query)))
            order_correct = sorted_intents == detected_intents
            print(f"Order matches query: {'✅ YES' if order_correct else '❌ NO'}")
            print(f"  Expected order: {expected_intents}")
            print(f"  Detected order: {detected_intents}")
            
            # Check for wrong course data
            wrong_course_issue = False
            if course and course != "BCA":
                # Check if BCA data appears when it shouldn't
                if "bca" in response_text.lower() and course.lower() not in response_text.lower():
                    wrong_course_issue = True
                    print(f"⚠️ Wrong course data: BCA mentioned but {course} selected")
            
            # Record result
            results.append({
                "query": query,
                "course": course,
                "intents_detected": detected_intents,
                "all_answered": all_answered,
                "order_correct": order_correct,
                "wrong_course": wrong_course_issue,
                "issues": [] if (all_answered and order_correct and not wrong_course_issue) else [
                    "Missing intents" if not all_answered else None,
                    "Wrong order" if not order_correct else None,
                    "Wrong course data" if wrong_course_issue else None,
                ]
            })
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                "query": query,
                "course": course,
                "intents_detected": [],
                "all_answered": False,
                "order_correct": False,
                "wrong_course": False,
                "issues": [f"Exception: {str(e)}"]
            })
    
    # Print summary table
    print("\n" + "="*100)
    print("SUMMARY TABLE")
    print("="*100)
    
    print(f"\n{'Query':<50} | {'Intents':<30} | {'All?':<5} | {'Order?':<7} | {'Issues':<30}")
    print("-" * 130)
    
    for result in results:
        query_short = result["query"][:47] + "..." if len(result["query"]) > 50 else result["query"]
        intents_str = ",".join(result["intents_detected"][:2])
        all_answered = "✅" if result["all_answered"] else "❌"
        order_correct = "✅" if result["order_correct"] else "❌"
        issues_str = "; ".join([i for i in result["issues"] if i])[:27]
        
        print(f"{query_short:<50} | {intents_str:<30} | {all_answered:<5} | {order_correct:<7} | {issues_str:<30}")
    
    # Print detailed results
    print("\n" + "="*100)
    print("DETAILED RESULTS")
    print("="*100)
    
    for i, result in enumerate(results, 1):
        print(f"\nTest {i}:")
        print(f"  Query: {result['query']}")
        print(f"  Course: {result['course']}")
        print(f"  Intents detected: {result['intents_detected']}")
        print(f"  All answered: {'✅ YES' if result['all_answered'] else '❌ NO'}")
        print(f"  Order correct: {'✅ YES' if result['order_correct'] else '❌ NO'}")
        print(f"  Wrong course data: {'⚠️ YES' if result['wrong_course'] else '✅ NO'}")
        if result['issues']:
            print(f"  Issues: {', '.join([i for i in result['issues'] if i])}")
    
    # Print statistics
    print("\n" + "="*100)
    print("STATISTICS")
    print("="*100)
    
    total = len(results)
    all_answered_count = sum(1 for r in results if r["all_answered"])
    order_correct_count = sum(1 for r in results if r["order_correct"])
    no_issues_count = sum(1 for r in results if not any(r["issues"]))
    
    print(f"\nTotal tests: {total}")
    print(f"All intents answered: {all_answered_count}/{total} ({all_answered_count*100//total}%)")
    print(f"Order correct: {order_correct_count}/{total} ({order_correct_count*100//total}%)")
    print(f"No issues: {no_issues_count}/{total} ({no_issues_count*100//total}%)")
    
    # Print recommendations
    print("\n" + "="*100)
    print("OBSERVATIONS (DO NOT FIX)")
    print("="*100)
    
    if all_answered_count < total:
        print(f"\n⚠️ {total - all_answered_count} queries missing intents")
        print("   This is expected - real users will reveal patterns")
    
    if order_correct_count < total:
        print(f"\n⚠️ {total - order_correct_count} queries have wrong order")
        print("   This indicates query order preservation needs work")
    
    if no_issues_count == total:
        print(f"\n✅ All tests passed - system handles multi-intent well")
    else:
        print(f"\n⚠️ {total - no_issues_count} tests have issues")
        print("   Collect real user data to understand patterns")


if __name__ == "__main__":
    print("\n" + "="*100)
    print("MULTI-INTENT QUERY TESTING SUITE")
    print("="*100)
    
    try:
        test_multi_intent_queries()
        
        print("\n" + "="*100)
        print("TEST COMPLETE")
        print("="*100)
        print("\nReminder: Do NOT fix anything based on these results.")
        print("Collect real user data first to understand actual patterns.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
