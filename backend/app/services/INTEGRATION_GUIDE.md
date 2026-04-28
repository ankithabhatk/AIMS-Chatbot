"""
INTEGRATION GUIDE - How to plug the 3 optimization modules into your existing pipeline

This file shows EXACTLY where and how to modify engine.py with minimal changes.
Copy-paste ready patches.
"""

# ==================== INTEGRATION PATCH 1: ADD IMPORTS ====================
# Add these imports to the top of engine.py

"""
from app.services.response_debate import debate_gate, run_debate
from app.services.response_transformer import format_response_for_ui, transform_to_card
from app.services.query_router import select_execution_path, optimize_retrieval_config, should_skip_layer
"""


# ==================== INTEGRATION PATCH 2: MODIFY format_rag_response ====================
# BEFORE (current):
# answer = format_rag_response(rag_chunks)

# AFTER: Add debate layer
"""
# Step 1: Check if debate is worth it
exec_config = select_execution_path(query, confidence=0.7, mode="rag")

# Step 2: Generate initial answer
initial_answer = format_rag_response(rag_chunks)

# Step 3: Optionally run debate for reasoning queries
if exec_config["use_debate"]:
    # Simple generate function
    def llm_generate(query, chunks, style="balanced"):
        # Your existing format_rag_response but with style awareness
        answer = format_rag_response(chunks)
        if style == "critical":
            answer = add_critical_caveats(answer)
        return answer
    
    final_answer, final_confidence = debate_gate(
        query=query,
        current_answer=initial_answer,
        current_confidence=0.7,
        chunks=rag_chunks,
        generate_answer_fn=llm_generate
    )
else:
    final_answer = initial_answer
    final_confidence = 0.7
"""


# ==================== INTEGRATION PATCH 3: ADD RESPONSE TRANSFORMATION ====================
# In execute_orchestration, BEFORE returning result:

"""
# Transform answer to UI card if confidence allows
if result.confidence > 0.5:  # Only for reasonable answers
    ui_response = format_response_for_ui(
        answer=result.answer,
        confidence=result.confidence,
        intent=result.intent,
        query=query,
        mode=result.mode,
        suggestions=result.suggestions
    )
    # Option A: Return as-is (UI handles card structure)
    return ui_response
    
    # Option B: Keep OrchestrationResult but add card
    result.answer_card = ui_response["message"]
    return result
"""


# ==================== INTEGRATION PATCH 4: OPTIMIZE RETRIEVAL ====================
# In execute_orchestration, BEFORE RAG retrieval:

"""
# Get optimized config
retrieval_config = optimize_retrieval_config(query, base_confidence=0.7)

# Use optimized top_k instead of fixed value
if not retrieved_chunks:
    try:
        index = get_index()
        if index and index.validate_integrity():
            rag_chunks = index.keyword_search(
                normalized_query,
                k=retrieval_config["top_k"]  # Use optimized k
            )
"""


# ==================== INTEGRATION PATCH 5: SKIP EXPENSIVE LAYERS ====================
# In verification/reranking code:

"""
# Before running expensive verification
if not should_skip_layer("verification", result.confidence):
    # Run verification
    is_valid = verify_answer(query, result.answer, chunks, llm)
    if not is_valid:
        result = fallback_response()
else:
    logger.debug("Skipping verification (high confidence)")
"""


# ==================== INTEGRATION PATCH 6: LATENCY MONITORING ====================
# At the end of execute_orchestration:

"""
import time

start_time = time.time()

# ... orchestration logic ...

actual_latency_ms = (time.time() - start_time) * 1000
exec_config = select_execution_path(query, result.confidence)
log_execution_metrics(query, exec_config, actual_latency_ms)

# Add latency to result metadata
result.metadata = {
    "latency_ms": int(actual_latency_ms),
    "path": exec_config["path"],
    "optimizations": {
        "skipped_debate": not exec_config["use_debate"],
        "skipped_verification": not exec_config["use_verification"]
    }
}
"""


# ==================== FULL INTEGRATION EXAMPLE ====================
"""
This is what your modified execute_orchestration would look like:

def execute_orchestration(query: str, retrieved_chunks = None):
    import time
    start_time = time.time()
    
    # 1. ROUTING (existing)
    if _is_out_of_domain(query):
        return out_of_domain_response()
    
    # 2. PARSING (existing)
    parsed = parse_query(normalize_query(query))
    
    # 3. STRUCTURED ATTEMPT (existing)
    structured_response = get_structured_response(query)
    if structured_response:
        return format_response_for_ui(
            structured_response["answer"],
            confidence=0.95,
            mode="structured"
        )
    
    # 4. OPTIMIZED RETRIEVAL (NEW - use optimized config)
    retrieval_config = optimize_retrieval_config(query)
    rag_chunks = index.keyword_search(query, k=retrieval_config["top_k"])
    
    if has_meaningful_chunks(rag_chunks):
        # 5. GENERATE WITH OPTIONAL DEBATE (NEW)
        exec_config = select_execution_path(query, confidence=0.7)
        
        initial_answer = format_rag_response(rag_chunks)
        
        if exec_config["use_debate"]:
            final_answer, confidence = debate_gate(
                query, initial_answer, 0.7, rag_chunks, 
                lambda q, c, **kw: format_rag_response(c)
            )
        else:
            final_answer = initial_answer
            confidence = 0.7
        
        # 6. VERIFY (OPTIONAL - skip if high confidence)
        if exec_config["use_verification"] and confidence < 0.75:
            if not verify_answer(query, final_answer, rag_chunks):
                final_answer = fallback_message()
        
        # 7. TRANSFORM TO UI CARD (NEW)
        result = format_response_for_ui(
            final_answer,
            confidence=confidence,
            intent=parsed.intents[0],
            mode="rag"
        )
        
        # 8. LOG METRICS (NEW)
        latency_ms = (time.time() - start_time) * 1000
        log_execution_metrics(query, exec_config, latency_ms)
        
        return result
    
    # 9. FALLBACK (existing)
    return fallback_response()
"""


# ==================== TESTING THE INTEGRATION ====================
"""
Test queries to verify the 3 layers are working:

# Test 1: Debate is triggered
Query: "Is MBA worth the cost?"
Expected: Debate runs → balanced answer with reasoning

# Test 2: Fast path (high confidence)
Query: "MBA fees"
Expected: ~200ms response, no debate

# Test 3: UI card transformation
Query: "placements"
Expected: Returns placement_card with structured data
    {
        "type": "placement_card",
        "data": {
            "highest": "₹23 LPA",
            "average": "₹8 LPA",
            "recruiters": ["Deloitte", "EY"]
        }
    }

# Test 4: Latency optimization
Query: "MBA"
Expected: Uses SEARCH path, retrieves only top_k=3

# Test 5: Complex query with full pipeline
Query: "Which is better: MBA or BBA for IT careers?"
Expected: DEEP path, runs debate, returns comparison_card
"""


# ==================== CONFIGURATION TUNING ====================
"""
If you want to adjust the behavior, modify these in query_router.py:

# Increase debate threshold
if base_confidence > 0.85:  # was 0.80
    return fast_path()

# Make fast path even faster
if profile.is_simple:
    return {
        "top_k": 2,  # was 3
        "use_reranking": False
    }

# Require more data for RAG
if not has_meaningful_chunks(rag_chunks, min_score=0.4):  # was 0.3
    fallback()

# Tune debate for your use case
in response_debate.py:
penalty_per_issue = 0.20  # was 0.15, stricter
final_confidence = min(winner.score + 0.03, 0.92)  # was +0.05, more conservative
"""


# ==================== MONITORING & OBSERVABILITY ====================
"""
Track these metrics in your dashboard:

1. Execution paths used
   - Fast: should be 30-40% of queries
   - Normal: should be 50-60%
   - Deep: should be 5-10%

2. Latency distribution
   - Fast path: 100-300ms
   - Normal path: 600-1000ms
   - Deep path: 1200-1800ms

3. Debate impact
   - Queries where debate changed answer: track %
   - Average confidence before/after debate
   - User satisfaction for debated vs non-debated

4. Card type distribution
   - placement_card %
   - fees_card %
   - text %
   - This tells you answer quality

5. Optimization effectiveness
   - Layers skipped per query
   - Total time saved vs baseline
   - Answer quality improvement
"""
