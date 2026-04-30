"""
Terminal Debug Harness - Find where the system ACTUALLY breaks.

This is NOT a pass/fail test.
This is a behavior observation tool.

Goal: Find weird behaviors, not count successes.
"""

import requests
import json
from typing import Dict, Any

API_URL = "http://127.0.0.1:8000/api/v1/chat"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def query_system(query: str, course: str = None) -> Dict[str, Any]:
    """Send query to system and return full response."""
    payload = {
        "query": query,
        "user": {"email": "test@example.com"},
        "session_id": f"terminal-debug-{hash(query)}",
    }
    if course:
        payload["context"] = {"course": course}
    
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def print_debug_info(response: Dict[str, Any]):
    """Print detailed debug information."""
    print(f"\n{Colors.CYAN}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}DEBUG INFO{Colors.END}")
    print(f"{Colors.CYAN}{'=' * 80}{Colors.END}")
    
    # Extract metadata
    intent = response.get("intent", "unknown")
    status = response.get("status", "unknown")
    confidence = response.get("confidence", 0)
    fallback = response.get("fallback", False)
    
    meta = response.get("meta", {})
    original_query = meta.get("original_query", "")
    corrected_query = meta.get("corrected_query", "")
    confidence_label = meta.get("confidence_label", "")
    retrieved_chunks = meta.get("retrieved_chunks", 0)
    structured_override = meta.get("structured_override", False)
    
    # Print key metrics
    print(f"{Colors.YELLOW}Intent:{Colors.END} {intent}")
    print(f"{Colors.YELLOW}Status:{Colors.END} {status}")
    print(f"{Colors.YELLOW}Confidence:{Colors.END} {confidence} ({confidence_label})")
    print(f"{Colors.YELLOW}Fallback:{Colors.END} {fallback}")
    print(f"{Colors.YELLOW}Structured Override:{Colors.END} {structured_override}")
    print(f"{Colors.YELLOW}Retrieved Chunks:{Colors.END} {retrieved_chunks}")
    
    if original_query != corrected_query:
        print(f"{Colors.YELLOW}Original Query:{Colors.END} {original_query}")
        print(f"{Colors.YELLOW}Corrected Query:{Colors.END} {corrected_query}")
    
    # Check for issues
    issues = []
    
    # Issue 1: Lead capture check
    answer = response.get("answer", "").lower()
    if any(indicator in answer for indicator in ["provide your name", "provide your email", "name:", "email:", "phone:"]):
        issues.append(f"{Colors.RED}⚠️  LEAD CAPTURE DETECTED{Colors.END}")
    
    # Issue 2: Status mismatch
    if status == "lock":
        issues.append(f"{Colors.RED}⚠️  STATUS LOCKED (lead gate active){Colors.END}")
    
    # Issue 3: Low confidence with high chunk count
    if confidence < 0.5 and retrieved_chunks > 5:
        issues.append(f"{Colors.YELLOW}⚠️  LOW CONFIDENCE despite {retrieved_chunks} chunks{Colors.END}")
    
    # Issue 4: Fallback with structured intent
    if fallback and intent in ["courses", "fees", "scholarship", "hostel", "admission"]:
        issues.append(f"{Colors.YELLOW}⚠️  FALLBACK for structured intent '{intent}'{Colors.END}")
    
    if issues:
        print(f"\n{Colors.RED}ISSUES DETECTED:{Colors.END}")
        for issue in issues:
            print(f"  {issue}")

def print_response(response: Dict[str, Any]):
    """Print the actual response."""
    print(f"\n{Colors.GREEN}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}RESPONSE{Colors.END}")
    print(f"{Colors.GREEN}{'=' * 80}{Colors.END}")
    
    answer = response.get("answer", "")
    print(answer)
    
    # Print sources if available
    sources = response.get("sources", [])
    if sources:
        print(f"\n{Colors.BLUE}Sources:{Colors.END}")
        for source in sources[:3]:
            print(f"  • {source.get('title', 'Unknown')}")
    
    # Print suggestions if available
    suggestions = response.get("suggestions", [])
    if suggestions:
        print(f"\n{Colors.BLUE}Suggestions:{Colors.END}")
        for suggestion in suggestions[:3]:
            print(f"  • {suggestion}")

def interactive_mode():
    """Run interactive terminal mode."""
    print(f"{Colors.HEADER}{'=' * 80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}TERMINAL DEBUG HARNESS{Colors.END}")
    print(f"{Colors.HEADER}{'=' * 80}{Colors.END}")
    print(f"\nType your queries. Type 'quit' to exit.\n")
    
    while True:
        try:
            query = input(f"{Colors.BOLD}You: {Colors.END}").strip()
            
            if not query:
                continue
            
            if query.lower() in ["quit", "exit", "q"]:
                print(f"\n{Colors.CYAN}Exiting...{Colors.END}")
                break
            
            # Query the system
            response = query_system(query)
            
            if "error" in response:
                print(f"{Colors.RED}ERROR: {response['error']}{Colors.END}")
                continue
            
            # Print debug info
            print_debug_info(response)
            
            # Print response
            print_response(response)
            
            print()  # Blank line for readability
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.CYAN}Exiting...{Colors.END}")
            break
        except Exception as e:
            print(f"{Colors.RED}Unexpected error: {e}{Colors.END}")

def batch_mode(queries: list):
    """Run batch mode with predefined queries."""
    print(f"{Colors.HEADER}{'=' * 80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}BATCH MODE - BRUTAL TESTING{Colors.END}")
    print(f"{Colors.HEADER}{'=' * 80}{Colors.END}")
    print(f"\nRunning {len(queries)} queries...\n")
    
    issues_found = []
    
    for i, query in enumerate(queries, 1):
        print(f"\n{Colors.BOLD}[Query {i}/{len(queries)}]{Colors.END} {query}")
        
        response = query_system(query)
        
        if "error" in response:
            print(f"{Colors.RED}ERROR: {response['error']}{Colors.END}")
            issues_found.append(f"Query {i}: API Error")
            continue
        
        # Quick check for issues
        answer = response.get("answer", "").lower()
        intent = response.get("intent", "unknown")
        status = response.get("status", "unknown")
        fallback = response.get("fallback", False)
        
        # Flag issues
        if any(indicator in answer for indicator in ["provide your name", "provide your email"]):
            print(f"{Colors.RED}⚠️  LEAD CAPTURE{Colors.END}")
            issues_found.append(f"Query {i}: Lead capture - '{query}'")
        
        if status == "lock":
            print(f"{Colors.RED}⚠️  STATUS LOCKED{Colors.END}")
            issues_found.append(f"Query {i}: Status locked - '{query}'")
        
        if fallback and intent in ["courses", "fees", "scholarship", "hostel"]:
            print(f"{Colors.YELLOW}⚠️  FALLBACK for structured intent{Colors.END}")
            issues_found.append(f"Query {i}: Fallback for '{intent}' - '{query}'")
        
        # Print short response preview
        print(f"{Colors.GREEN}Response:{Colors.END} {answer[:150]}...")
    
    # Summary
    print(f"\n{Colors.HEADER}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}BATCH SUMMARY{Colors.END}")
    print(f"{Colors.HEADER}{'=' * 80}{Colors.END}")
    print(f"Total queries: {len(queries)}")
    print(f"Issues found: {len(issues_found)}")
    
    if issues_found:
        print(f"\n{Colors.RED}ISSUES:{Colors.END}")
        for issue in issues_found:
            print(f"  • {issue}")
    else:
        print(f"\n{Colors.GREEN}No critical issues found!{Colors.END}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        # Load brutal test queries
        from brutal_test_queries import BRUTAL_QUERIES
        batch_mode(BRUTAL_QUERIES)
    else:
        # Interactive mode
        interactive_mode()
