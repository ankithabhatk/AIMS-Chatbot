#!/usr/bin/env python3
"""
Fast API Test - Chatbot Verification (No Browser Installation)
Tests the chatbot by making direct API calls only
"""

import subprocess
import time
import json
import uuid
import requests
import sys
from typing import Optional
from datetime import datetime


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


API_BASE_URL = "http://localhost:8000"
HEALTH_CHECK_URL = f"{API_BASE_URL}/api/v1/health"
CHAT_ENDPOINT = f"{API_BASE_URL}/api/v1/chat"
STATS_ENDPOINT = f"{API_BASE_URL}/api/v1/stats"

# Real student questions
TEST_QUERIES = [
    "What programs does AIMS offer?",
    "What is the fee structure for MBA?",
    "Does AIMS have placement assistance?",
    "What is the admission process?",
    "Does AIMS have campus facilities like hostel or gym?",
]


def check_api_health() -> bool:
    """Check if API is running and healthy"""
    print(f"\n{Colors.OKCYAN}🔍 Checking API Health...{Colors.ENDC}")
    
    try:
        response = requests.get(HEALTH_CHECK_URL, timeout=5)
        if response.status_code == 200:
            print(f"{Colors.OKGREEN}✅ API is healthy{Colors.ENDC}")
            return True
        else:
            print(
                f"{Colors.FAIL}❌ API returned status {response.status_code}{Colors.ENDC}"
            )
            return False
    except requests.exceptions.ConnectionError:
        print(
            f"{Colors.FAIL}❌ Cannot connect to API at {API_BASE_URL}{Colors.ENDC}"
        )
        print(f"   {Colors.WARNING}Make sure the API is running:{Colors.ENDC}")
        print(f"   uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"{Colors.FAIL}❌ Health check error: {e}{Colors.ENDC}")
        return False


def get_api_stats() -> Optional[dict]:
    """Get API statistics"""
    try:
        response = requests.get(STATS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"{Colors.WARNING}⚠️  Could not fetch stats: {e}{Colors.ENDC}")
    return None


def test_chat_api() -> dict:
    """Test the chat endpoint directly"""
    print(f"\n{Colors.OKCYAN}🧪 Testing Chat API...{Colors.ENDC}")
    
    results = {
        "total_queries": len(TEST_QUERIES),
        "successful_responses": 0,
        "with_high_confidence": 0,
        "average_response_time": 0,
        "queries": [],
    }
    
    response_times = []
    session_id = str(uuid.uuid4())
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n   [{i}/{len(TEST_QUERIES)}] {Colors.BOLD}{query}{Colors.ENDC}")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                CHAT_ENDPOINT,
                json={"query": query, "session_id": session_id},
                timeout=10,
            )
            
            elapsed = time.time() - start_time
            response_times.append(elapsed)
            
            if response.status_code == 200:
                data = response.json()
                
                answer = data.get("answer", "")
                confidence = data.get("confidence", 0)  # Field name is 'confidence', not 'confidence_score'
                sources = data.get("sources", [])
                is_fallback = data.get("fallback", False)  # Use fallback field from API
                
                results["successful_responses"] += 1
                
                # Check if confidence is good
                if confidence >= 0.5:
                    results["with_high_confidence"] += 1
                
                if is_fallback:
                    status = f"{Colors.WARNING}⚠️  FALLBACK{Colors.ENDC}"
                else:
                    status = f"{Colors.OKGREEN}✅ ANSWERED{Colors.ENDC}"
                
                print(f"      {status}")
                print(f"      Confidence: {Colors.BOLD}{confidence:.1%}{Colors.ENDC}")
                print(f"      Response time: {elapsed:.2f}s")
                print(f"      Sources: {len(sources)} document(s)")
                
                results["queries"].append({
                    "query": query,
                    "answered_directly": not is_fallback,
                    "confidence": confidence,
                    "time_seconds": elapsed,
                    "sources_used": len(sources),
                    "answer_preview": answer[:80] + "..." if len(answer) > 80 else answer,
                })
                
            else:
                print(f"      {Colors.FAIL}❌ HTTP {response.status_code}{Colors.ENDC}")
                
        except requests.exceptions.Timeout:
            print(f"      {Colors.FAIL}❌ Timeout (>10s){Colors.ENDC}")
        except Exception as e:
            print(f"      {Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
    
    # Calculate metrics
    if response_times:
        results["average_response_time"] = sum(response_times) / len(response_times)
    
    return results


def print_summary(api_results: dict, stats: Optional[dict] = None):
    """Print formatted results"""
    print(f"\n{Colors.HEADER}{'='*80}")
    print(f"CHATBOT TEST RESULTS")
    print(f"{'='*80}{Colors.ENDC}\n")
    
    # Index Status
    if stats:
        print(f"{Colors.BOLD}📊 Knowledge Base:{Colors.ENDC}")
        index_stats = stats.get('search_stats', {})
        print(f"   Documents: {index_stats.get('total_documents', 'N/A')}")
        print(f"   Model: {index_stats.get('embedding_model', 'N/A')}")
        print()
    
    # Success Rates
    print(f"{Colors.BOLD}📈 Performance:{Colors.ENDC}")
    total = api_results['total_queries']
    successful = api_results['successful_responses']
    high_confidence = api_results['with_high_confidence']
    
    success_rate = (successful / total * 100) if total > 0 else 0
    confidence_rate = (high_confidence / successful * 100) if successful > 0 else 0
    
    print(f"   Response rate: {Colors.OKGREEN}{successful}/{total} ({success_rate:.0f}%){Colors.ENDC}")
    print(f"   High confidence: {Colors.OKGREEN}{high_confidence}/{successful} ({confidence_rate:.0f}%){Colors.ENDC}")
    print(f"   Avg response time: {Colors.BOLD}{api_results['average_response_time']:.2f}s{Colors.ENDC}")
    print()
    
    # Query breakdown
    print(f"{Colors.BOLD}📋 Per-Query Results:{Colors.ENDC}")
    for q in api_results["queries"]:
        icon = "✅" if q["answered_directly"] else "⚠️ "
        print(f"   {icon} {q['query'][:50]}")
        print(f"      └─ Confidence: {q['confidence']:.0%} | {q['time_seconds']:.2f}s")
    
    print()
    
    # Overall assessment
    print(f"{Colors.BOLD}🎯 Assessment:{Colors.ENDC}")
    if success_rate >= 70:
        status = f"{Colors.OKGREEN}✅ EXCELLENT - Production ready{Colors.ENDC}"
    elif success_rate >= 50:
        status = f"{Colors.OKGREEN}✅ GOOD - Ready for data enrichment{Colors.ENDC}"
    elif success_rate >= 32:
        status = f"{Colors.WARNING}⚠️  FAIR - Needs more training data{Colors.ENDC}"
    else:
        status = f"{Colors.FAIL}❌ NEEDS WORK - More data required{Colors.ENDC}"
    
    print(f"   {status}")
    
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}\n")


def main():
    """Main execution"""
    print(f"\n{Colors.HEADER}")
    print("╔" + "="*78 + "╗")
    print("║" + " "*18 + "CHATBOT AGENTIC TEST — FAST MODE" + " "*30 + "║")
    print("╚" + "="*78 + "╝")
    print(f"{Colors.ENDC}\n")
    
    # Step 1: Health check
    if not check_api_health():
        print(f"\n{Colors.FAIL}❌ API not running. Cannot proceed.{Colors.ENDC}")
        sys.exit(1)
    
    # Step 2: Get stats
    stats = get_api_stats()
    
    # Step 3: Test API
    api_results = test_chat_api()
    
    # Step 4: Print results
    print_summary(api_results, stats)
    
    # Step 5: Save results
    results_file = "/tmp/chatbot_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "api_results": api_results,
            "api_stats": stats,
        }, f, indent=2)
    print(f"💾 Results saved: {results_file}\n")


if __name__ == "__main__":
    main()
