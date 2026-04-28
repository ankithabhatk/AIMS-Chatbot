#!/usr/bin/env python3
"""
Simple audit: check metadata for course references WITHOUT embedding
"""

import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.retrieval.faiss_index import get_index

# Load index
try:
    index = get_index()
    if not index or index.doc_count == 0:
        print("❌ Index is empty or failed to load")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error loading index: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("📊 VECTOR DB METADATA AUDIT - No Embedding Required")
print("="*80 + "\n")

print(f"Total documents: {index.doc_count}\n")

# Scan all metadata for course references
courses_found = {}
course_keywords = {
    'BBA': ['bba'],
    'MBA': ['mba'],
    'B.Com': ['bcom', 'b.com', 'commerce'],
    'M.Com': ['mcom', 'm.com'],
    'BHM': ['bhm', 'hotel'],
    'BCA': ['bca'],
    'Diploma': ['diploma'],
    'PU': ['puc', 'pu college', 'pre-university'],
    'BEM': ['bem', 'banking economics money'],
}

print("🔍 Scanning all {0} documents for course terms...\n".format(index.doc_count))

for idx, meta in enumerate(index.metadata):
    doc_id = meta.get('doc_id', f'unknown_{idx}')
    full_text = (meta.get("full_text") or meta.get("text", "")).lower()
    heading = (meta.get("heading", "")).lower()
    
    combined_text = f"{heading} {full_text}"
    
    for course, keywords in course_keywords.items():
        for kw in keywords:
            if kw in combined_text:
                if course not in courses_found:
                    courses_found[course] = {
                        'count': 0,
                        'sample_docs': [],
                        'sample_heading': ''
                    }
                courses_found[course]['count'] += 1
                if len(courses_found[course]['sample_docs']) < 2:
                    courses_found[course]['sample_docs'].append((doc_id, heading[:80]))
                    courses_found[course]['sample_heading'] = heading[:80]
                break

print("="*80)
print("📋 RESULTS")
print("="*80 + "\n")

for course in sorted(course_keywords.keys()):
    if course in courses_found:
        data = courses_found[course]
        print(f"✅ {course}: {data['count']} document(s)")
        print(f"   Sample: {data['sample_heading']}")
    else:
        print(f"❌ {course}: NOT FOUND in any document")

print("\n" + "="*80)
print("📊 SUMMARY")
print("="*80)

found_courses = set(courses_found.keys())
missing_courses = set(course_keywords.keys()) - found_courses

print(f"\nFound: {len(found_courses)} / {len(course_keywords)}")
for course in sorted(found_courses):
    print(f"  ✅ {course}")

if missing_courses:
    print(f"\nMissing: {len(missing_courses)}")
    for course in sorted(missing_courses):
        print(f"  ❌ {course}")

print("\n" + "="*80)
