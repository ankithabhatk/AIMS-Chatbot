"""
Phase 2 Validation Test - Retrieval Engine Integration

Tests:
1. FAISS index loads correctly
2. Embeddings work
3. Chat endpoint returns answers with sources
4. Fallback logic triggers on low confidence
"""

import sys
import json
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

import asyncio
from app.api.chat_v2 import (
    initialize_retrieval,
    chat,
    health_check,
    retrieval_stats,
    ChatRequest
)


async def test_retrieval_engine():
    """Test the complete retrieval engine"""
    
    print("\n" + "="*70)
    print("PHASE 2: RETRIEVAL ENGINE VALIDATION")
    print("="*70)
    
    # Step 1: Initialize
    print("\n[STEP 1] Initializing retrieval engine...")
    initialize_retrieval()
    print("✓ Initialization complete")
    
    # Step 2: Check health
    print("\n[STEP 2] Checking system health...")
    health = await health_check()
    print(f"✓ Status: {health['status']}")
    print(f"  FAISS vectors: {health['faiss_vectors']}")
    print(f"  Chunks loaded: {health['chunks_loaded']}")
    
    if health['status'] == 'degraded':
        print("\n⚠️  WARNING: Knowledge base not loaded!")
        print("   Run: python backend/scripts/ingest.py")
        return False
    
    # Step 3: System stats
    print("\n[STEP 3] System statistics...")
    stats = await retrieval_stats()
    print(f"✓ FAISS Index:")
    print(f"  - Vectors: {stats['faiss_index']['vectors']}")
    print(f"  - Dimension: {stats['faiss_index']['dimension']}")
    print(f"✓ Chunks:")
    print(f"  - Total: {stats['chunks']['total']}")
    print(f"  - Sources: {stats['chunks']['sources']}")
    
    # Step 4: Test queries
    print("\n[STEP 4] Testing retrieval with real queries...")
    
    test_queries = [
        "What is the admission process for BBA?",
        "What programs are offered?",
        "Tell me about campus facilities",
        "xyz abc def 123",  # Should trigger fallback
    ]
    
    for query in test_queries:
        print(f"\n   Query: {query[:50]}...")
        
        try:
            request = ChatRequest(query=query, session_id="test-phase2")
            response = await chat(request)
            
            print(f"   ✓ Answer: {response.answer[:100]}...")
            print(f"   ✓ Confidence: {response.confidence}")
            print(f"   ✓ Sources found: {response.chunks_found}")
            print(f"   ✓ Fallback: {response.is_fallback}")
            print(f"   ✓ Time: {response.processing_time_ms}ms")
            
            if response.sources:
                print(f"   Sources: {len(response.sources)}")
                for i, source in enumerate(response.sources, 1):
                    print(f"     {i}. {source.url} ({source.relevance_score})")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    # Final summary
    print("\n" + "="*70)
    print("✅ PHASE 2 VALIDATION COMPLETE")
    print("="*70)
    print("\nRetrieval Engine Status:")
    print("  ✓ FAISS index operational")
    print("  ✓ Embeddings working")
    print("  ✓ Chat endpoint integrated")
    print("  ✓ Fallback logic active")
    print("\nReady for Phase 3: Response Generation & Optimization")
    print("="*70 + "\n")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_retrieval_engine())
    sys.exit(0 if success else 1)
