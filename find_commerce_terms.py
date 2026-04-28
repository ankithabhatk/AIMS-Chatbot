#!/usr/bin/env python3
"""
Find what B.Com variations exist in metadata
"""

import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.retrieval.faiss_index import get_index
import re

index = get_index()

print("\n" + "="*80)
print("🔍 METADATA SEARCH - What B.Com terms are used?")
print("="*80 + "\n")

# Look for commerce-related terms
commerce_patterns = [
    "bcom",
    "b.com",
    "b com",
    "commerce",
    "mcom",
    "m.com",
    "m com",
]

print("Scanning metadata for commerce variations:\n")

term_occurrences = {}

for idx, meta in enumerate(index.metadata):
    full_text = (meta.get("full_text") or meta.get("text", "")).lower()
    heading = (meta.get("heading", "")).lower()
    
    combined = f"{heading} {full_text}"
    
    for pattern in commerce_patterns:
        if pattern in combined:
            if pattern not in term_occurrences:
                term_occurrences[pattern] = {
                    'count': 0,
                    'samples': []
                }
            term_occurrences[pattern]['count'] += 1
            if len(term_occurrences[pattern]['samples']) < 1:
                # Find position in text
                pos = combined.find(pattern)
                context_start = max(0, pos - 30)
                context_end = min(len(combined), pos + len(pattern) + 30)
                context = combined[context_start:context_end].replace('\n', ' ')
                term_occurrences[pattern]['samples'].append(context)

print("Results:\n")
for term, data in sorted(term_occurrences.items()):
    print(f"  '{term}': {data['count']} times")
    if data['samples']:
        # Escape and show sample
        sample = data['samples'][0][:100].replace('\n', ' ')
        print(f"    Sample: ...{sample}...")

if not term_occurrences:
    print("  ❌ No commerce terms found in metadata!")

# Now test keyword search to see what terms it extracts from queries
print("\n" + "-"*80)
print("🔍 Testing keyword extraction logic:\n")

test_queries = ["bcom", "b.com", "b com", "commerce", "bcom available"]

for test_q in test_queries:
    terms = [term for term in re.findall(r"[a-z0-9]+", (test_q or "").lower()) if len(term) > 2]
    print(f"Query: '{test_q}'")
    print(f"  Extracted terms: {terms}\n")

print("="*80)
