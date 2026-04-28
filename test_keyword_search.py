#!/usr/bin/env python3
"""
Test keyword search for B.Com vs BCA
"""

import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.retrieval.faiss_index import get_index

index = get_index()

print("\n" + "="*80)
print("🔍 KEYWORD SEARCH TEST - B.Com vs BCA")
print("="*80 + "\n")

# Test queries
test_queries = [
    ("bcom", "B.Com query"),
    ("bcom available", "B.Com availability"),
    ("bca", "BCA query"),
    ("bca available", "BCA availability"),
]

for query, description in test_queries:
    print(f"\n📌 Query: '{query}' ({description})")
    print("-" * 60)
    
    results = index.keyword_search(query, k=3)
    
    if results:
        for i, result in enumerate(results, 1):
            text = result[0][:80] if isinstance(result, tuple) else result.get("text", "")[:80]
            score = result[1] if isinstance(result, tuple) else result.get("score", 0)
            heading = result[3] if isinstance(result, tuple) and len(result) > 3 else ""
            
            print(f"  [{i}] Score: {score:.3f}")
            print(f"      Heading: {heading[:60]}")
            print(f"      Text: {text.replace(chr(10), ' ')}...")
    else:
        print(f"  ❌ No results found!")
    print()

print("\n" + "="*80)
