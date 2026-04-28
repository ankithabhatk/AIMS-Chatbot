"""Test runner for chat API - validates good + bad queries"""

import requests
import json

URL = "http://localhost:8000/api/v1/chat"

# Test queries
TESTS = [
    # Good queries - should work
    ("mba fees", "structured"),
    ("mca admission", "structured"),
    ("placement record", "rag"),
    ("wat corses u hav", "structured"),  # typo
    ("admission procedure for mba", "structured"),
    ("what courses do you offer", "structured"),
    ("mca fees", "structured"),
    ("bba admission", "structured"),
    
    # Edge cases
    ("??", "fallback"),
    ("tell me about iit bombay", "fallback"),  # out of domain
    ("fee", "fallback"),  # too short
    ("hostel facilities", "rag"),
    ("random nonsense text xyz", "fallback"),
    
    # Typo tests
    ("mba admision", "structured"),
    ("mca feees", "structured"),
]

def validate_response(query: str, expected_mode: str, data: dict) -> tuple[bool, str]:
    """Validate response quality"""
    answer = data.get("answer", "")
    mode = data.get("mode", "")
    is_fallback = data.get("fallback", data.get("is_fallback", False))
    
    # Check 1: Empty or weak answer
    if not answer or len(answer.split()) < 3:
        return False, "FAIL: empty/weak answer"
    
    # Check 2: Out of domain leak
    out_of_domain = ["iit", "harvard", "mit", "stanford", "iim"]
    if any(x in answer.lower() for x in out_of_domain):
        return False, "FAIL: out-of-domain leak"

    if mode != expected_mode:
        return False, f"FAIL: expected {expected_mode}, got {mode}"

    if expected_mode == "fallback" and not is_fallback:
        return False, "FAIL: fallback expected but not triggered"
    
    # Check 3: Structured should have high confidence
    if "fees" in query.lower() or "admission" in query.lower() or "course" in query.lower():
        if is_fallback and mode != "structured":
            return False, f"FAIL: structured query got fallback (mode={mode})"
    
    return True, "PASS"


def run_tests():
    """Run all tests"""
    print("=" * 60)
    print("CHAT API TEST RUNNER")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for query, expected_mode in TESTS:
        try:
            payload = {
                "query": query,
                "session_id": "test-session-001",
                "user_context": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "course": "MBA"
                }
            }
            
            resp = requests.post(URL, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            is_valid, msg = validate_response(query, expected_mode, data)
            actual_mode = data.get("mode", "unknown")
            fallback = data.get("fallback", data.get("is_fallback", False))
            confidence = data.get("confidence", data.get("confidence_score", 0))
            
            status = "✅" if is_valid else "❌"
            print(f"{status} {msg} | {query} | {actual_mode} | fallback={fallback}")
            print(f"   Expected: {expected_mode}")
            print(f"   Confidence: {confidence:.2f}")
            print()
            
            if is_valid:
                passed += 1
            else:
                failed += 1
                
        except requests.exceptions.Timeout:
            print(f"❌ TIMEOUT | {query}")
            failed += 1
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP {resp.status_code} | {query}")
            print(f"   Raw: {resp.text[:300]}")
            print()
            failed += 1
        except Exception as e:
            print(f"❌ ERROR | {query} | {e}")
            failed += 1
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    run_tests()
