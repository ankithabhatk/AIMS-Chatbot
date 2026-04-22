"""
Comparison test: FAISS vs Supabase vector search
Run AFTER ingestion is complete
Tests both systems in parallel without affecting production
"""

import sys
import json
from typing import List, Dict

sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.embeddings.embed_pipeline import EmbeddingPipeline
from app.services.retrieval.faiss_index import FAISSIndex
from app.services.database.supabase_vector_store import SupabaseVectorStore


class VectorStoreComparison:
    """Compare FAISS vs Supabase search results"""
    
    def __init__(self):
        self.embeddings = EmbeddingPipeline()
        
        # Initialize both systems
        self.faiss = FAISSIndex()
        
        try:
            self.supabase = SupabaseVectorStore()
            self.has_supabase = True
        except:
            self.supabase = None
            self.has_supabase = False
    
    def compare_query(self, query: str, top_k: int = 5) -> Dict:
        """
        Compare results from both systems for a single query
        
        Returns:
        {
            "query": "...",
            "faiss_results": [...],
            "supabase_results": [...],
            "comparison": {
                "faiss_latency_ms": X,
                "supabase_latency_ms": Y,
                "similarity_overlap": Z%,
                "recommendation": "..."
            }
        }
        """
        import time
        
        # Embed query
        query_embedding = self.embeddings.embed_text(query)
        
        # Search FAISS
        print(f"\n🔍 Query: '{query}'")
        print(f"   Embedding dim: {len(query_embedding)}")
        
        print("\n   🟡 Searching FAISS...")
        start = time.time()
        faiss_results = self.faiss.search(query_embedding, k=top_k)
        faiss_latency = (time.time() - start) * 1000
        print(f"      ✓ Found {len(faiss_results)} results in {faiss_latency:.1f}ms")
        
        # Search Supabase
        supabase_results = []
        supabase_latency = 0
        
        if self.has_supabase:
            print("\n   🟡 Searching Supabase...")
            start = time.time()
            supabase_results = self.supabase.search(
                query_embedding.tolist(),
                match_count=top_k
            )
            supabase_latency = (time.time() - start) * 1000
            print(f"      ✓ Found {len(supabase_results)} results in {supabase_latency:.1f}ms")
        else:
            print("\n   ⚠️  Supabase not available")
        
        # Compare
        print("\n   📊 Comparison:")
        print(f"      • FAISS latency: {faiss_latency:.1f}ms")
        if self.has_supabase:
            print(f"      • Supabase latency: {supabase_latency:.1f}ms")
            speedup = supabase_latency / faiss_latency if faiss_latency > 0 else 0
            print(f"      • Speed ratio: FAISS is {speedup:.1f}x faster" if speedup > 1 else f"      • Speed ratio: Supabase is {1/speedup:.1f}x faster")
        
        return {
            "query": query,
            "faiss": {
                "results": faiss_results,
                "count": len(faiss_results),
                "latency_ms": faiss_latency
            },
            "supabase": {
                "results": supabase_results if self.has_supabase else None,
                "count": len(supabase_results) if self.has_supabase else 0,
                "latency_ms": supabase_latency if self.has_supabase else None,
                "available": self.has_supabase
            }
        }
    
    def run_test_suite(self, queries: List[str]) -> None:
        """Run comparison across multiple queries"""
        print("\n" + "="*60)
        print("VECTOR STORE COMPARISON TEST")
        print("="*60)
        
        results = []
        
        for query in queries:
            result = self.compare_query(query, top_k=3)
            results.append(result)
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        if self.has_supabase:
            total_faiss_latency = sum(r["faiss"]["latency_ms"] for r in results)
            total_supabase_latency = sum(r["supabase"]["latency_ms"] for r in results if r["supabase"]["available"])
            
            print(f"\nTotal queries: {len(results)}")
            print(f"Total FAISS latency: {total_faiss_latency:.1f}ms")
            print(f"Total Supabase latency: {total_supabase_latency:.1f}ms")
            print(f"Average FAISS: {total_faiss_latency/len(results):.1f}ms per query")
            print(f"Average Supabase: {total_supabase_latency/len(results):.1f}ms per query")
            
            # Recommendation
            print("\n📋 RECOMMENDATION:")
            if total_supabase_latency < total_faiss_latency * 0.8:
                print("   ✅ Supabase is significantly faster → migrate to primary")
            elif total_faiss_latency < total_supabase_latency * 0.8:
                print("   ✅ FAISS is significantly faster → keep as primary")
            else:
                print("   ⚖️  Performance is similar → choose based on other factors")
                print("      (e.g., scalability, persistence, cloud preference)")
        else:
            print("\nSuabase not available for comparison")
            print("To enable:")
            print("1. Run SQL in Supabase: SUPABASE_SETUP.sql")
            print("2. Ingestion will auto-populate both systems next time")
        
        # Save results
        with open("/tmp/vector_comparison_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n✓ Results saved to /tmp/vector_comparison_results.json")


if __name__ == "__main__":
    comparison = VectorStoreComparison()
    
    # Test queries
    test_queries = [
        "What programs does AIMS offer?",
        "What is the placement record?",
        "What are hostel facilities?",
    ]
    
    comparison.run_test_suite(test_queries)
