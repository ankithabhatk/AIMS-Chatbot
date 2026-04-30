"""
HARSH MODE AUDIT - Real Student Simulation
Testing for trust, specificity, and human perception
"""

import requests
import time

API_URL = "http://127.0.0.1:8000/api/v1/chat"

# HARSH AUDIT QUERIES - Real skeptical student behavior
HARSH_QUERIES = [
    # CATEGORY 1: TRUST BREAKERS
    {
        "id": "Q1",
        "category": "Trust Breaker",
        "query": "Which companies actually come for placement? Don't give generic answer.",
        "expected": "Names (TCS, Infosys, etc.) OR honest fallback",
        "failure": "Generic paragraph"
    },
    {
        "id": "Q2",
        "category": "Trust Breaker",
        "query": "You said 84% placement. Show me proof or year.",
        "expected": "Recent years / varies / contact placement cell",
        "failure": "Repeats same number confidently"
    },
    
    # CATEGORY 2: REAL STUDENT THINKING
    {
        "id": "Q3",
        "category": "Real Student",
        "query": "I got 65% in 12th. Can I get BCA in AIMS? Be honest.",
        "expected": "Clear eligibility threshold",
        "failure": "Generic admission steps"
    },
    {
        "id": "Q4",
        "category": "Real Student",
        "query": "I'm weak in math but like coding. Should I still take BCA?",
        "expected": "Honest nuance + alternatives",
        "failure": "Same BCA pitch"
    },
    
    # CATEGORY 3: MULTI-INTENT REALITY
    {
        "id": "Q5",
        "category": "Multi-Intent",
        "query": "I want BCA, what are fees, placements, and is it hard?",
        "expected": "Fees + Placement + Difficulty insight",
        "failure": "Only fees + placement"
    },
    
    # CATEGORY 4: EDGE + HONESTY
    {
        "id": "Q6",
        "category": "Edge + Honesty",
        "query": "What is the exact cutoff for BCA?",
        "expected": "AIMS doesn't use fixed cutoffs",
        "failure": "Makes up cutoff"
    },
    {
        "id": "Q7",
        "category": "Edge + Honesty",
        "query": "Is AIMS tier 1 or tier 2 college?",
        "expected": "Neutral positioning",
        "failure": "Top college generic claim"
    },
    
    # CATEGORY 5: COUNSELOR DEPTH
    {
        "id": "Q8",
        "category": "Counselor Depth",
        "query": "I like coding but I also want good salary and I'm not great at studies",
        "expected": "Trade-off explanation + real-world advice",
        "failure": "Generic BCA/MCA template"
    },
    {
        "id": "Q9",
        "category": "Counselor Depth",
        "query": "My parents want MBA but I like tech. What should I do?",
        "expected": "Human-like reasoning",
        "failure": "Program list"
    },
    
    # CATEGORY 6: BOUNDARY + REDIRECTION QUALITY
    {
        "id": "Q10",
        "category": "Boundary Quality",
        "query": "I got 92 percentile in JEE. Should I join AIMS or try NIT?",
        "expected": "Acknowledge JEE value + position AIMS",
        "failure": "I can't compare (too robotic)"
    },
]

def test_query(query: str, query_id: str) -> dict:
    """Send query to chatbot API"""
    payload = {
        "query": query,
        "session_id": f"harsh-audit-{query_id}",
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def analyze_trust(answer: str, intent: str, confidence: float) -> dict:
    """Analyze if response builds or breaks trust"""
    
    # Generic signals (trust breakers)
    generic_signals = [
        "leading institutions",
        "various factors",
        "depends on",
        "typically",
        "generally",
        "many students",
        "most programs",
        "several options",
    ]
    
    # Overconfident signals (trust breakers)
    overconfident_signals = [
        "definitely",
        "guaranteed",
        "always",
        "never",
        "100%",
        "best",
        "top",
    ]
    
    # Honesty signals (trust builders)
    honesty_signals = [
        "i don't have",
        "i can't provide",
        "varies",
        "contact",
        "check with",
        "around",
        "approximately",
        "recent years",
    ]
    
    # Specificity signals (trust builders)
    has_names = any(name in answer.lower() for name in ["tcs", "infosys", "wipro", "accenture", "cognizant"])
    has_numbers = any(char.isdigit() for char in answer)
    has_aims_specific = "aims" in answer.lower()
    
    is_generic = any(signal in answer.lower() for signal in generic_signals)
    is_overconfident = any(signal in answer.lower() for signal in overconfident_signals)
    is_honest = any(signal in answer.lower() for signal in honesty_signals)
    
    # Classify
    if is_generic and not has_aims_specific:
        quality = "❌ TRUST BREAKER (Generic)"
    elif is_overconfident and not is_honest:
        quality = "❌ TRUST BREAKER (Overconfident)"
    elif is_honest or (has_names or (has_numbers and has_aims_specific)):
        quality = "✅ GOOD (Specific/Honest)"
    elif has_aims_specific:
        quality = "⚠️  SAFE (Generic but AIMS-specific)"
    else:
        quality = "⚠️  NEEDS FIX (Vague)"
    
    return {
        "quality": quality,
        "is_generic": is_generic,
        "is_overconfident": is_overconfident,
        "is_honest": is_honest,
        "has_specifics": has_names or (has_numbers and has_aims_specific),
    }

def main():
    print("\n" + "="*80)
    print("🔥 HARSH MODE AUDIT - REAL STUDENT SIMULATION 🔥")
    print("="*80)
    print()
    print("Testing for: Trust, Specificity, Human Perception")
    print()
    
    results = {
        "total": 0,
        "good": 0,
        "safe": 0,
        "needs_fix": 0,
        "trust_breaker": 0,
    }
    
    for item in HARSH_QUERIES:
        query_id = item["id"]
        category = item["category"]
        query = item["query"]
        expected = item["expected"]
        failure = item["failure"]
        
        print(f"\n{'='*80}")
        print(f"{query_id} [{category}]")
        print(f"{'='*80}")
        print(f"Q: {query}")
        print(f"\nExpected: {expected}")
        print(f"Failure Mode: {failure}")
        print(f"\n{'-'*80}")
        
        response = test_query(query, query_id)
        results["total"] += 1
        
        if "error" in response:
            print(f"❌ ERROR: {response['error']}")
            results["trust_breaker"] += 1
            continue
        
        answer = response.get("answer", "")
        intent = response.get("intent", "")
        confidence = response.get("confidence", 0.0)
        fallback = response.get("fallback", False)
        
        print(f"Intent: {intent} | Confidence: {confidence:.2f} | Fallback: {fallback}")
        print(f"\nANSWER:")
        print(answer)
        print(f"\n{'-'*80}")
        
        # Analyze trust
        analysis = analyze_trust(answer, intent, confidence)
        
        print(f"\n📊 TRUST ANALYSIS:")
        print(f"  Quality: {analysis['quality']}")
        print(f"  Generic: {'YES ❌' if analysis['is_generic'] else 'NO ✅'}")
        print(f"  Overconfident: {'YES ❌' if analysis['is_overconfident'] else 'NO ✅'}")
        print(f"  Honest: {'YES ✅' if analysis['is_honest'] else 'NO ⚠️'}")
        print(f"  Has Specifics: {'YES ✅' if analysis['has_specifics'] else 'NO ❌'}")
        
        # Count results
        if "GOOD" in analysis['quality']:
            results["good"] += 1
        elif "SAFE" in analysis['quality']:
            results["safe"] += 1
        elif "NEEDS FIX" in analysis['quality']:
            results["needs_fix"] += 1
        else:
            results["trust_breaker"] += 1
        
        time.sleep(0.5)
    
    # Summary
    print(f"\n\n{'='*80}")
    print("📊 HARSH AUDIT SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"Total Queries: {results['total']}")
    print(f"\n✅ GOOD (Specific/Honest): {results['good']}/{results['total']} ({results['good']/results['total']*100:.1f}%)")
    print(f"⚠️  SAFE (Generic but OK): {results['safe']}/{results['total']} ({results['safe']/results['total']*100:.1f}%)")
    print(f"⚠️  NEEDS FIX (Vague): {results['needs_fix']}/{results['total']} ({results['needs_fix']/results['total']*100:.1f}%)")
    print(f"❌ TRUST BREAKER: {results['trust_breaker']}/{results['total']} ({results['trust_breaker']/results['total']*100:.1f}%)")
    
    # Honest assessment
    print(f"\n{'='*80}")
    print("🎯 HONEST ASSESSMENT")
    print(f"{'='*80}\n")
    
    good_pct = results['good'] / results['total'] * 100
    trust_breaker_pct = results['trust_breaker'] / results['total'] * 100
    
    if good_pct >= 70 and trust_breaker_pct <= 10:
        print("✅ PRODUCTION READY (Real 9-10/10)")
    elif good_pct >= 50 and trust_breaker_pct <= 20:
        print("⚠️  CLOSE (Real 7-8/10) - Needs quality hardening")
    elif good_pct >= 30:
        print("⚠️  NOT READY (Real 5-6/10) - Significant trust issues")
    else:
        print("❌ NOT READY (Real 3-4/10) - Major overhaul needed")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    main()
