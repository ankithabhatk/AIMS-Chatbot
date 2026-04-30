"""
Terminal Q&A Tester - Interactive testing tool for chatbot

Features:
- Test all 100 questions automatically
- Interactive mode for manual testing
- Detailed response analysis
- Category-wise breakdown
- Export results to file
"""

import requests
import time
import json
from student_questions_100 import ALL_QUESTIONS, CATEGORY_MAP, STUDENT_QUESTIONS

API_URL = "http://127.0.0.1:8000/api/v1/chat"

class Colors:
    """Terminal colors for better readability"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def test_query(query: str, session_id: str = None) -> dict:
    """Send query to chatbot API and return response"""
    if not session_id:
        session_id = f"terminal-test-{hash(query)}"
    
    payload = {
        "query": query,
        "user": {"email": "terminal@test.com"},
        "session_id": session_id,
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Connection refused - is the backend running?"}
    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except Exception as e:
        return {"error": str(e)}

def print_response(query: str, response: dict, show_full: bool = False):
    """Pretty print query and response"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}Q: {query}{Colors.END}")
    
    if "error" in response:
        print(f"{Colors.RED}ERROR: {response['error']}{Colors.END}")
        return
    
    answer = response.get("answer", "")
    intent = response.get("intent", "unknown")
    confidence = response.get("confidence", 0.0)
    fallback = response.get("fallback", False)
    
    # Status indicator
    if fallback:
        status = f"{Colors.YELLOW}⚠️  FALLBACK{Colors.END}"
    elif confidence >= 0.8:
        status = f"{Colors.GREEN}✅ HIGH CONF{Colors.END}"
    else:
        status = f"{Colors.YELLOW}⚠️  LOW CONF{Colors.END}"
    
    print(f"{Colors.BOLD}Intent:{Colors.END} {intent} | {Colors.BOLD}Confidence:{Colors.END} {confidence:.2f} | {status}")
    
    if show_full:
        print(f"\n{Colors.BOLD}Answer:{Colors.END}")
        print("-" * 80)
        print(answer)
        print("-" * 80)
    else:
        # Show first 200 chars
        preview = answer[:200] + "..." if len(answer) > 200 else answer
        print(f"\n{Colors.BOLD}Answer Preview:{Colors.END}")
        print(preview)

def analyze_response(response: dict) -> dict:
    """Analyze response quality"""
    if "error" in response:
        return {"status": "error", "quality": "error"}
    
    answer = response.get("answer", "")
    intent = response.get("intent", "unknown")
    confidence = response.get("confidence", 0.0)
    fallback = response.get("fallback", False)
    
    # Determine quality
    if fallback:
        quality = "fallback"
    elif confidence >= 0.8 and len(answer) > 50:
        quality = "good"
    elif confidence >= 0.5:
        quality = "medium"
    else:
        quality = "poor"
    
    return {
        "status": "success",
        "quality": quality,
        "intent": intent,
        "confidence": confidence,
        "fallback": fallback,
        "answer_length": len(answer),
    }

def run_all_tests(show_full: bool = False, delay: float = 0.5):
    """Run all 100 questions and analyze results"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}RUNNING 100 STUDENT QUESTIONS TEST{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}\n")
    
    results = {
        "total": 0,
        "success": 0,
        "errors": 0,
        "good": 0,
        "medium": 0,
        "poor": 0,
        "fallback": 0,
        "by_category": {},
        "details": [],
    }
    
    start_time = time.time()
    
    for i, query in enumerate(ALL_QUESTIONS, 1):
        category = CATEGORY_MAP.get(query, "unknown")
        
        print(f"\n{Colors.BOLD}[{i}/100] Category: {category}{Colors.END}")
        
        response = test_query(query)
        analysis = analyze_response(response)
        
        results["total"] += 1
        
        if analysis["status"] == "error":
            results["errors"] += 1
        else:
            results["success"] += 1
            results[analysis["quality"]] += 1
        
        # Category stats
        if category not in results["by_category"]:
            results["by_category"][category] = {
                "total": 0,
                "good": 0,
                "medium": 0,
                "poor": 0,
                "fallback": 0,
            }
        
        results["by_category"][category]["total"] += 1
        if analysis["status"] == "success":
            results["by_category"][category][analysis["quality"]] += 1
        
        # Store details
        results["details"].append({
            "question": query,
            "category": category,
            "analysis": analysis,
            "response": response if show_full else None,
        })
        
        print_response(query, response, show_full=show_full)
        
        time.sleep(delay)  # Rate limiting
    
    elapsed = time.time() - start_time
    
    # Print summary
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}TEST SUMMARY{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}\n")
    
    print(f"{Colors.BOLD}Total Questions:{Colors.END} {results['total']}")
    print(f"{Colors.BOLD}Success:{Colors.END} {results['success']} ({results['success']/results['total']*100:.1f}%)")
    print(f"{Colors.BOLD}Errors:{Colors.END} {results['errors']}")
    print(f"\n{Colors.BOLD}Quality Breakdown:{Colors.END}")
    print(f"  {Colors.GREEN}Good:{Colors.END} {results['good']} ({results['good']/results['total']*100:.1f}%)")
    print(f"  {Colors.YELLOW}Medium:{Colors.END} {results['medium']} ({results['medium']/results['total']*100:.1f}%)")
    print(f"  {Colors.RED}Poor:{Colors.END} {results['poor']} ({results['poor']/results['total']*100:.1f}%)")
    print(f"  {Colors.YELLOW}Fallback:{Colors.END} {results['fallback']} ({results['fallback']/results['total']*100:.1f}%)")
    
    print(f"\n{Colors.BOLD}Category Breakdown:{Colors.END}")
    for category, stats in results["by_category"].items():
        total = stats["total"]
        good_pct = stats["good"]/total*100 if total > 0 else 0
        print(f"  {category}: {stats['good']}/{total} good ({good_pct:.1f}%)")
    
    print(f"\n{Colors.BOLD}Time Elapsed:{Colors.END} {elapsed:.1f}s")
    print(f"{Colors.BOLD}Avg Response Time:{Colors.END} {elapsed/results['total']:.2f}s per query")
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}\n")
    
    return results

def interactive_mode():
    """Interactive Q&A mode"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}INTERACTIVE Q&A MODE{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}\n")
    
    print(f"{Colors.BOLD}Commands:{Colors.END}")
    print("  - Type your question and press Enter")
    print("  - Type 'quit' or 'exit' to exit")
    print("  - Type 'test <number>' to test a specific question from the dataset")
    print("  - Type 'list' to see all 100 questions")
    print()
    
    session_id = f"interactive-{int(time.time())}"
    
    while True:
        try:
            query = input(f"{Colors.BOLD}{Colors.BLUE}You: {Colors.END}").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print(f"\n{Colors.GREEN}Goodbye!{Colors.END}\n")
                break
            
            if query.lower() == 'list':
                print(f"\n{Colors.BOLD}100 STUDENT QUESTIONS:{Colors.END}\n")
                for i, q in enumerate(ALL_QUESTIONS, 1):
                    category = CATEGORY_MAP.get(q, "unknown")
                    print(f"{i:3d}. [{category}] {q}")
                print()
                continue
            
            if query.lower().startswith('test '):
                try:
                    num = int(query.split()[1])
                    if 1 <= num <= 100:
                        query = ALL_QUESTIONS[num - 1]
                        print(f"{Colors.CYAN}Testing question {num}: {query}{Colors.END}\n")
                    else:
                        print(f"{Colors.RED}Invalid number. Use 1-100{Colors.END}\n")
                        continue
                except (ValueError, IndexError):
                    print(f"{Colors.RED}Invalid command. Use: test <number>{Colors.END}\n")
                    continue
            
            response = test_query(query, session_id)
            print_response(query, response, show_full=True)
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.GREEN}Goodbye!{Colors.END}\n")
            break
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.END}\n")

def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'all':
            # Run all tests
            show_full = '--full' in sys.argv
            results = run_all_tests(show_full=show_full, delay=0.3)
            
            # Save results
            with open('test_results_100.json', 'w') as f:
                json.dump(results, f, indent=2)
            print(f"{Colors.GREEN}Results saved to test_results_100.json{Colors.END}\n")
        
        elif command == 'category':
            # Test specific category
            if len(sys.argv) < 3:
                print(f"{Colors.RED}Usage: python terminal_qa_tester.py category <category_name>{Colors.END}")
                print(f"{Colors.BOLD}Available categories:{Colors.END}")
                for cat in STUDENT_QUESTIONS.keys():
                    print(f"  - {cat}")
                return
            
            category = sys.argv[2]
            if category not in STUDENT_QUESTIONS:
                print(f"{Colors.RED}Invalid category: {category}{Colors.END}")
                return
            
            questions = STUDENT_QUESTIONS[category]
            print(f"\n{Colors.BOLD}Testing {len(questions)} questions from category: {category}{Colors.END}\n")
            
            for i, query in enumerate(questions, 1):
                print(f"\n{Colors.BOLD}[{i}/{len(questions)}]{Colors.END}")
                response = test_query(query)
                print_response(query, response, show_full=True)
                time.sleep(0.5)
        
        elif command == 'interactive' or command == 'i':
            interactive_mode()
        
        else:
            print(f"{Colors.RED}Unknown command: {command}{Colors.END}")
            print(f"\n{Colors.BOLD}Usage:{Colors.END}")
            print("  python terminal_qa_tester.py all          # Run all 100 tests")
            print("  python terminal_qa_tester.py all --full   # Run all tests with full responses")
            print("  python terminal_qa_tester.py category <name>  # Test specific category")
            print("  python terminal_qa_tester.py interactive  # Interactive mode")
    
    else:
        # Default: interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
