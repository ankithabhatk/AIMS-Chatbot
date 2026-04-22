# backend/app/services/reranker.py

def simple_rerank(query: str, results: list, min_score: float = 0.2):
    """
    Rerank search results by combining semantic similarity with keyword overlap.
    
    Args:
        query: The rewritten user query.
        results: List of dictionaries with keys 'content', 'score' (FAISS similarity).
        min_score: Minimum threshold (adjusted to 0.2 for balance).
        
    Returns:
        Top 3 reranked chunks.
    """
    # 1. Filter out weak chunks early (Pre-filtering)
    filtered_results = [r for r in results if r.get("score", 0) >= min_score]
    
    if not filtered_results:
        return []
        
    # 2. Tokenize query into words (Token overlap only)
    query_words = set(query.lower().split())

    def calculate_rerank_score(chunk):
        content = chunk.get("content", "").lower()
        content_words = set(content.split())

        # Word-level overlap count
        overlap = len(query_words & content_words)

        # Combine FAISS semantic score + keyword boost (0.05 per overlapping word)
        return chunk.get("score", 0) + (0.05 * overlap)

    # 3. Sort by boosted score
    ranked = sorted(filtered_results, key=calculate_rerank_score, reverse=True)

    # 4. Return top 3
    return ranked[:3]
