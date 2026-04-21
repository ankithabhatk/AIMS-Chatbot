#!/usr/bin/env python3
"""
FAISS Index Diagnostic

Check index integrity and metadata alignment
"""

import sys
import os
import json

sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.retrieval.faiss_index import get_index, INDEX_FILE, METADATA_FILE

print("\n" + "="*70)
print("  FAISS Index Diagnostic")
print("="*70 + "\n")

# Get index
index = get_index()

# Show stats
stats = index.get_stats()
print("Index Statistics:")
print(f"  FAISS vectors: {stats['index_size']}")
print(f"  Metadata entries: {stats['metadata_count']}")
print(f"  doc_count: {stats['document_count']}")
print(f"  Synced: {stats['synced']}")

# Validate
print("\nValidation:")
is_valid = index.validate_integrity()

if not is_valid:
    print("\n❌ Index integrity check FAILED")
    print("\nFIX: Run ingest.py to rebuild the index")
else:
    print("✅ Index integrity OK")
    
    # Show sample metadata
    print(f"\nSample metadata (first 3 entries):")
    for i, meta in enumerate(index.metadata[:3]):
        print(f"  {i}: {meta.get('url', 'N/A')} - {meta.get('heading', 'N/A')[:40]}")

print("\n" + "="*70)
