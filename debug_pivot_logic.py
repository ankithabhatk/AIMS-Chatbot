#!/usr/bin/env python3
"""
DEBUG: Why are Tests 1 and 2 still failing?

Trace through _is_reinforcing_pivot logic
"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.confidence_engine import _is_reinforcing_pivot
from app.services.conversation_memory import UserProfile

print("="*80)
print("DEBUG: _is_reinforcing_pivot logic")
print("="*80)
print()

profile = UserProfile()
profile.interests = ["coding"]

test_queries = [
    "I actually feel coding is right for me",
    "actually I think coding makes sense",
    "I actually like business more than coding",
    "actually I'm not sure anymore"
]

for query in test_queries:
    print(f"Query: {query}")
    print(f"Profile interests: {profile.interests}")
    
    result = _is_reinforcing_pivot(query, profile)
    
    print(f"Result: {result} ({'REINFORCE - no penalty' if result else 'RECONSIDERING - apply penalty'})")
    
    # Manual trace
    q = query.lower()
    print(f"  Query lower: {q}")
    
    # Check comparison
    comparison_words = [
        "more than", "instead of", "rather than", "instead",
        "instead of", "versus", "vs", "but not"
    ]
    has_comparison = any(word in q for word in comparison_words)
    print(f"  Has comparison language? {has_comparison}")
    
    # Check new domains
    new_domains = [
        "business", "medicine", "law", "engineering", "design", "marketing",
        "sales", "art", "music", "writing", "teaching", "finance"
    ]
    found_new_domain = False
    for domain in new_domains:
        if domain in q:
            if not any(domain in interest.lower() for interest in profile.interests):
                found_new_domain = True
                print(f"  Found new domain '{domain}' not in interests")
                break
    print(f"  Has new domain? {found_new_domain}")
    
    # Check positive affirmations
    positive_affirmations = [
        "like", "love", "want", "enjoy", "right", "makes sense",
        "feel", "sure", "confident", "decided", "good"
    ]
    has_positive = any(word in q for word in positive_affirmations)
    print(f"  Has positive affirmations? {has_positive}")
    
    if has_positive:
        has_interest_mention = False
        for interest in profile.interests:
            if interest.lower() in q:
                has_interest_mention = True
                print(f"    Interest '{interest}' found in query")
                break
        print(f"  Interest mentioned? {has_interest_mention}")
    
    print()

print("="*80)
print("EXPECTED RESULTS")
print("="*80)
print("""
Test 1: "I actually feel coding is right for me"
  Should be: True (REINFORCE)
  Profile has "coding" ✓, query has "feel" and "right" ✓

Test 2: "actually I think coding makes sense"
  Should be: True (REINFORCE)
  Profile has "coding" ✓, query has "makes sense" ✓

Test 3: "I actually like business more than coding"
  Should be: False (RECONSIDERING)
  Has comparison "more than" ✓, has new domain "business" ✓

Test 4: "actually I'm not sure anymore"
  Should be: False (RECONSIDERING)
  No positive affirmations, default to False
""")
