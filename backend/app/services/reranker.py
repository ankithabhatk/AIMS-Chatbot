# backend/app/services/reranker.py
"""
Reranker v2 — Retrieval Optimization for 0.9 Accuracy
======================================================
Key improvements over v1:
  1. Returns top 5 (not 3) — synthesis picks the best, more options = better coverage
  2. Bi-gram matching on top of unigrams — "highest package", "hostel fee" etc.
  3. Tighter heading-intent signals tuned from validation failures
  4. Source priority boost preserved (official > scraped)
  5. Keyword density bonus — chunks with higher % of query words score higher
"""


def simple_rerank(query: str, results: list, min_score: float = 0.2):
    """
    Rerank search results by combining semantic similarity with keyword overlap,
    bi-gram matching, and heading-intent matching.

    Args:
        query: The rewritten user query.
        results: List of dicts with keys 'content', 'score', 'heading'.
        min_score: Minimum threshold for inclusion.

    Returns:
        Top 5 reranked chunks (increased from 3 for better synthesis coverage).
    """
    # 1. Filter weak chunks
    filtered_results = [r for r in results if r.get("score", 0) >= min_score]
    if not filtered_results:
        return []

    # 2. Tokenise query — unigrams + bi-grams
    query_lower = query.lower()
    query_words = set(query_lower.split())

    # Bi-grams: "highest package", "hostel fee", "last date", etc.
    words_list = query_lower.split()
    query_bigrams = set(
        f"{words_list[i]} {words_list[i+1]}"
        for i in range(len(words_list) - 1)
    )

    # 3. Intent → heading signals (tightened from v1 based on validation)
    INTENT_SIGNALS = [
        # Specializations
        (["specializ", "subject", "stream", "track"],
         ["mba specializ", "bba specializ", "specialization", "program"]),
        # Placements — covers recruiters AND stats queries
        (["recruiter", "recruit", "company", "placed", "hiring",
          "placement", "lpa", "package", "salary", "ctc", "average", "highest"],
         ["placement", "recruiters", "top recruiters", "placement statistics",
          "placement cell", "campus placement"]),
        # Hostel / campus
        (["hostel", "accommodation", "stay", "dormitor", "resident", "campus"],
         ["hostel", "campus facilities", "campus", "infrastructure"]),
        # Admission / eligibility
        (["admission", "apply", "application", "eligib", "process",
          "procedure", "last date", "deadline", "register"],
         ["admission", "admissions process", "eligibility", "apply"]),
        # Fees / cost
        (["fee", "fees", "cost", "tuition", "scholarship", "emi", "loan"],
         ["scholarship", "fees", "financial", "fee structure", "tuition"]),
        # Accreditation
        (["accredit", "naac", "iacbe", "ranking", "nirf"],
         ["accreditation", "ranking", "naac", "recognition"]),
        # Programs / courses overview
        (["program", "course", "offer", "mba", "bba", "bca", "mca",
          "pgdm", "degree"],
         ["programs", "courses", "mba program", "bba program", "overview"]),
        # FAQ / general
        (["is", "does", "can", "how", "what", "compulsory", "lateral", "medium"],
         ["faqs", "frequently asked questions", "general"]),
    ]

    def heading_boost(chunk) -> float:
        heading = chunk.get("heading", "").lower()
        boost = 0.0

        # MBA specializations super-boost (prevent BBA bleed)
        if any(t in query_lower for t in ["specializ", "subject", "stream"]):
            if "mba" in query_lower:
                if "mba specializ" in heading or ("specializ" in heading and "mba" in heading):
                    boost += 0.35
                if "bba" in heading and "bba" not in query_lower:
                    boost -= 0.15
                return boost  # short-circuit — this signal is decisive

        for query_triggers, heading_keywords in INTENT_SIGNALS:
            if any(t in query_lower for t in query_triggers):
                matched_headings = sum(1 for h in heading_keywords if h in heading)
                if matched_headings:
                    boost += 0.10 + (0.05 * min(matched_headings, 2))  # up to +0.20

        return min(boost, 0.25)  # cap to avoid dominating semantic score

    def source_boost(chunk) -> float:
        """Official institution data beats scraped data."""
        if chunk.get("source") == "official" or chunk.get("priority", 1) >= 2:
            return 0.20
        return 0.0

    def keyword_density_bonus(chunk) -> float:
        """Higher % of query words present in chunk = better relevance signal."""
        if not query_words:
            return 0.0
        content_words = set(chunk.get("content", "").lower().split())
        unigram_hits  = len(query_words & content_words)
        density = unigram_hits / max(len(query_words), 1)
        return round(density * 0.10, 3)  # max +0.10

    def bigram_bonus(chunk) -> float:
        """Bi-gram hits catch precise phrases better than unigrams."""
        if not query_bigrams:
            return 0.0
        content_lower = chunk.get("content", "").lower()
        hits = sum(1 for bg in query_bigrams if bg in content_lower)
        return round(hits * 0.06, 3)  # +0.06 per bi-gram match

    def calculate_rerank_score(chunk) -> float:
        return (
            chunk.get("score", 0)       # base semantic similarity
            + keyword_density_bonus(chunk)
            + bigram_bonus(chunk)
            + heading_boost(chunk)
            + source_boost(chunk)
        )

    # 4. Sort by boosted score
    ranked = sorted(filtered_results, key=calculate_rerank_score, reverse=True)

    # 5. Return top 5 (was 3) — synthesis selects best, more context = better answers
    return ranked[:5]
