# backend/scripts/test_query_rewriter.py

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.query_rewriter import rewrite_query

def test_rewriter():
    test_cases = [
        # Case 1: Short query
        ("mba fees", "mba fees aims college"),
        
        # Case 2: Context already present (No duplication)
        ("aims mba fees", "aims mba fees"),
        
        # Case 3: Noisy query (Clean + Expand)
        ("mba-fees!!!", "mba fees aims college"),
        
        # Case 4: Long query (No expansion)
        ("what is the mba admission process", "what is the mba admission process"),
        
        # Additional Case: Multiple spaces
        ("mba    fees", "mba fees aims college"),
        
        # Additional Case: Empty/None (Graceful handle)
        ("", ""),
    ]
    
    print("\n" + "="*60)
    print("TESTING QUERY REWRITER")
    print("="*60)
    
    passed = 0
    for i, (text, expected) in enumerate(test_cases, 1):
        result = rewrite_query(text)
        status = "✅" if result == expected else "❌"
        if result == expected:
            passed += 1
        print(f"CASE {i}: {status}")
        print(f"   Input:    '{text}'")
        print(f"   Expected: '{expected}'")
        print(f"   Result:   '{result}'\n")
        
    print("="*60)
    print(f"RESULT: {passed}/{len(test_cases)} PASSED")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_rewriter()
