#!/usr/bin/env python3
"""
PRODUCTION VALIDATION TEST - All 4 Dimensions + Stress Test
Validates: Relevance, Length, Context, Noise Filtering, Fee Intent
"""

import requests
import json
import time
from typing import Dict, List, Tuple

BASE_URL = "http://127.0.0.1:8000"
SESSION_ID = "test-session-validation"

class ValidationResult:
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = 0
        self.failed = 0
        self.checks = []
    
    def check(self, condition: bool, message: str):
        if condition:
            self.passed += 1
            self.checks.append(f"  ✅ {message}")
        else:
            self.failed += 1
            self.checks.append(f"  ❌ {message}")
    
    def print_summary(self):
        print(f"\n{'='*70}")
        print(f"TEST: {self.test_name}")
        print(f"{'='*70}")
        for check in self.checks:
            print(check)
        total = self.passed + self.failed
        status = "✅ PASSED" if self.failed == 0 else "❌ FAILED"
        print(f"\nResult: {self.passed}/{total} checks passed [{status}]")
        return self.failed == 0

def query_api(query: str, session_id: str = SESSION_ID) -> Tuple[Dict, float]:
    """Query API and return response + latency"""
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json={"query": query, "session_id": session_id},
            timeout=15
        )
        latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            return response.json(), latency
        else:
            return {"error": response.status_code}, latency
    except Exception as e:
        return {"error": str(e)}, (time.time() - start) * 1000

def extract_answer(data: Dict) -> str:
    """Extract answer from response"""
    return data.get("answer", "")

def run_relevance_test():
    """TEST 1: Relevance - Does it stay on topic? No BBA/MBA mixing?"""
    result = ValidationResult("1️⃣  RELEVANCE TEST")
    
    test_queries = [
        ("placements", "single word"),
        ("What about placements?", "question"),
        ("campus facilities", "compound topic"),
        ("hostel", "single facility"),
    ]
    
    for query, desc in test_queries:
        data, latency = query_api(query)
        answer = extract_answer(data)
        
        if "error" in data:
            result.check(False, f"'{query}' ({desc}) - API error")
            continue
        
        is_fallback = data.get("fallback", False)
        mode = data.get("mode", "")
        
        # Check: not fallback
        result.check(not is_fallback, f"'{query}' - not fallback")
        
        # Check: actual content
        result.check(len(answer) > 50, f"'{query}' - has content (len={len(answer)})")
        
        # Check: stays on topic (placements content mentions placement/salary/recruiter)
        if "placement" in query.lower():
            has_topic = any(w in answer.lower() for w in ["placement", "salary", "recruiter", "package", "hiring"])
            result.check(has_topic, f"'{query}' - stays on topic (placement)")
        
        # Check: no random course mixing
        has_course_mix = ("BBA" in answer and "MBA" in answer and 
                         query.lower() not in ["all courses", "comparison"])
        result.check(not has_course_mix, f"'{query}' - no random BBA/MBA mixing")
        
        print(f"  Query: '{query}' | Mode: {mode} | Chars: {len(answer)} | Latency: {latency:.0f}ms")
    
    return result.print_summary()

def run_length_test():
    """TEST 2: Length & Readability - Under 500 chars? 3-5 lines? Clean bullets?"""
    result = ValidationResult("2️⃣  LENGTH & READABILITY TEST")
    
    test_queries = [
        "Tell me about placements",
        "campus facilities",
        "hostel information",
        "admission process",
    ]
    
    for query in test_queries:
        data, latency = query_api(query)
        answer = extract_answer(data)
        
        if "error" in data:
            result.check(False, f"'{query}' - API error")
            continue
        
        chars = len(answer)
        lines = len(answer.split("\n"))
        bullets = answer.count("•")
        
        # Check: under 500 chars (or structured path which is allowed to be shorter)
        is_structured = data.get("mode") == "structured"
        max_chars = 300 if is_structured else 500
        result.check(chars <= max_chars, f"'{query}' - under {max_chars} chars ({chars})")
        
        # Check: 3-5 lines
        result.check(3 <= lines <= 5, f"'{query}' - 3-5 lines ({lines})")
        
        # Check: sensible bullets (0-3)
        result.check(bullets <= 3, f"'{query}' - reasonable bullets ({bullets})")
        
        # Check: can read in 5 seconds (avg 200 chars per 5 secs = ~40 chars/sec)
        readability_time = chars / 40  # rough estimate
        result.check(readability_time <= 5, f"'{query}' - readable in <5 sec ({readability_time:.1f}s)")
        
        print(f"  Query: '{query}' | Chars: {chars} | Lines: {lines} | Bullets: {bullets}")
    
    return result.print_summary()

def run_context_test():
    """TEST 3: Context - Does conversation flow work? Course context preserved?"""
    result = ValidationResult("3️⃣  CONTEXT TEST (Conversation Flow)")
    
    # Simulate: MBA fees → What about placements → And facilities
    session = "context-test-session"
    
    # Q1: MBA fees
    data1, _ = query_api("MBA fees", session)
    answer1 = extract_answer(data1)
    
    result.check(
        not data1.get("fallback", False) and len(answer1) > 30,
        "Q1: 'MBA fees' returns structured answer"
    )
    result.check(
        "fee" in answer1.lower() or "₹" in answer1,
        "Q1: Answer mentions fees"
    )
    print(f"  Q1: 'MBA fees' → {len(answer1)} chars")
    
    # Q2: What about placements? (follow-up - should infer MBA context)
    time.sleep(0.5)
    data2, _ = query_api("What about placements?", session)
    answer2 = extract_answer(data2)
    
    result.check(
        not data2.get("fallback", False) and len(answer2) > 50,
        "Q2: 'What about placements?' returns RAG answer"
    )
    result.check(
        any(w in answer2.lower() for w in ["placement", "salary", "hiring", "recruiter"]),
        "Q2: Answer discusses placements"
    )
    print(f"  Q2: 'What about placements?' → {len(answer2)} chars")
    
    # Q3: And facilities? (another follow-up)
    time.sleep(0.5)
    data3, _ = query_api("And facilities?", session)
    answer3 = extract_answer(data3)
    
    result.check(
        not data3.get("fallback", False) and len(answer3) > 30,
        "Q3: 'And facilities?' returns answer"
    )
    # Check if it's about campus facilities (not random)
    has_facility_content = any(w in answer3.lower() for w in 
        ["facility", "facilities", "campus", "hostel", "lab", "library", "infrastructure"])
    result.check(
        has_facility_content,
        "Q3: Answer discusses facilities"
    )
    print(f"  Q3: 'And facilities?' → {len(answer3)} chars")
    
    return result.print_summary()

def run_noise_test():
    """TEST 4: Noise/Garbage - No 'apply now', 'click here', forms, links?"""
    result = ValidationResult("4️⃣  NOISE/GARBAGE FILTERING TEST")
    
    junk_phrases = [
        "apply now", "click here", "enquire", "http", "www",
        "select state", "fill the form", "submit", "send"
    ]
    
    test_queries = [
        "campus",
        "placements",
        "hostel",
        "facilities",
    ]
    
    for query in test_queries:
        data, _ = query_api(query)
        answer = extract_answer(data)
        
        if "error" in data or not answer:
            result.check(False, f"'{query}' - no answer")
            continue
        
        answer_lower = answer.lower()
        found_junk = []
        for phrase in junk_phrases:
            if phrase in answer_lower:
                found_junk.append(phrase)
        
        result.check(
            len(found_junk) == 0,
            f"'{query}' - no junk phrases ({', '.join(found_junk) if found_junk else 'clean'})"
        )
        
        # Check no raw URLs
        result.check(
            not any(url in answer for url in ["http://", "https://", "www."]),
            f"'{query}' - no raw URLs"
        )
        
        print(f"  Query: '{query}' | Junk found: {found_junk if found_junk else 'none'}")
    
    return result.print_summary()

def run_stress_test():
    """TEST 5: BONUS - Fee Intent Robustness"""
    result = ValidationResult("5️⃣  BONUS STRESS TEST (Fee Intent Variations)")
    
    fee_variations = [
        "fees",
        "course fee",
        "how much does it cost",
        "price of mba",
        "MBA cost",
        "tuition fees",
    ]
    
    for query in fee_variations:
        data, _ = query_api(query)
        answer = extract_answer(data)
        
        if "error" in data:
            result.check(False, f"'{query}' - API error")
            continue
        
        is_fallback = data.get("fallback", False)
        has_content = len(answer) > 30
        
        # Should either hit structured path or have meaningful RAG
        result.check(
            not is_fallback,
            f"'{query}' - not fallback"
        )
        
        result.check(
            has_content,
            f"'{query}' - has content ({len(answer)} chars)"
        )
        
        # Should mention fees/cost/price
        mentions_cost = any(w in answer.lower() for w in ["fee", "cost", "price", "₹", "rupee", "annual"])
        result.check(
            mentions_cost,
            f"'{query}' - discusses cost"
        )
        
        print(f"  Query: '{query}' | Mode: {data.get('mode')} | Chars: {len(answer)}")
    
    return result.print_summary()

def main():
    print("\n" + "="*70)
    print("🚀 PRODUCTION VALIDATION TEST SUITE")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print(f"Session ID: {SESSION_ID}")
    print("="*70)
    
    # Wait for server
    print("\n⏳ Waiting for server...")
    time.sleep(2)
    
    results = []
    
    # Run all tests
    results.append(("Relevance", run_relevance_test()))
    time.sleep(0.5)
    
    results.append(("Length", run_length_test()))
    time.sleep(0.5)
    
    results.append(("Context", run_context_test()))
    time.sleep(0.5)
    
    results.append(("Noise", run_noise_test()))
    time.sleep(0.5)
    
    results.append(("Stress", run_stress_test()))
    
    # Final summary
    print("\n" + "="*70)
    print("📊 FINAL TEST SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print("="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED - PRODUCTION READY")
    else:
        print("⚠️  SOME TESTS FAILED - NEEDS REVIEW")
    print("="*70)

if __name__ == "__main__":
    main()
