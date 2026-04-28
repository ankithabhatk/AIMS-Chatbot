"""
Browser Test: Verify Deployment Readiness

Tests:
1. System responds to queries
2. Logging captures all fields
3. API endpoints work
4. Analysis detects patterns

Run: python test_deployment_ready.py
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Test queries that should trigger different patterns
TEST_QUERIES = [
    {
        "query": "What are BCA fees?",
        "expected_intent": "fees",
        "description": "Standard fees query"
    },
    {
        "query": "cost of bca",
        "expected_pattern": "language_gap",
        "description": "Language gap: 'cost' vs 'fees'"
    },
    {
        "query": "fees and hostel",
        "expected_intents": ["fees", "hostel"],
        "description": "Multi-intent query"
    },
    {
        "query": "xyz abc def",
        "expected_pattern": "fallback",
        "description": "Gibberish - should fallback"
    },
    {
        "query": "placement salary package",
        "expected_intent": "placement",
        "description": "Placement query"
    }
]

def test_chat_endpoint():
    """Test that chat endpoint works and logs are created"""
    print("\n" + "="*60)
    print("TEST 1: Chat Endpoint & Logging")
    print("="*60)
    
    for i, test in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}] Testing: {test['description']}")
        print(f"    Query: {test['query']}")
        
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                json={
                    "query": test["query"],
                    "session_id": f"test_session_{i}"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"    ✅ Response received")
                print(f"    Intent: {data.get('intent', 'N/A')}")
                print(f"    Confidence: {data.get('confidence', 'N/A')}")
                print(f"    Mode: {data.get('mode', 'N/A')}")
            else:
                print(f"    ❌ Error: {response.status_code}")
                print(f"    {response.text}")
        
        except Exception as e:
            print(f"    ❌ Exception: {e}")
        
        time.sleep(0.5)  # Small delay between requests

def test_logs_endpoint():
    """Test that logs API endpoint works"""
    print("\n" + "="*60)
    print("TEST 2: Logs API Endpoint")
    print("="*60)
    
    try:
        response = requests.get(
            f"{API_BASE}/deployment/logs?limit=10",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print(f"✅ Logs endpoint working")
            print(f"   Logs collected: {count}")
            
            if count > 0:
                log = data['logs'][0]
                print(f"\n   Sample log entry:")
                print(f"   - raw_query: {log.get('raw_query')}")
                print(f"   - processed_query: {log.get('processed_query')}")
                print(f"   - matched_keywords: {log.get('matched_keywords')}")
                print(f"   - detected_intents: {log.get('detected_intents')}")
                print(f"   - response_type: {log.get('response_type')}")
                print(f"   - fallback: {log.get('fallback')}")
                print(f"   - fallback_reason: {log.get('fallback_reason')}")
        else:
            print(f"❌ Error: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_analysis_endpoint():
    """Test that analysis API endpoint works"""
    print("\n" + "="*60)
    print("TEST 3: Analysis API Endpoint")
    print("="*60)
    
    try:
        response = requests.get(
            f"{API_BASE}/deployment/analysis",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            analysis = data.get('analysis', {})
            
            print(f"✅ Analysis endpoint working")
            print(f"\n   Metrics:")
            print(f"   - Total queries: {analysis.get('total_queries', 0)}")
            print(f"   - Fallback rate: {analysis.get('fallback_rate', 'N/A')}")
            print(f"   - Top intents: {analysis.get('top_intents', [])[:3]}")
            print(f"   - Language gaps: {analysis.get('language_gaps_count', 0)}")
            print(f"   - Routing errors: {analysis.get('routing_errors_count', 0)}")
            print(f"   - Low confidence intents: {analysis.get('low_confidence_intents_count', 0)}")
            
            if analysis.get('language_gaps_sample'):
                print(f"\n   Language gap examples:")
                for gap in analysis['language_gaps_sample'][:2]:
                    print(f"   - '{gap.get('raw_query')}' → no intent")
        else:
            print(f"❌ Error: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_status_endpoint():
    """Test that status endpoint works"""
    print("\n" + "="*60)
    print("TEST 4: Status API Endpoint")
    print("="*60)
    
    try:
        response = requests.get(
            f"{API_BASE}/deployment/status",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status endpoint working")
            print(f"   Status: {data.get('status')}")
            print(f"   Logs collected: {data.get('logs_collected', 0)}")
            print(f"   Fallback rate: {data.get('fallback_rate', 'N/A')}")
            print(f"   Log file: {data.get('log_file', 'N/A')}")
        else:
            print(f"❌ Error: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_export_endpoint():
    """Test that export endpoint works"""
    print("\n" + "="*60)
    print("TEST 5: Export API Endpoint")
    print("="*60)
    
    try:
        response = requests.get(
            f"{API_BASE}/deployment/export",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                csv_file = data.get('csv_file')
                print(f"✅ Export endpoint working")
                print(f"   CSV file: {csv_file}")
                
                # Check if file exists
                if Path(csv_file).exists():
                    print(f"   ✅ CSV file created successfully")
                    # Count lines
                    with open(csv_file) as f:
                        lines = len(f.readlines())
                    print(f"   Rows in CSV: {lines}")
            else:
                print(f"⚠️  {data.get('message')}")
        else:
            print(f"❌ Error: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    print("\n" + "🚀 "*30)
    print("DEPLOYMENT READINESS TEST")
    print("🚀 "*30)
    
    print(f"\nTesting against: {BASE_URL}")
    print("Make sure backend is running: python -m uvicorn app.main:app --reload")
    
    # Run tests
    test_chat_endpoint()
    time.sleep(1)
    test_logs_endpoint()
    test_analysis_endpoint()
    test_status_endpoint()
    test_export_endpoint()
    
    print("\n" + "="*60)
    print("DEPLOYMENT READINESS SUMMARY")
    print("="*60)
    print("""
✅ If all tests passed:
   - System is logging correctly
   - API endpoints are working
   - Observability layer is active
   - Ready for deployment

🚀 Next steps:
   1. Deploy to 10-20 real users
   2. Collect 50-100 queries
   3. Export logs and analyze
   4. Come back with findings

📊 What to look for in logs:
   - language_gaps: queries with no matched keywords
   - low_confidence_intents: intents scoring < 0.65
   - routing_errors: correct intent but wrong response_type
   - fallback_reasons: why system fell back
    """)

if __name__ == "__main__":
    main()
