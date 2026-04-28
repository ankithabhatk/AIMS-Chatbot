#!/usr/bin/env python3
"""
Check what's actually in the FAISS index - simple version
"""

import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.retrieval.faiss_index import get_index
from app.services.retrieval.embeddings import get_embeddings

# Get index and embedder
index = get_index()
embedder = get_embeddings()

print("\n" + "="*80)
print("📊 VECTOR DB AUDIT")
print("="*80)

# Check index size
print(f"\n📈 Index Statistics:")
print(f"   Total documents: {index.doc_count}")
print(f"   FAISS vectors: {index.index.ntotal}\n")

# Test retrieval for key courses
test_queries = [
    "BBA placement",
    "MBA fees",
    "B.Com",
    "BCA",
    "BHM",
    "Diploma",
    "M.Com",
    "PU college"
]

print("🔍 Course Coverage Test:\n")

for query in test_queries:
    # Get embedding for query
    query_embedding = embedder.encode(query)
    
    # Search
    results = index.search(query_embedding, k=3)
    
    print(f"Query: '{query}'")
    if results:
        print(f"  ✅ Found {len(results)} results")
        for i, (text, score, url, heading, doc_id, source) in enumerate(results[:1], 1):
            # Extract course name from text
            text_preview = text[:80].replace('\n', ' ')
            print(f"     [{i}] Score: {score:.3f} | {text_preview}...")
    else:
        print(f"  ❌ No results found")
    print()

# List all unique courses mentioned in the metadata
print("\n" + "-"*80)
print("📋 All Courses in Index (from metadata):\n")

courses_found = set()
for meta in index.metadata:
    text = meta.get('full_text', meta.get('text', '')).lower()
    
    if 'bba' in text:
        courses_found.add('BBA')
    if 'mba' in text:
        courses_found.add('MBA')
    if 'bcom' in text or 'b.com' in text:
        courses_found.add('B.Com')
    if 'mcom' in text or 'm.com' in text:
        courses_found.add('M.Com')
    if 'bhm' in text:
        courses_found.add('BHM')
    if 'bca' in text:
        courses_found.add('BCA')
    if 'diploma' in text:
        courses_found.add('Diploma')
    if 'puc' in text or 'pu' in text:
        courses_found.add('PU')

print(f"Courses found: {sorted(courses_found)}\n")

if 'B.Com' not in courses_found:
    print("⚠️  B.COM NOT FOUND - Data gap detected!")
if 'M.Com' not in courses_found:
    print("⚠️  M.COM NOT FOUND - Data gap detected!")
if 'BHM' not in courses_found:
    print("⚠️  BHM NOT FOUND - Data gap detected!")
if 'Diploma' not in courses_found:
    print("⚠️  Diploma NOT FOUND - Data gap detected!")

print("\n" + "="*80)
