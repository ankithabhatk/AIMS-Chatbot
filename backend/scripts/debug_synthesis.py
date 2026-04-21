#!/usr/bin/env python3
"""
Debug Answer Generation

Show exactly what's happening inside answer synthesis
"""

import sys
import os
import logging

sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s'
)

from app.services.embeddings.embedding_service import embed_text
from app.services.retrieval.faiss_index import get_index
from app.services.response.filter import filter_results_by_relevance
from app.services.llm.answer_generator import get_answer_generator


query = "What is the admission process?"

print("="*70)
print(f"Query: {query}")
print("="*70)

# Embed
embedding = embed_text(query)

# Search
index = get_index()
chunks = index.search(embedding, k=3)

print(f"\nRetrieved {len(chunks)} chunks:")
for i, chunk in enumerate(chunks):
    text = chunk[0]
    score = chunk[1] if len(chunk) > 1 else 0
    print(f"\n  Chunk {i+1}:")
    print(f"    Score: {score:.3f}")
    print(f"    Length: {len(text)} chars")
    print(f"    First 200 chars: {text[:200]}...")
    print(f"    Last 50 chars: ...{text[-50:]}")

# Filter
filtered = filter_results_by_relevance(chunks, min_score=0.3)
print(f"\nAfter filtering: {len(filtered)} chunks")

# Synthesize
print(f"\nSynthesizing answer...")
answer_gen = get_answer_generator()
answer = answer_gen.synthesize(query, filtered)

print(f"\n{'='*70}")
print(f"Generated answer ({len(answer)} chars):")
print(f"{'='*70}")
print(answer)
print(f"{'='*70}")
