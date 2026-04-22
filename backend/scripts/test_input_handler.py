# backend/scripts/test_input_handler.py

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.input_handler import classify_intent

def test_handler():
    test_cases = [
        ("hi", "GREETING"),
        ("Hello!", "GREETING"),
        ("thanks", "EXIT"),
        ("Bye bye.", "EXIT"),
        ("asdfgh", "NONSENSE"),
        ("123456", "NONSENSE"),
        ("a", "NONSENSE"),
        ("What is the MBA fee?", "QUESTION"),
        ("hi, what is the MBA fee?", "QUESTION"),  # Should be question because of strict matching
        ("Tell me about hostel", "QUESTION")
    ]
    
    print("\n" + "="*50)
    print("TESTING INPUT HANDLER")
    print("="*50)
    
    passed = 0
    for text, expected in test_cases:
        result = classify_intent(text)
        status = "✅" if result == expected else "❌"
        if result == expected:
            passed += 1
        print(f"{status} Input: '{text}'")
        print(f"   Expected: {expected}")
        print(f"   Result:   {result}\n")
        
    print("="*50)
    print(f"RESULT: {passed}/{len(test_cases)} PASSED")
    print("="*50 + "\n")

if __name__ == "__main__":
    test_handler()
