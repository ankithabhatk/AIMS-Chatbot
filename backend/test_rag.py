#!/usr/bin/env python
"""
Quick Test Script for RAG Chatbot

Tests the complete pipeline without running the server.
"""

import sys
sys.path.insert(0, '.')

import logging
from app.services.embeddings.embedding_service import embed_text
from app.services.retrieval.faiss_index import get_index
from app.services.llm.response_generator import get_generator
from app.services.data_ingestion import test_with_sample_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_rag_pipeline():
    """Test complete RAG pipeline"""
    
    print("\n" + "="*60)
    print("AIMS Chatbot RAG Pipeline - Quick Test")
    print("="*60 + "\n")
    
    # 1. Load sample data
    print("1️⃣  Loading sample data...")
    result = test_with_sample_data()
    print(f"   Result: {result}\n")
    
    # 2. Test embedding
    print("2️⃣  Testing embedding...")
    test_query = "What programs does AIMS offer?"
    embedding = embed_text(test_query)
    print(f"   Query: {test_query}")
    print(f"   Embedding shape: {embedding.shape}")
    print(f"   First 5 values: {embedding[:5]}\n")
    
    # 3. Test retrieval
    print("3️⃣  Testing retrieval...")
    index = get_index()
    results = index.search(embedding, k=3)
    print(f"   Found {len(results)} results:")
    for i, (text, score, url, heading) in enumerate(results, 1):
        print(f"   [{i}] {heading} (score: {score:.3f})")
        print(f"       {text[:100]}...\n")
    
    # 4. Test response generation
    print("4️⃣  Generating response...")
    generator = get_generator(use_openai=False)
    response, confidence, is_fallback = generator.generate(test_query, results)
    print(f"   Response: {response}")
    print(f"   Confidence: {confidence:.2f}")
    print(f"   Is Fallback: {is_fallback}\n")
    
    # 5. Test multiple queries
    print("5️⃣  Testing multiple queries...\n")
    test_queries = [
        "How can I apply to AIMS?",
        "What is the placement rate?",
        "Tell me about the campus facilities",
        "Random gibberish xyz abc 123"
    ]
    
    for q in test_queries:
        q_embedding = embed_text(q)
        q_results = index.search(q_embedding, k=3)
        q_response, q_conf, q_fallback = generator.generate(q, q_results)
        
        status = "✅" if not q_fallback else "⚠️"
        print(f"{status} Q: {q}")
        print(f"   {q_response[:80]}...")
        print(f"   Confidence: {q_conf:.2f}\n")
    
    print("\n" + "="*60)
    print("✅ Test completed successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        test_rag_pipeline()
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
