#!/usr/bin/env python3
"""
Automated Test Harness — Test all 30 queries against API
Exports results to JSON and CSV for analysis
"""

import requests
import json
import csv
import time
from datetime import datetime
from typing import List, Dict, Any

# Fixed test queries (from Phase 5 validation)
TEST_QUERIES = [
    "What programs does AIMS offer?",
    "What is the admission process?",
    "What is the MBA program fee?",
    "What are the entrance exam requirements?",
    "What is the placement rate?",
    "Does AIMS have hostel facilities?",
    "How much is the hostel fee?",
    "Does AIMS have a gym?",
    "What are the scholarship opportunities?",
    "What is the duration of the program?",
    "Are there any entrance exams?",
    "What is the average package of graduates?",
    "Does AIMS provide campus placements?",
    "What are the campus facilities?",
    "Can I defer my admission?",
    "What is the cutoff score?",
    "Are there any merit scholarships?",
    "What is the acceptance rate?",
    "Do you offer online programs?",
    "What is the student-to-faculty ratio?",
    "Are there internship opportunities?",
    "What are the eligibility criteria?",
    "Is there a entrance exam fee?",
    "Can I apply without an entrance exam?",
    "What is the refund policy?",
    "Are registrations open for winter intake?",
    "What are the programming languages taught?",
    "Does AIMS have a library?",
    "What is the average salary package?",
    "Are there any financial aid options?",
]

class TestHarness:
    """Automated test runner for chatbot API"""
    
    def __init__(self, api_url: str = "http://localhost:8000/api/v1/chat"):
        self.api_url = api_url
        self.results: List[Dict[str, Any]] = []
        self.start_time = None
        
    def run_tests(self) -> Dict[str, Any]:
        """Run all tests and collect results"""
        print(f"{'='*80}")
        print(f"🧪 AUTOMATED TEST HARNESS")
        print(f"{'='*80}")
        print(f"API URL: {self.api_url}")
        print(f"Test queries: {len(TEST_QUERIES)}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        self.start_time = time.time()
        
        for i, query in enumerate(TEST_QUERIES, 1):
            self._test_query(query, i)
        
        elapsed = time.time() - self.start_time
        return self._generate_report(elapsed)
    
    def _test_query(self, query: str, index: int) -> None:
        """Test a single query"""
        try:
            start = time.time()
            
            response = requests.post(
                self.api_url,
                json={"query": query},
                timeout=10
            )
            
            elapsed = time.time() - start
            
            if response.status_code != 200:
                result = {
                    "index": index,
                    "query": query,
                    "status": "error",
                    "error": f"HTTP {response.status_code}",
                    "answer": None,
                    "confidence": 0.0,
                    "fallback": True,
                    "response_time_ms": elapsed * 1000
                }
            else:
                data = response.json()
                result = {
                    "index": index,
                    "query": query,
                    "status": "ok",
                    "answer": data.get("answer"),
                    "confidence": data.get("confidence", 0.0),
                    "fallback": data.get("fallback", False),
                    "response_time_ms": elapsed * 1000,
                    "sources_count": len(data.get("sources", [])),
                }
            
            self.results.append(result)
            
            # Print progress
            status_char = "✅" if (not result.get("fallback") and result.get("status") == "ok") else "❌"
            print(f"[{index:2d}] {status_char} {query[:50]:50s} | "
                  f"confidence: {result.get('confidence', 0):.2f} | "
                  f"time: {result.get('response_time_ms', 0):.1f}ms")
        
        except requests.exceptions.ConnectionError:
            print(f"[{index:2d}] ❌ {query[:50]:50s} | ERROR: API not responding")
            self.results.append({
                "index": index,
                "query": query,
                "status": "connection_error",
                "error": "API not responding",
                "answer": None,
                "confidence": 0.0,
                "fallback": True,
                "response_time_ms": 0
            })
        
        except Exception as e:
            print(f"[{index:2d}] ❌ {query[:50]:50s} | ERROR: {str(e)[:30]}")
            self.results.append({
                "index": index,
                "query": query,
                "status": "error",
                "error": str(e),
                "answer": None,
                "confidence": 0.0,
                "fallback": True,
                "response_time_ms": 0
            })
    
    def _generate_report(self, elapsed: float) -> Dict[str, Any]:
        """Generate summary statistics"""
        total = len(self.results)
        answered = sum(1 for r in self.results if not r.get("fallback") and r.get("status") == "ok")
        fallback = total - answered
        
        valid_results = [r for r in self.results if r.get("status") == "ok"]
        avg_confidence = sum(r.get("confidence", 0) for r in valid_results) / len(valid_results) if valid_results else 0
        avg_time = sum(r.get("response_time_ms", 0) for r in self.results) / total if total > 0 else 0
        
        # Categorize failures
        failure_categories = self._categorize_failures()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_queries": total,
                "answered": answered,
                "answered_rate": f"{(answered/total)*100:.1f}%" if total > 0 else "0%",
                "fallback": fallback,
                "fallback_rate": f"{(fallback/total)*100:.1f}%" if total > 0 else "0%",
                "avg_confidence": f"{avg_confidence:.3f}",
                "avg_response_time_ms": f"{avg_time:.1f}",
                "total_runtime_seconds": f"{elapsed:.1f}"
            },
            "failure_categories": failure_categories,
            "results": self.results
        }
        
        return report
    
    def _categorize_failures(self) -> Dict[str, List[str]]:
        """Categorize failed queries by topic"""
        categories = {
            "fees": [],
            "placements": [],
            "facilities": [],
            "admissions": [],
            "scholarships": [],
            "other": []
        }
        
        keywords = {
            "fees": ["fee", "cost", "price", "payment", "charge", "expense"],
            "placements": ["placement", "salary", "package", "job", "recruit", "company"],
            "facilities": ["hostel", "gym", "library", "campus", "lab", "facility"],
            "admissions": ["admission", "apply", "enroll", "entrance", "cutoff", "requirement"],
            "scholarships": ["scholarship", "financial", "grant", "aid", "waiver"]
        }
        
        for result in self.results:
            if result.get("fallback") and result.get("status") == "ok":
                query = result.get("query", "").lower()
                categorized = False
                
                for category, words in keywords.items():
                    if any(word in query for word in words):
                        categories[category].append(result.get("query"))
                        categorized = True
                        break
                
                if not categorized:
                    categories["other"].append(result.get("query"))
        
        # Return only non-empty categories
        return {k: v for k, v in categories.items() if v}
    
    def save_json(self, filename: str = "/tmp/test_harness_results.json") -> str:
        """Save results to JSON"""
        if not self.results:
            return "No results to save"
        
        # Build report
        report = self._generate_report(time.time() - self.start_time)
        
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        
        return filename
    
    def save_csv(self, filename: str = "/tmp/test_harness_results.csv") -> str:
        """Save results to CSV"""
        if not self.results:
            return "No results to save"
        
        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "index", "query", "status", "answer", "confidence", "fallback", "response_time_ms"
            ])
            writer.writeheader()
            
            for result in self.results:
                # Truncate answer for CSV readability
                answer = result.get("answer", "")
                if answer and len(answer) > 100:
                    answer = answer[:97] + "..."
                
                writer.writerow({
                    "index": result.get("index"),
                    "query": result.get("query"),
                    "status": result.get("status"),
                    "answer": answer,
                    "confidence": f"{result.get('confidence', 0):.3f}",
                    "fallback": result.get("fallback"),
                    "response_time_ms": f"{result.get('response_time_ms', 0):.1f}"
                })
        
        return filename
    
    def print_summary(self, report: Dict) -> None:
        """Print formatted summary"""
        summary = report.get("summary", {})
        
        print(f"\n{'='*80}")
        print(f"📊 TEST RESULTS SUMMARY")
        print(f"{'='*80}\n")
        
        print(f"Total Queries:       {summary.get('total_queries')}")
        print(f"Answered:            {summary.get('answered')} ({summary.get('answered_rate')})")
        print(f"Fallback:            {summary.get('fallback')} ({summary.get('fallback_rate')})")
        print(f"Avg Confidence:      {summary.get('avg_confidence')}")
        print(f"Avg Response Time:   {summary.get('avg_response_time_ms')}ms")
        print(f"Total Runtime:       {summary.get('total_runtime_seconds')}s")
        
        # Failure categories
        failures = report.get("failure_categories", {})
        if failures:
            print(f"\n{'='*80}")
            print(f"❌ FAILURE BREAKDOWN (by category)")
            print(f"{'='*80}\n")
            
            for category, queries in sorted(failures.items(), key=lambda x: len(x[1]), reverse=True):
                print(f"{category.upper():15s} ({len(queries)} failures)")
                for q in queries[:3]:  # Show first 3
                    print(f"  • {q}")
                if len(queries) > 3:
                    print(f"  ... and {len(queries)-3} more")
                print()
        
        print(f"{'='*80}\n")


def main():
    """Main entry point"""
    harness = TestHarness()
    
    try:
        report = harness.run_tests()
        
        # Save results
        json_file = harness.save_json()
        csv_file = harness.save_csv()
        
        # Print summary
        harness.print_summary(report)
        
        print(f"📄 Results saved:")
        print(f"  JSON: {json_file}")
        print(f"  CSV:  {csv_file}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")


if __name__ == "__main__":
    main()
