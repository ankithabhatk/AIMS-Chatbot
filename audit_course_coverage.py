#!/usr/bin/env python3
"""
Audit: What courses are actually in the vector DB?
Find what's retrievable vs what's missing
"""

import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.retrieval.faiss_index import get_index
import re

# Get the FAISS index
index = get_index()

# Test queries for each course
test_queries = [
    ("BBA", "bba placement"),
    ("MBA", "mba fees"),
    ("B.Com", "bcom courses"),
    ("M.Com", "mcom"),
    ("BHM", "bhm hospitality"),
    ("Diploma", "diploma"),
    ("PU/PUC", "pu college"),
    ("BCA", "bca"),
]

print("\n" + "="*80)
print("📊 COURSE COVERAGE AUDIT - What's in the Vector DB?")
print("="*80 + "\n")

coverage = {}

for course_name, query in test_queries:
    print(f"🔍 Testing '{course_name}' with query: '{query}'")
    
    try:
        # Retrieve chunks for this course
        results = index.retrieve(query, k=5)
        
        if results and len(results) > 0:
            chunks_found = len(results)
            
            # Extract course info from chunks
            courses_in_results = set()
            for chunk in results:
                text = chunk.get('text', '').lower()
                # Look for course names
                if 'bba' in text:
                    courses_in_results.add('BBA')
                if 'mba' in text:
                    courses_in_results.add('MBA')
                if 'bcom' in text or 'b.com' in text or 'commerce' in text:
                    courses_in_results.add('B.Com')
                if 'mcom' in text or 'm.com' in text:
                    courses_in_results.add('M.Com')
                if 'bhm' in text or 'hospitality' in text:
                    courses_in_results.add('BHM')
                if 'diploma' in text:
                    courses_in_results.add('Diploma')
                if 'puc' in text or 'pu' in text or 'pre-university' in text:
                    courses_in_results.add('PU')
                if 'bca' in text:
                    courses_in_results.add('BCA')
            
            status = "✅" if course_name in courses_in_results or chunks_found > 0 else "⚠️"
            print(f"  {status} Found {chunks_found} chunks")
            print(f"     Courses mentioned: {courses_in_results}")
            
            # Show first chunk preview
            if results:
                preview = results[0].get('text', '')[:100].replace('\n', ' ')
                print(f"     Preview: {preview}...\n")
            
            coverage[course_name] = {
                'found': chunks_found,
                'courses': courses_in_results,
                'status': 'PRESENT' if chunks_found > 0 else 'MISSING'
            }
        else:
            print(f"  ❌ NO DATA FOUND\n")
            coverage[course_name] = {
                'found': 0,
                'courses': set(),
                'status': 'MISSING'
            }
    
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        coverage[course_name] = {
            'found': 0,
            'courses': set(),
            'status': 'ERROR'
        }

# Summary
print("\n" + "="*80)
print("📋 COVERAGE SUMMARY")
print("="*80 + "\n")

present = [c for c, data in coverage.items() if data['status'] == 'PRESENT']
missing = [c for c, data in coverage.items() if data['status'] == 'MISSING']

print(f"✅ Present in DB: {present}")
print(f"❌ Missing from DB: {missing}\n")

if missing:
    print(f"⚠️  {len(missing)} courses not retrievable - DATA GAP DETECTED")
else:
    print("✅ All courses covered")

# Detailed table
print("\n" + "-"*80)
print(f"{'Course':<15} {'Status':<15} {'Chunks Found':<15}")
print("-"*80)
for course, data in coverage.items():
    print(f"{course:<15} {data['status']:<15} {data['found']:<15}")
print("-"*80)
