# Technical Decisions Log

## Framework Selection

**[2026-04-19]**
- **Decision**: Use FastAPI for backend
- **Reason**: 
  - Async/await support for concurrency
  - Built-in API documentation (/docs)
  - Type hints for safety
  - Easy to learn and maintain
- **Impact**: Good scalability + easy debugging
- **Status**: ✅ WORKING

---

## Embedding Strategy

**[2026-04-19]**
- **Decision**: Use Sentence-Transformers (all-MiniLM-L6-v2, local)
- **Reason**:
  - No API dependency (OpenAI would cost $$)
  - 384-dimensional vectors (good balance)
  - Fast inference on CPU
  - Proven accuracy for semantic search
- **Alternative Rejected**: OpenAI embeddings (costs money)
- **Impact**: Runtime cost $0, no network calls, slightly lower accuracy
- **Status**: ✅ WORKING

---

## Vector Search

**[2026-04-19]**
- **Decision**: Use FAISS for local vector indexing
- **Reason**:
  - Zero external dependency
  - Lightning-fast L2 distance search
  - Minimal setup overhead
  - Perfect for MVP
- **Alternative Rejected**: 
  - Pinecone (external API, costs)
  - PostgreSQL pgvector (overkill for MVP)
- **Limitation**: Scales to ~100K vectors max on single machine
- **Future**: Migrate to Pinecone for production
- **Status**: ✅ WORKING

---

## Response Generation

**[2026-04-19]**
- **Decision**: Use template-based response generation (no LLM)
- **Reason**:
  - No API dependency
  - Deterministic (no hallucinations)
  - Fast (<150ms)
  - Good enough for MVP
- **Template**: "Based on information about '[heading]': [text excerpt]"
- **Optional Path**: Can swap in OpenAI if OPENAI_API_KEY provided
- **Trade-off**: Lower quality responses vs absolute reliability
- **Status**: ✅ WORKING

---

## Data Source Strategy

**[2026-04-19]**
- **Decision**: Use sample data for MVP, with option to scrape real website
- **Reason**:
  - Sample data: Fast, reliable for testing
  - Real scraping: Realistic data but fragile (website changes)
  - Can switch without code changes
- **Current**: 5 hardcoded sample documents
- **Path to Real**: `ingest_college_data()` instead of `test_with_sample_data()`
- **Web Scraper**: BeautifulSoup + Selenium ready to deploy
- **Status**: ✅ SAMPLE WORKING, Real scraper ready

---

## Project Structure

**[2026-04-19]**
- **Decision**: Modular service architecture
  ```
  services/
    ├── embeddings/      → Encapsulates embedding logic
    ├── retrieval/       → Encapsulates search logic
    ├── llm/             → Encapsulates response generation
    ├── scraper/         → Encapsulates web scraping
  ```
- **Reason**:
  - Easy to swap components (e.g., LLM)
  - Clear separation of concerns
  - Testable in isolation
  - Scalable to microservices later
- **Impact**: Clean, maintainable code
- **Status**: ✅ IMPLEMENTED

---

## Confidence Scoring

**[2026-04-19]**
- **Decision**: Use FAISS similarity score (0-1) directly as confidence
- **Reason**:
  - Simple, interpretable
  - Threshold-based fallback (0.7)
  - No additional ML model needed
- **Threshold**: 0.7 = "confident", <0.7 = "fallback to contact info"
- **Status**: ✅ WORKING

---

## Fallback Strategy

**[2026-04-19]**
- **Decision**: Return contact info when confidence < 0.7
- **Response**: "I don't have specific information. Contact admissions@theaims.ac.in"
- **Reason**:
  - Graceful degradation
  - Always useful to user
  - No misinformation
  - CRM integration point (capture contact)
- **Status**: ✅ WORKING

---

## Data Persistence

**[2026-04-19]**
- **Decision**: Local disk storage for MVP (FAISS in /tmp/)
- **Reason**:
  - No database setup needed
  - Fast for testing
  - Survives process restarts
- **Future**: PostgreSQL + pgvector for production
- **Status**: ✅ WORKING for MVP

---

## Dependencies

**[2026-04-19]**
- **Decision**: Minimal external dependencies
- **Added**:
  - sentence-transformers (embeddings)
  - faiss-cpu (vector search)
  - numpy (arrays)
  - lxml (HTML parsing)
- **Reason**: Fast startup, small footprint, easier deployment
- **Status**: ✅ WORKING

---

## Error Handling

**[2026-04-19]**
- **Decision**: Graceful degradation with logging
  - Invalid query → 400 Bad Request
  - Processing error → 500 with error message
  - Missing data → Fallback response
  - Logging: All errors + warnings to stdout
- **Reason**: 
  - Professional error handling
  - Debuggable in production
  - User-friendly messages
- **Status**: ✅ IMPLEMENTED

---

## Testing Strategy

**[2026-04-19]**
- **Decision**: Provide test_rag.py script (no unit tests yet)
- **Covers**:
  - Embedding generation
  - FAISS retrieval
  - Response generation
  - Multi-query testing
- **Future**: Add pytest + fixtures
- **Status**: ✅ WORKING

---

## Next Major Decision: Database

**[PENDING]**
- Use PostgreSQL with pgvector extension?
- Timing: After lead capture is working
- Reason: Need persistence for chat history + analytics

---

## Next Major Decision: LLM

**[PENDING]**
- Add OpenAI API for better responses?
- Timing: When template-based no longer sufficient
- Cost: ~$0.001-0.01 per request
- Decision needed when: User satisfaction drops

---

## Next Major Decision: Scale

**[PENDING]**
- Migrate FAISS → Pinecone?
- Timing: When >10K documents
- Cost: $0.25/month per 100K vectors
- Decision needed when: FAISS performance degrades
