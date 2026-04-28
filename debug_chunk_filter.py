#!/usr/bin/env python3
"""Debug chunk filtering regression for placements queries"""

import sys
sys.path.insert(0, "/Users/maneeth/Desktop/Chat-Bot")

from backend.app.services.orchestration.engine import (
    _inject_course_context,
    _filter_chunks_by_relevance,
    _clean_rag_answer,
    parse_query,
    normalize_query
)
from backend.app.services.retrieval.faiss_index import get_index

def test_chunk_filtering():
    """Test filtering with real queries and chunks"""
    
    # Test case: placements query for MBA
    query = "Tell me about placements"
    normalized_query = normalize_query(query)
    parsed = parse_query(normalized_query)
    
    print(f"🔍 Original Query: '{query}'")
    print(f"📝 Normalized: '{normalized_query}'")
    print(f"🎯 Parsed Intents: {parsed.intents}")
    print(f"📌 Parsed Entities: {parsed.entities}")
    
    entities = parsed.entities
    course = entities.get("course", "").strip()
    
    # Step 1: Course injection
    rag_query = _inject_course_context(normalized_query, entities)
    print(f"\n💉 After Course Injection: '{rag_query}'")
    print(f"   Course: '{course}'")
    
    # Step 2: Retrieve chunks
    try:
        index = get_index()
        if index:
            print(f"\n🔎 Retrieving chunks for: '{rag_query}'...")
            chunks = index.keyword_search(rag_query, k=25)
            print(f"📦 Retrieved {len(chunks)} chunks")
            
            # Show first 5 chunks BEFORE filtering
            print(f"\n📊 First 5 chunks BEFORE filtering:")
            for i, chunk in enumerate(chunks[:5]):
                if isinstance(chunk, tuple):
                    text = chunk[0][:100] if chunk[0] else ""
                    score = chunk[1] if len(chunk) > 1 else 0
                else:
                    text = chunk.get("text", chunk.get("content", ""))[:100]
                    score = chunk.get("score", 0)
                
                print(f"  [{i}] (score={score:.3f}): {text}...")
                if isinstance(chunk, tuple) and len(chunk) > 0:
                    print(f"       Full text: {chunk[0][:200]}")
                else:
                    print(f"       Full text: {text[:200]}")
            
            # Step 3: Filter chunks
            print(f"\n🔧 Filtering with:")
            print(f"   - course='{course}'")
            print(f"   - query='{rag_query}'")
            print(f"   - max_chunks=5")
            
            filtered_chunks = _filter_chunks_by_relevance(
                chunks,
                query=rag_query,
                course=course if course else None,
                max_chunks=5
            )
            
            print(f"\n✂️  After filtering: {len(filtered_chunks)} chunks")
            
            if filtered_chunks:
                print(f"\n✅ Filtered chunks:")
                for i, chunk in enumerate(filtered_chunks):
                    if isinstance(chunk, tuple):
                        text = chunk[0][:150] if chunk[0] else ""
                    else:
                        text = chunk.get("text", chunk.get("content", ""))[:150]
                    print(f"  [{i}] {text}...")
            else:
                print(f"\n❌ NO CHUNKS AFTER FILTERING!")
                print(f"\n🔍 DEBUGGING WHY:")
                print(f"\n   Testing filtering logic manually on first 5 chunks...")
                
                for i, chunk in enumerate(chunks[:5]):
                    if isinstance(chunk, tuple):
                        text = chunk[0] if len(chunk) > 0 else ""
                    else:
                        text = chunk.get("text", chunk.get("content", ""))
                    
                    if not text:
                        print(f"\n   Chunk {i}: EMPTY TEXT - SKIPPED")
                        continue
                    
                    text_lower = text.lower()
                    print(f"\n   Chunk {i}:")
                    print(f"      Text: {text[:100]}...")
                    
                    # Course check
                    has_course = course and course.lower() in text_lower
                    print(f"      Contains course '{course}'? {has_course}")
                    
                    # Query keyword check
                    query_words = set(rag_query.lower().split())
                    query_words.discard("mba").discard("bca").discard("bba").discard("mca")
                    query_words = {w for w in query_words if len(w) > 2}
                    print(f"      Query keywords to match: {query_words}")
                    
                    if query_words:
                        matches = [w for w in query_words if w in text_lower]
                        print(f"      Matched keywords: {matches}")
                        if not matches:
                            print(f"      ❌ NO KEYWORD MATCH - would be filtered")
                    else:
                        print(f"      ⚠️  No query keywords to match")
        else:
            print("❌ Could not get FAISS index")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chunk_filtering()
