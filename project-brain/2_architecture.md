# System Architecture

## 🏗️ High-Level Flow

```
User Query
    ↓
[FastAPI Router] /api/v1/chat
    ↓
[RAG Pipeline]
  • Embed query (Sentence-Transformers)
  • Search FAISS index
  • Retrieve top-5 chunks
  • Generate response (template/LLM)
    ↓
[Response Formatting]
  • Add sources
  • Calculate confidence
  • Track processing time
    ↓
JSON Response (answer + sources + confidence)
```

## 📦 Components

### 1. API Layer (FastAPI)
- **Routing**: app/api/
  - chat.py (RAG queries) ✅ WORKING
  - leads.py (lead capture) 🟡 Placeholder
  - analytics.py (metrics) 🟡 Placeholder
  - health.py (status check) ✅ WORKING

### 2. Services Layer (Business Logic)
- **embeddings/** - Text to vectors (Sentence-Transformers)
  - embedding_service.py ✅ WORKING
- **retrieval/** - Vector search (FAISS)
  - faiss_index.py ✅ WORKING
- **llm/** - Response generation
  - response_generator.py ✅ WORKING
- **scraper/** - Web scraping
  - college_scraper.py ✅ WORKING
- **data_ingestion.py** - Orchestrates pipeline ✅ WORKING
- crm/ (NOT STARTED)
- analytics/ (NOT STARTED)

### 3. Data Layer
- **Models** (ORM)
  - db_models.py ✅ Defined
    - documents (web pages)
    - embeddings (vectors)
    - leads (contact info)
    - chat_events (queries/responses)
- **Database**
  - PostgreSQL (not yet used)
  - FAISS index (/tmp/chatbot_faiss/) ✅ WORKING
- **Cache**
  - Redis (not yet used)

### 4. Infrastructure
- Docker Compose (Postgres + Redis + FastAPI + Celery)
- Configuration (.env based)
- Logging (structured)

## 🔄 RAG Pipeline (Detailed)

### Startup Phase
1. Load embedding model (all-MiniLM-L6-v2, 384-dim)
2. Initialize FAISS index
3. Load sample data (5 documents)
4. Ready for queries

### Query Processing Phase (Per Request)
```
Input: ChatRequest(query, session_id)
  ↓
1. Validate query (3+ chars)
  ↓
2. Embed query → 384-dim vector (50ms)
  ↓
3. FAISS search → top-5 similar chunks (10ms)
  ↓
4. Score similarity (0-1)
  ↓
5. Generate response:
   - If confidence > 0.7: Template-based generation
   - Else: Fallback (contact info)
  ↓
6. Build response:
   - Answer text
   - Confidence score
   - Top-3 sources (url + heading + snippet)
   - Processing time
  ↓
Output: ChatResponse(JSON)
```

### Performance Metrics
- Embedding load: 2-3s (first request only)
- Query embedding: 50-100ms
- FAISS search: 10-20ms
- Response generation: 100-150ms
- **Total per request**: 200-300ms
- Index size: 5 documents → Sub-second

## 🗄️ Data Flow

### Document Storage
```
Website (theaims.ac.in)
  ↓ [Scraper]
HTML Pages
  ↓ [Cleaner]
Raw Text
  ↓ [Chunker] (400-600 tokens, 50% overlap)
Text Chunks
  ↓ [Embedder] (Sentence-Transformers)
Vectors (384-dim)
  ↓ [FAISS]
Vector Index (searchable)
```

### Query Resolution
```
User Question
  ↓ [Embedder]
Query Vector (384-dim)
  ↓ [FAISS]
Similar Chunks (with scores)
  ↓ [Response Gen]
Natural Language Answer
  ↓ [Formatter]
JSON Response
```

## 🔌 Integrations (Planned)

### Phase 1 (Current)
- ✅ No external APIs (local embeddings + search)

### Phase 2 (Next)
- PostgreSQL for persistence
- Redis for response caching
- Celery for background scraping

### Phase 3 (Future)
- OpenAI GPT-3.5 for better response generation
- Salesforce CRM for lead capture
- Pinecone for scaling embeddings
- Analytics dashboard

## Security & Constraints
- ✅ No input APIs needed (offline)
- ✅ No external keys required
- 🟡 FAISS limited to GB-scale vectors
- ⚠️ Template responses may be lower quality
- ⚠️ No real-time content updates (manual scrape)

## Scalability Path
```
Current: 5 docs in FAISS
  ↓
Scale to: 1,000 docs with FAISS
  ↓
Scale to: 100K+ docs with Pinecone
  ↓
Production: Multi-region inference
```
