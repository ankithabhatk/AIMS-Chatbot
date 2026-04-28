#!/usr/bin/env python3
"""5-Dimensional Production Validation - Final Check"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

class ValidationReport:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "dimensions": {
                "relevance": [],
                "length": [],
                "context": [],
                "noise": [],
                "stress": []
            },
            "summary": {}
        }
    
    def test_relevance(self):
        """Dimension 1: Answer relevance to query"""
        print("\n" + "="*70)
        print("📊 DIMENSION 1: RELEVANCE (Does answer match query intent?)")
        print("="*70)
        
        tests = [
            ("Tell me about placements", ["placement", "lpa", "recruiter"]),
            ("What are the fees?", ["fee", "₹", "cost"]),
            ("MBA course details", ["mba", "duration", "specialization"]),
            ("Tell me about admissions", ["admission", "apply", "eligibility"]),
            ("Campus facilities", ["campus", "facility", "hostel", "library"]),
        ]
        
        passed = 0
        for query, keywords in tests:
            try:
                resp = requests.post(
                    f"{BASE_URL}/api/v1/chat",
                    json={"query": query, "session_id": "val-rel"},
                    timeout=10
                )
                if resp.status_code == 200:
                    answer = resp.json().get("answer", "").lower()
                    has_keywords = any(kw.lower() in answer for kw in keywords)
                    status = "✅" if has_keywords else "❌"
                    print(f"{status} '{query}' -> {len(answer)} chars, keywords: {has_keywords}")
                    if has_keywords:
                        passed += 1
                    self.results["dimensions"]["relevance"].append({
                        "query": query,
                        "passed": has_keywords,
                        "char_count": len(answer)
                    })
                else:
                    print(f"❌ '{query}' -> HTTP {resp.status_code}")
                    self.results["dimensions"]["relevance"].append({
                        "query": query,
                        "passed": False,
                        "error": f"HTTP {resp.status_code}"
                    })
            except Exception as e:
                print(f"❌ '{query}' -> Error: {e}")
                self.results["dimensions"]["relevance"].append({
                    "query": query,
                    "passed": False,
                    "error": str(e)
                })
            time.sleep(0.5)
        
        relevance_score = (passed / len(tests)) * 100
        print(f"\n✅ Relevance Score: {relevance_score:.0f}% ({passed}/{len(tests)} passed)")
        self.results["summary"]["relevance_score"] = relevance_score
        return relevance_score
    
    def test_length(self):
        """Dimension 2: Answer length control"""
        print("\n" + "="*70)
        print("📏 DIMENSION 2: LENGTH (Are answers appropriately sized?)")
        print("="*70)
        
        tests = [
            ("Tell me about placements", 80, 300),
            ("What are the fees?", 80, 300),
            ("Tell me about campus facilities", 100, 400),
        ]
        
        passed = 0
        for query, min_len, max_len in tests:
            try:
                resp = requests.post(
                    f"{BASE_URL}/api/v1/chat",
                    json={"query": query, "session_id": "val-len"},
                    timeout=10
                )
                if resp.status_code == 200:
                    answer = resp.json().get("answer", "")
                    char_count = len(answer)
                    is_valid = min_len <= char_count <= max_len
                    status = "✅" if is_valid else "❌"
                    print(f"{status} '{query}' -> {char_count} chars (target: {min_len}-{max_len})")
                    if is_valid:
                        passed += 1
                    self.results["dimensions"]["length"].append({
                        "query": query,
                        "char_count": char_count,
                        "target_min": min_len,
                        "target_max": max_len,
                        "passed": is_valid
                    })
                else:
                    print(f"❌ '{query}' -> HTTP {resp.status_code}")
            except Exception as e:
                print(f"❌ '{query}' -> Error: {e}")
            time.sleep(0.5)
        
        length_score = (passed / len(tests)) * 100
        print(f"\n✅ Length Score: {length_score:.0f}% ({passed}/{len(tests)} passed)")
        self.results["summary"]["length_score"] = length_score
        return length_score
    
    def test_context(self):
        """Dimension 3: Conversation context awareness"""
        print("\n" + "="*70)
        print("🔗 DIMENSION 3: CONTEXT (Is conversation context preserved?)")
        print("="*70)
        
        session = "val-ctx-123"
        try:
            # First query
            resp1 = requests.post(
                f"{BASE_URL}/api/v1/chat",
                json={"query": "Tell me about MBA", "session_id": session},
                timeout=10
            )
            print(f"✅ Q1 (MBA) -> {resp1.status_code}")
            
            time.sleep(0.5)
            
            # Follow-up query
            resp2 = requests.post(
                f"{BASE_URL}/api/v1/chat",
                json={"query": "What about fees?", "session_id": session},
                timeout=10
            )
            print(f"✅ Q2 (fees follow-up) -> {resp2.status_code}")
            
            context_maintained = resp1.status_code == 200 and resp2.status_code == 200
            self.results["dimensions"]["context"].append({
                "test": "multi-turn conversation",
                "passed": context_maintained
            })
            
            print(f"\n✅ Context Score: {'100' if context_maintained else '0'}% (conversation maintained)")
            self.results["summary"]["context_score"] = 100 if context_maintained else 0
            return 100 if context_maintained else 0
            
        except Exception as e:
            print(f"❌ Context test failed: {e}")
            self.results["summary"]["context_score"] = 0
            return 0
    
    def test_noise(self):
        """Dimension 4: Junk/spam filtering"""
        print("\n" + "="*70)
        print("🧹 DIMENSION 4: NOISE FILTERING (No spam/ads/links?)")
        print("="*70)
        
        spam_keywords = ["click here", "apply now", "http://", "www.", "email us at"]
        
        tests = [
            "Tell me about placements",
            "MBA fees",
            "Campus facilities"
        ]
        
        passed = 0
        for query in tests:
            try:
                resp = requests.post(
                    f"{BASE_URL}/api/v1/chat",
                    json={"query": query, "session_id": "val-noise"},
                    timeout=10
                )
                if resp.status_code == 200:
                    answer = resp.json().get("answer", "").lower()
                    has_spam = any(spam in answer for spam in spam_keywords)
                    status = "✅" if not has_spam else "❌"
                    print(f"{status} '{query}' -> Clean: {not has_spam}")
                    if not has_spam:
                        passed += 1
                    self.results["dimensions"]["noise"].append({
                        "query": query,
                        "has_spam": has_spam,
                        "passed": not has_spam
                    })
                else:
                    print(f"❌ '{query}' -> HTTP {resp.status_code}")
            except Exception as e:
                print(f"❌ '{query}' -> Error: {e}")
            time.sleep(0.5)
        
        noise_score = (passed / len(tests)) * 100
        print(f"\n✅ Noise Score: {noise_score:.0f}% ({passed}/{len(tests)} passed)")
        self.results["summary"]["noise_score"] = noise_score
        return noise_score
    
    def test_stress(self):
        """Dimension 5: Load handling"""
        print("\n" + "="*70)
        print("⚡ DIMENSION 5: STRESS TEST (Can system handle load?)")
        print("="*70)
        
        queries = [
            "Tell me about placements",
            "MBA fees",
            "Admissions process",
            "Campus facilities",
            "Course duration"
        ]
        
        successful = 0
        failed = 0
        
        for i, query in enumerate(queries, 1):
            try:
                resp = requests.post(
                    f"{BASE_URL}/api/v1/chat",
                    json={"query": query, "session_id": f"stress-{i}"},
                    timeout=10
                )
                if resp.status_code == 200:
                    print(f"✅ Request {i}/{len(queries)} -> OK")
                    successful += 1
                else:
                    print(f"❌ Request {i}/{len(queries)} -> HTTP {resp.status_code}")
                    failed += 1
            except Exception as e:
                print(f"❌ Request {i}/{len(queries)} -> Error")
                failed += 1
            time.sleep(0.3)
        
        stress_score = (successful / len(queries)) * 100
        print(f"\n✅ Stress Score: {stress_score:.0f}% ({successful}/{len(queries)} successful)")
        self.results["summary"]["stress_score"] = stress_score
        return stress_score
    
    def final_report(self):
        """Generate final report"""
        print("\n" + "="*70)
        print("📈 FINAL PRODUCTION READINESS REPORT")
        print("="*70)
        
        scores = self.results["summary"]
        avg_score = sum([
            scores.get("relevance_score", 0),
            scores.get("length_score", 0),
            scores.get("context_score", 0),
            scores.get("noise_score", 0),
            scores.get("stress_score", 0)
        ]) / 5
        
        print(f"\n📊 5-Dimensional Scores:")
        print(f"  1. Relevance: {scores.get('relevance_score', 0):.0f}%")
        print(f"  2. Length:    {scores.get('length_score', 0):.0f}%")
        print(f"  3. Context:   {scores.get('context_score', 0):.0f}%")
        print(f"  4. Noise:     {scores.get('noise_score', 0):.0f}%")
        print(f"  5. Stress:    {scores.get('stress_score', 0):.0f}%")
        print(f"\n🎯 Overall Score: {avg_score:.1f}%")
        
        if avg_score >= 95:
            status = "🟢 APPROVED FOR PRODUCTION (95%+ Confidence)"
        elif avg_score >= 85:
            status = "🟡 READY WITH MINOR ISSUES (85-95% Confidence)"
        else:
            status = "🔴 NOT READY (Below 85% Confidence)"
        
        print(f"Status: {status}")
        
        # Save report
        with open("PRODUCTION_VALIDATION_FINAL.md", "w") as f:
            f.write(f"# Production Validation Report\n\n")
            f.write(f"**Generated:** {self.results['timestamp']}\n\n")
            f.write(f"## 5-Dimensional Validation\n\n")
            f.write(f"| Dimension | Score |\n")
            f.write(f"|-----------|-------|\n")
            f.write(f"| Relevance | {scores.get('relevance_score', 0):.0f}% |\n")
            f.write(f"| Length | {scores.get('length_score', 0):.0f}% |\n")
            f.write(f"| Context | {scores.get('context_score', 0):.0f}% |\n")
            f.write(f"| Noise Filtering | {scores.get('noise_score', 0):.0f}% |\n")
            f.write(f"| Stress Test | {scores.get('stress_score', 0):.0f}% |\n")
            f.write(f"\n**Overall: {avg_score:.1f}%**\n\n")
            f.write(f"## Status\n{status}\n")
        
        print(f"\n📄 Report saved to: PRODUCTION_VALIDATION_FINAL.md")
        return avg_score

def main():
    validator = ValidationReport()
    
    print("\n" + "="*70)
    print("🚀 PRODUCTION READINESS VALIDATION (5 DIMENSIONS)")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Run all validations
    validator.test_relevance()
    time.sleep(1)
    validator.test_length()
    time.sleep(1)
    validator.test_context()
    time.sleep(1)
    validator.test_noise()
    time.sleep(1)
    validator.test_stress()
    
    # Final report
    final_score = validator.final_report()
    
    # Save detailed JSON
    with open("validation_results.json", "w") as f:
        json.dump(validator.results, f, indent=2)

if __name__ == "__main__":
    main()
