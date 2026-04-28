#!/usr/bin/env python3
"""
Check what courses are in the FAISS index
"""

import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.retrieval.faiss_index import get_index
from app.services.embeddings.embed_pipeline import EmbeddingPipeline

# Load index and embedder
try:
    index = get_index()
    embedder = EmbeddingPipeline()
except Exception as e:
    print(f"Error loading services: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("📊 VECTOR DB AUDIT - Course Coverage")
print("="*80)

# Check index size
print(f"\n📈 Index Statistics:")
print(f"   Total documents in metadata: {len(index.metadata)}")
print(f"   FAISS vectors: {index.index.ntotal}\n")

if index.index.ntotal == 0:
    print("⚠️  Index is EMPTY - No data loaded!")
    sys.exit(1)

# Test retrieval for key courses
test_queries = [
    "BBA",
    "MBA",
    "B.Com",
    "M.Com",
    "BHM",
    "BCA",
    "Diploma",
    "PU college"
]

print("🔍 Course Retrieval Test:\n")

courses_found_in_results = {}

for query in test_queries:
    # Get embedding
    query_embedding = embedder.embed_text(query)
    
    # Search
    results = index.search(query_embedding, k=3)
    
    print(f"Query: '{query}'")
    if results:
        print(f"  ✅ Found {len(results)} result(s)")
        for i, result in enumerate(results[:1], 1):
            # Handle different result tuple formats
            if len(result) >= 4:
                text, score, url, heading = result[0], result[1], result[2], result[3]
            else:
                text, score = result[0], result[1]
            # Extract first 100 chars
            text_preview = text[:100].replace('\n', ' ')
            print(f"     [{i}] Score: {score:.3f}")
            print(f"     Text: {text_preview}...")
        courses_found_in_results[query] = 'FOUND'
    else:
        print(f"  ❌ No results found")
        courses_found_in_results[query] = 'MISSING'
    print()

# Now scan metadata to find all course references
print("\n" + "-"*80)
print("📋 Scanning all documents for course references:\n")

courses_in_metadata = set()
course_keywords = {
    'BBA': ['bba'],
    'MBA': ['mba'],
    'B.Com': ['bcom', 'b.com', 'commerce'],
    'M.Com': ['mcom', 'm.com'],
    'BHM': ['bhm', 'hospitality'],
    'BCA': ['bca'],
    'Diploma': ['diploma'],
    'PU': ['puc', 'pu college', 'pre-university']
}

for meta in index.metadata:
    text = (meta.get('full_text') or meta.get('text', '')).lower()
    heading = (meta.get('heading', '')).lower()
    
    for course, keywords in course_keywords.items():
        for kw in keywords:
            if kw in text or kw in heading:
                courses_in_metadata.add(course)
                break

print(f"Courses found in metadata: {sorted(courses_in_metadata)}\n")

# Summary
print("\n" + "="*80)
print("⚠️  DATA GAP ANALYSIS")
print("="*80)

missing = [q for q, status in courses_found_in_results.items() if status == 'MISSING']
if missing:
    print(f"\n❌ Missing courses (query returned no results):")
    for course in missing:
        print(f"    - {course}")
else:
    print(f"\n✅ All test courses returned results")

not_in_metadata = set(test_queries) - courses_in_metadata
if not_in_metadata:
    print(f"\n❌ Not in metadata (no document references):")
    for course in not_in_metadata:
        print(f"    - {course}")
else:
    print(f"\n✅ All test courses mentioned in documents")

print("\n" + "="*80)
