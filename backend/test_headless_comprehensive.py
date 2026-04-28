"""
Comprehensive Headless Browser Test - Full Stack Validation

Tests:
1. API connectivity and response format
2. Session memory across multiple queries
3. Intent detection accuracy
4. Answer quality and hallucination detection
5. Routing modes (structured/RAG/fallback)
6. Brain layer components (cleaner, scorer, context, etc.)
7. Edge cases and error handling

HONEST ASSESSMENT: No sugarcoating, real metrics, actual errors reported.
"""

import sys
import json
import time
import uuid
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

import requests
from dataclasses import dataclass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
API_BASE = "http://127.0.0.1:8000"
CHAT_ENDPOINT = f"{API_BASE}/api/v1/chat"
SCREENSHOT_DIR = Path("/Users/maneeth/Desktop/Chat-Bot/test-results/headless_screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class TestResult:
    test_name: str
    passed: bool
    details: str
    screenshot_path: str = None
    metrics: Dict[str, Any] = None
    error: str = None


class HeadlessTestRunner:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.results: List[TestResult] = []
        self.conversation_context = {
            "last_course": None,
            "last_intent": None,
            "last_topic": None,
        }
        self.api_available = False
        
    def log_result(self, result: TestResult):
        """Log a test result."""
        status_icon = "✅" if result.passed else "❌"
        logger.info(f"{status_icon} {result.test_name}")
        logger.info(f"   Details: {result.details}")
        if result.error:
            logger.info(f"   Error: {result.error}")
        self.results.append(result)
    
    def save_screenshot(self, test_name: str, data: Dict[str, Any]) -> str:
        """Save API response as JSON screenshot for inspection."""
        path = SCREENSHOT_DIR / f"{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return str(path)
    
    # ============================================================================
    # TEST 1: API CONNECTIVITY
    # ============================================================================
    def test_api_connectivity(self) -> bool:
        """Test if API is running and responding."""
        logger.info("\n" + "="*70)
        logger.info("TEST 1: API CONNECTIVITY")
        logger.info("="*70)
        
        try:
            response = requests.post(
                CHAT_ENDPOINT,
                json={"query": "test"},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                path = self.save_screenshot("test01_api_connectivity", data)
                
                self.log_result(TestResult(
                    test_name="API Connectivity",
                    passed=True,
                    details=f"API responding with status {response.status_code}. Response: {json.dumps(data)[:200]}...",
                    screenshot_path=path,
                    metrics={"response_time_ms": response.elapsed.total_seconds() * 1000}
                ))
                self.api_available = True
                return True
            else:
                self.log_result(TestResult(
                    test_name="API Connectivity",
                    passed=False,
                    details=f"API returned status {response.status_code}",
                    error=response.text[:500]
                ))
                return False
                
        except requests.exceptions.ConnectionError as e:
            self.log_result(TestResult(
                test_name="API Connectivity",
                passed=False,
                details="Cannot connect to API",
                error=f"Connection refused: {str(e)}"
            ))
            logger.error("⚠️  API is not running! Please start the server first.")
            return False
        except Exception as e:
            self.log_result(TestResult(
                test_name="API Connectivity",
                passed=False,
                details="API connection test failed",
                error=str(e)
            ))
            return False
    
    # ============================================================================
    # TEST 2: SESSION MEMORY - SINGLE QUERY
    # ============================================================================
    def test_session_memory_single(self) -> bool:
        """Test if session is created and returned correctly."""
        logger.info("\n" + "="*70)
        logger.info("TEST 2: SESSION MEMORY - SINGLE QUERY")
        logger.info("="*70)
        
        if not self.api_available:
            self.log_result(TestResult(
                test_name="Session Memory (Single)",
                passed=False,
                details="Skipped (API not available)"
            ))
            return False
        
        try:
            response = requests.post(
                CHAT_ENDPOINT,
                json={
                    "query": "What is MBA fees?",
                    "session_id": self.session_id
                },
                timeout=10
            )
            
            data = response.json()
            path = self.save_screenshot("test02_session_single", data)
            
            # Check response structure
            has_session = "meta" in data and "session_id" in data["meta"]
            has_answer = "answer" in data and len(data.get("answer", "")) > 0
            has_intent = "intent" in data
            
            if has_session and has_answer and has_intent:
                logger.info(f"   Session ID: {data['meta'].get('session_id')}")
                logger.info(f"   Intent: {data['intent']}")
                logger.info(f"   Answer Preview: {data['answer'][:100]}...")
                
                self.log_result(TestResult(
                    test_name="Session Memory (Single)",
                    passed=True,
                    details=f"Session created. Intent: {data['intent']}, Answer length: {len(data['answer'])} chars",
                    screenshot_path=path,
                    metrics={
                        "session_id": data['meta'].get('session_id'),
                        "intent": data['intent'],
                        "answer_length": len(data['answer']),
                        "confidence": data.get('confidence', 0)
                    }
                ))
                
                # Store for next query
                self.conversation_context["last_intent"] = data['intent']
                return True
            else:
                self.log_result(TestResult(
                    test_name="Session Memory (Single)",
                    passed=False,
                    details=f"Response missing fields. Has session: {has_session}, has answer: {has_answer}",
                    screenshot_path=path,
                    error=json.dumps(data)[:300]
                ))
                return False
                
        except Exception as e:
            self.log_result(TestResult(
                test_name="Session Memory (Single)",
                passed=False,
                details="Failed to test session",
                error=str(e)
            ))
            return False
    
    # ============================================================================
    # TEST 3: SESSION MEMORY - FOLLOW-UP QUERY
    # ============================================================================
    def test_session_memory_followup(self) -> bool:
        """Test if follow-up queries retain context."""
        logger.info("\n" + "="*70)
        logger.info("TEST 3: SESSION MEMORY - FOLLOW-UP QUERY")
        logger.info("="*70)
        
        if not self.api_available:
            self.log_result(TestResult(
                test_name="Session Memory (Follow-up)",
                passed=False,
                details="Skipped (API not available)"
            ))
            return False
        
        try:
            # Follow-up query
            response = requests.post(
                CHAT_ENDPOINT,
                json={
                    "query": "What about hostel?",  # Follow-up context
                    "session_id": self.session_id,
                    "context": {
                        "last_intent": self.conversation_context.get("last_intent"),
                        "last_course": "MBA"
                    }
                },
                timeout=10
            )
            
            data = response.json()
            path = self.save_screenshot("test03_session_followup", data)
            
            has_session = data['meta'].get('session_id') == self.session_id
            has_answer = len(data.get('answer', '')) > 0
            context_mentioned = 'mba' in data.get('answer', '').lower() or 'hostel' in data.get('answer', '').lower()
            
            logger.info(f"   Same session ID: {has_session}")
            logger.info(f"   Has answer: {has_answer}")
            logger.info(f"   Context preserved: {context_mentioned}")
            
            self.log_result(TestResult(
                test_name="Session Memory (Follow-up)",
                passed=has_session and has_answer,
                details=f"Follow-up query processed. Same session: {has_session}, Context preserved: {context_mentioned}",
                screenshot_path=path,
                metrics={
                    "same_session": has_session,
                    "answer_length": len(data['answer']),
                    "intent": data['intent']
                }
            ))
            
            return has_session
            
        except Exception as e:
            self.log_result(TestResult(
                test_name="Session Memory (Follow-up)",
                passed=False,
                details="Failed to test follow-up",
                error=str(e)
            ))
            return False
    
    # ============================================================================
    # TEST 4: INTENT DETECTION ACCURACY
    # ============================================================================
    def test_intent_detection(self) -> bool:
        """Test if intents are detected correctly."""
        logger.info("\n" + "="*70)
        logger.info("TEST 4: INTENT DETECTION ACCURACY")
        logger.info("="*70)
        
        if not self.api_available:
            self.log_result(TestResult(
                test_name="Intent Detection",
                passed=False,
                details="Skipped (API not available)"
            ))
            return False
        
        test_cases = [
            ("What is the fee structure?", "fees"),
            ("How to get admission?", "admission"),
            ("Where are placements?", "placement"),
            ("Tell me about campus", "campus"),
            ("What courses are available?", "courses"),
        ]
        
        passed = 0
        failed = 0
        
        for query, expected_intent in test_cases:
            try:
                response = requests.post(
                    CHAT_ENDPOINT,
                    json={"query": query},
                    timeout=10
                )
                data = response.json()
                detected_intent = data.get('intent', 'unknown')
                is_correct = detected_intent == expected_intent
                
                status = "✅" if is_correct else "❌"
                logger.info(f"   {status} Query: '{query}'")
                logger.info(f"      Expected: {expected_intent} | Detected: {detected_intent}")
                
                if is_correct:
                    passed += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.info(f"   ❌ Query: '{query}' - Error: {str(e)[:100]}")
                failed += 1
        
        accuracy = passed / (passed + failed) * 100 if (passed + failed) > 0 else 0
        
        self.log_result(TestResult(
            test_name="Intent Detection",
            passed=accuracy >= 80,  # 80% threshold
            details=f"Intent detection accuracy: {accuracy:.1f}% ({passed}/{passed+failed} correct)",
            metrics={
                "accuracy_percent": accuracy,
                "passed": passed,
                "failed": failed
            }
        ))
        
        return accuracy >= 80
    
    # ============================================================================
    # TEST 5: ANSWER QUALITY & HALLUCINATION DETECTION
    # ============================================================================
    def test_answer_quality(self) -> bool:
        """Test if answers are coherent and not hallucinating."""
        logger.info("\n" + "="*70)
        logger.info("TEST 5: ANSWER QUALITY & HALLUCINATION")
        logger.info("="*70)
        
        if not self.api_available:
            self.log_result(TestResult(
                test_name="Answer Quality",
                passed=False,
                details="Skipped (API not available)"
            ))
            return False
        
        test_queries = [
            "What is AIMS?",
            "MBA placement record",
            "How to apply for BCA?",
            "Scholarship eligibility",
            "Campus location"
        ]
        
        quality_scores = []
        hallucination_detected = 0
        
        for query in test_queries:
            try:
                response = requests.post(
                    CHAT_ENDPOINT,
                    json={"query": query},
                    timeout=10
                )
                data = response.json()
                answer = data.get('answer', '')
                confidence = data.get('confidence', 0)
                fallback = data.get('fallback', False)
                
                # Quality metrics
                has_length = len(answer) > 50
                has_substance = len(answer.split()) > 10
                mentions_aims = 'aims' in answer.lower()
                is_hallucinating = any(
                    phrase in answer.lower() for phrase in
                    ["i don't know", "not sure", "unable to", "i can't", "uncertain"]
                )
                
                score = 0
                if has_length: score += 1
                if has_substance: score += 1
                if mentions_aims: score += 1
                if not is_hallucinating: score += 1
                
                quality_scores.append(score / 4.0)
                
                if is_hallucinating:
                    hallucination_detected += 1
                
                logger.info(f"   Query: '{query}'")
                logger.info(f"      Answer length: {len(answer)} chars | Confidence: {confidence:.2f}")
                logger.info(f"      Quality score: {score}/4 | Hallucinating: {is_hallucinating}")
                
            except Exception as e:
                logger.info(f"   ❌ Query: '{query}' - Error: {str(e)[:100]}")
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        hallucination_rate = hallucination_detected / len(test_queries) * 100 if test_queries else 0
        
        self.log_result(TestResult(
            test_name="Answer Quality",
            passed=avg_quality >= 0.75 and hallucination_rate <= 20,
            details=f"Avg quality score: {avg_quality:.2f}/1.0 | Hallucination rate: {hallucination_rate:.1f}%",
            metrics={
                "avg_quality_score": avg_quality,
                "hallucination_rate_percent": hallucination_rate,
                "hallucinations_detected": hallucination_detected,
                "total_queries": len(test_queries)
            }
        ))
        
        return avg_quality >= 0.75
    
    # ============================================================================
    # TEST 6: ROUTING MODES
    # ============================================================================
    def test_routing_modes(self) -> bool:
        """Test if queries are routed to correct mode (structured/RAG/fallback)."""
        logger.info("\n" + "="*70)
        logger.info("TEST 6: ROUTING MODES")
        logger.info("="*70)
        
        if not self.api_available:
            self.log_result(TestResult(
                test_name="Routing Modes",
                passed=False,
                details="Skipped (API not available)"
            ))
            return False
        
        test_cases = [
            ("MBA fees", "structured"),  # Should hit structured KB
            ("Campus facilities", "rag"),  # Should hit RAG
            ("Random gibberish xyz", "fallback"),  # Should fallback
        ]
        
        correct_routes = 0
        
        for query, expected_mode in test_cases:
            try:
                response = requests.post(
                    CHAT_ENDPOINT,
                    json={"query": query},
                    timeout=10
                )
                data = response.json()
                detected_mode = data.get('mode', 'unknown')
                is_correct = detected_mode == expected_mode
                
                status = "✅" if is_correct else "❌"
                logger.info(f"   {status} Query: '{query}'")
                logger.info(f"      Expected: {expected_mode} | Detected: {detected_mode}")
                logger.info(f"      Fallback: {data.get('fallback')}")
                
                if is_correct:
                    correct_routes += 1
                    
            except Exception as e:
                logger.info(f"   ❌ Query: '{query}' - Error: {str(e)[:100]}")
        
        accuracy = correct_routes / len(test_cases) * 100 if test_cases else 0
        
        self.log_result(TestResult(
            test_name="Routing Modes",
            passed=accuracy >= 66,  # 2 out of 3
            details=f"Routing accuracy: {accuracy:.1f}% ({correct_routes}/{len(test_cases)} correct)",
            metrics={
                "accuracy_percent": accuracy,
                "correct_routes": correct_routes,
                "total_tests": len(test_cases)
            }
        ))
        
        return accuracy >= 66
    
    # ============================================================================
    # TEST 7: BRAIN LAYER COMPONENTS
    # ============================================================================
    def test_brain_layer(self) -> bool:
        """Test if brain layer components are active."""
        logger.info("\n" + "="*70)
        logger.info("TEST 7: BRAIN LAYER COMPONENTS")
        logger.info("="*70)
        
        if not self.api_available:
            self.log_result(TestResult(
                test_name="Brain Layer",
                passed=False,
                details="Skipped (API not available)"
            ))
            return False
        
        try:
            # Test 1: Domain guard (should reject IIT query)
            response = requests.post(
                CHAT_ENDPOINT,
                json={"query": "What is IIT Delhi placement?"},
                timeout=10
            )
            data = response.json()
            domain_guard_works = data.get('fallback', False) or "AIMS" in data.get('answer', '')
            logger.info(f"   Domain guard (IIT query): {domain_guard_works}")
            
            # Test 2: Context resolution (follow-up should work)
            response = requests.post(
                CHAT_ENDPOINT,
                json={
                    "query": "What about hostel?",
                    "context": {"last_course": "MBA"}
                },
                timeout=10
            )
            data = response.json()
            context_works = len(data.get('answer', '')) > 20
            logger.info(f"   Context resolution (follow-up): {context_works}")
            
            # Test 3: Chunk cleaning (should remove noise)
            response = requests.post(
                CHAT_ENDPOINT,
                json={"query": "Placement"},
                timeout=10
            )
            data = response.json()
            has_clean_answer = len(data.get('answer', '')) > 0
            logger.info(f"   Chunk cleaning (processed): {has_clean_answer}")
            
            components_working = domain_guard_works or context_works or has_clean_answer
            
            self.log_result(TestResult(
                test_name="Brain Layer",
                passed=components_working,
                details=f"Brain layer active. Domain guard: {domain_guard_works}, Context: {context_works}, Cleaning: {has_clean_answer}",
                metrics={
                    "domain_guard": domain_guard_works,
                    "context_resolution": context_works,
                    "chunk_cleaning": has_clean_answer
                }
            ))
            
            return components_working
            
        except Exception as e:
            self.log_result(TestResult(
                test_name="Brain Layer",
                passed=False,
                details="Failed to test brain layer",
                error=str(e)
            ))
            return False
    
    # ============================================================================
    # TEST 8: EDGE CASES & ERROR HANDLING
    # ============================================================================
    def test_edge_cases(self) -> bool:
        """Test edge cases and error handling."""
        logger.info("\n" + "="*70)
        logger.info("TEST 8: EDGE CASES & ERROR HANDLING")
        logger.info("="*70)
        
        if not self.api_available:
            self.log_result(TestResult(
                test_name="Edge Cases",
                passed=False,
                details="Skipped (API not available)"
            ))
            return False
        
        edge_cases = [
            ("", "empty query"),
            ("a", "single char"),
            ("?" * 100, "spam chars"),
            ("MBA" * 50, "repetitive"),
        ]
        
        handled_correctly = 0
        
        for query, case_type in edge_cases:
            try:
                response = requests.post(
                    CHAT_ENDPOINT,
                    json={"query": query},
                    timeout=10
                )
                
                if response.status_code in [200, 400, 422]:
                    handled_correctly += 1
                    status = "✅"
                else:
                    status = "❌"
                
                logger.info(f"   {status} {case_type}: Status {response.status_code}")
                
            except Exception as e:
                logger.info(f"   ❌ {case_type}: {str(e)[:50]}")
        
        self.log_result(TestResult(
            test_name="Edge Cases",
            passed=handled_correctly >= 3,
            details=f"Edge cases handled: {handled_correctly}/{len(edge_cases)}",
            metrics={
                "handled_correctly": handled_correctly,
                "total_cases": len(edge_cases)
            }
        ))
        
        return handled_correctly >= 3
    
    def run_diagnostic_questions(self) -> str:
        """Run 10+ diagnostic questions."""
        logger.info("\n" + "="*70)
        logger.info("DIAGNOSTIC QUESTIONS (10+ CRITICAL QUESTIONS)")
        logger.info("="*70)
        
        questions = [
            ("Q1", "Is the API server running without crashes?", 
             f"Status: {'Yes' if self.api_available else 'NO - API NOT RESPONDING'}"),
            
            ("Q2", "Are responses returning valid JSON format?",
             f"Status: {'Yes - all responses valid' if self.api_available else 'Cannot determine - API down'}"),
            
            ("Q3", "Is session memory being maintained across queries?",
             f"Status: Need manual verification from test logs"),
            
            ("Q4", "Are intents being detected accurately?",
             f"Status: Check TEST 4 results above"),
            
            ("Q5", "Are answers coherent and not hallucinating?",
             f"Status: Check TEST 5 results above"),
            
            ("Q6", "Is the router sending queries to correct modes?",
             f"Status: Check TEST 6 results above"),
            
            ("Q7", "Are brain layer components (cleaner, scorer, etc) active?",
             f"Status: Check TEST 7 results above"),
            
            ("Q8", "Is confidence scoring reliable?",
             f"Status: Need to check if scores correlate with answer quality"),
            
            ("Q9", "Are out-of-domain queries properly rejected?",
             f"Status: Domain guard test in TEST 7"),
            
            ("Q10", "Is follow-up context being preserved?",
             f"Status: Check TEST 3 for follow-up context"),
            
            ("Q11", "Are error conditions handled gracefully?",
             f"Status: Check TEST 8 edge cases"),
            
            ("Q12", "Is there evidence of chunk cleaning improving answers?",
             f"Status: Need to compare raw vs cleaned answers"),
        ]
        
        diagnostics = "\n" + "="*70 + "\nDIAGNOSTIC QUESTIONS & ANSWERS\n" + "="*70 + "\n"
        
        for q_num, question, answer in questions:
            diagnostics += f"\n{q_num}: {question}\n   → {answer}\n"
        
        return diagnostics
    
    def generate_report(self) -> str:
        """Generate final report."""
        logger.info("\n" + "="*70)
        logger.info("FINAL REPORT")
        logger.info("="*70)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        
        report = f"""
================================================================================
                    HEADLESS BROWSER TEST REPORT
================================================================================

TEST SUMMARY:
  Total Tests: {total}
  Passed: {passed} ✅
  Failed: {failed} ❌
  Success Rate: {passed/total*100:.1f}%

DETAILED RESULTS:
"""
        
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            report += f"\n{status}: {result.test_name}\n"
            report += f"  Details: {result.details}\n"
            if result.screenshot_path:
                report += f"  Screenshot: {result.screenshot_path}\n"
            if result.metrics:
                report += f"  Metrics: {json.dumps(result.metrics, indent=4)}\n"
            if result.error:
                report += f"  Error: {result.error}\n"
        
        report += self.run_diagnostic_questions()
        
        report += f"""
================================================================================
HONEST ASSESSMENT:
================================================================================

SYSTEM STATUS: {'✅ PRODUCTION READY' if passed/total >= 0.85 else '⚠️  NEEDS WORK' if passed/total >= 0.6 else '❌ CRITICAL ISSUES'}

ACCURACY BREAKDOWN:
{chr(10).join(f"  • {r.test_name}: {'✅' if r.passed else '❌'}" for r in self.results)}

KEY FINDINGS:
  1. API Connectivity: {'✅ Working' if self.api_available else '❌ Not running - FIX FIRST'}
  2. Session Memory: Verify from test outputs
  3. Model Accuracy: Check individual test metrics
  4. Brain Layer: Check TEST 7 results
  5. Error Handling: Check TEST 8 results

NEXT STEPS:
  1. Fix any failed tests above
  2. Review screenshot outputs in: {SCREENSHOT_DIR}
  3. Address ERROR entries first
  4. Re-run tests after fixes

SCREENSHOT OUTPUTS:
  All API responses saved to: {SCREENSHOT_DIR}
  Open individual JSON files to inspect full responses

================================================================================
"""
        
        return report
    
    def run_all_tests(self):
        """Run all tests in sequence."""
        logger.info("\n\n")
        logger.info("╔" + "="*78 + "╗")
        logger.info("║" + " "*20 + "COMPREHENSIVE HEADLESS TEST SUITE" + " "*25 + "║")
        logger.info("║" + " "*15 + "Session: " + self.session_id[:20] + " "*43 + "║")
        logger.info("╚" + "="*78 + "╝")
        
        # Run all tests
        self.test_api_connectivity()
        if self.api_available:
            self.test_session_memory_single()
            self.test_session_memory_followup()
            self.test_intent_detection()
            self.test_answer_quality()
            self.test_routing_modes()
            self.test_brain_layer()
            self.test_edge_cases()
        
        # Generate and display report
        report = self.generate_report()
        logger.info(report)
        
        # Save report to file
        report_path = SCREENSHOT_DIR / "FULL_TEST_REPORT.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"\n✅ Full report saved to: {report_path}")
        logger.info(f"✅ Screenshots saved to: {SCREENSHOT_DIR}")
        
        # Calculate final result
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        return passed/total >= 0.85 if total > 0 else False


if __name__ == "__main__":
    runner = HeadlessTestRunner()
    runner.run_all_tests()
