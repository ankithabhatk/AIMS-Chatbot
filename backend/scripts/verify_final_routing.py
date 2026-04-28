import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.orchestration.self_healing_engine import execute_orchestration
import logging

# Setup minimal logging
logging.basicConfig(level=logging.INFO)

def test_routing():
    queries = [
        "admission process",
        "placement record",
        "mba fees",
        "courses offered"
    ]
    
    print("\n🚀 Testing Final Routing Hardening...")
    print("-" * 50)
    
    for query in queries:
        result = execute_orchestration(query)
        print(f"QUERY: {query}")
        print(f"INTENT: {result.intent}")
        print(f"MODE: {result.mode}")
        print(f"FALLBACK: {result.fallback}")
        print("-" * 50)
        
        # Validation
        if "admission" in query and (result.mode != "structured" or result.fallback):
            print(f"❌ FAIL: {query} should be structured and NOT fallback")
        if "placement" in query and (result.mode != "rag" or result.fallback):
            print(f"❌ FAIL: {query} should be rag and NOT fallback")
            
    print("✅ Logic Check Complete.")

if __name__ == "__main__":
    test_routing()
