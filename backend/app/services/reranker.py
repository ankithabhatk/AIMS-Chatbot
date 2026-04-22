# backend/app/services/reranker.py

def simple_rerank(query: str, results: list, min_score: float = 0.2):
    """
    Rerank search results by combining semantic similarity with keyword overlap
    and heading-intent matching.

    Args:
        query: The rewritten user query.
        results: List of dictionaries with keys 'content', 'score', 'heading'.
        min_score: Minimum threshold.

    Returns:
        Top 3 reranked chunks.
    """
    # 1. Filter out weak chunks early
    filtered_results = [r for r in results if r.get("score", 0) >= min_score]

    if not filtered_results:
        return []

    # 2. Tokenize query
    query_lower = query.lower()
    query_words = set(query_lower.split())

    # 3. Intent detection — key phrases that signal what kind of answer is needed
    INTENT_SIGNALS = [
        (['specializ', 'subject', 'stream', 'track', 'course'],
         ['mba program', 'specialization', 'bba program']),
        (['recruiter', 'recruit', 'company', 'placed', 'hiring', 'placement'],
         ['placement', 'recruiters', 'top recruiters']),
        (['hostel', 'accommodation', 'stay', 'dormitor', 'resident'],
         ['hostel', 'campus facilities']),
        (['admission', 'apply', 'application', 'eligib', 'process', 'procedure'],
         ['admission', 'admissions process', 'eligibility']),
        (['package', 'salary', 'lpa', 'ctc', 'highest', 'average'],
         ['placement statistics', 'placement', 'top recruiters']),
        (['fee', 'fees', 'cost', 'tuition'],
         ['scholarship', 'fees', 'financial']),
        (['accredit', 'naac', 'iacbe', 'ranking', 'nirf'],
         ['accreditation', 'ranking', 'naac']),
        (['is', 'does', 'can', 'how', 'what', 'compulsory', 'loan', 'lateral', 'medium'],
         ['faqs', 'frequently asked questions']),
    ]

    def heading_boost(chunk):
        heading = chunk.get("heading", "").lower()
        
        # SUPER-BOOST: MBA Specializations query → must return MBA Specs chunk, not BBA
        if any(t in query_lower for t in ['specializ', 'subject', 'stream']):
            if 'mba' in query_lower:
                # Strong preference for MBA specializations heading
                if 'mba specializ' in heading or ('specializ' in heading and 'mba' in heading):
                    return 0.35
                # Penalize BBA when asking for MBA specializations
                if 'bba' in heading and 'bba' not in query_lower:
                    return -0.15

        for query_triggers, heading_keywords in INTENT_SIGNALS:
            if any(t in query_lower for t in query_triggers):
                if any(h in heading for h in heading_keywords):
                    return 0.15  # Standard heading match bonus
        return 0.0

    def source_boost(chunk):
        """Official institution data beats scraped data."""
        if chunk.get("source") == "official" or chunk.get("priority", 1) >= 2:
            return 0.20
        return 0.0

    def calculate_rerank_score(chunk):
        content = chunk.get("content", "").lower()
        content_words = set(content.split())

        # Word-level overlap
        overlap = len(query_words & content_words)

        # Semantic score + keyword boost + heading intent boost + official source boost
        return chunk.get("score", 0) + (0.04 * overlap) + heading_boost(chunk) + source_boost(chunk)

    # 4. Sort by boosted score
    ranked = sorted(filtered_results, key=calculate_rerank_score, reverse=True)

    # 5. Return top 3
    return ranked[:3]
