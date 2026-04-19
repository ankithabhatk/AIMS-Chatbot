# PRODUCTION-GRADE COLLEGE CHATBOT SYSTEM - COMPLETE ANALYSIS & IMPLEMENTATION PLAN

**Analysis Date:** April 2026  
**System Type:** RAG-based LLM Chatbot with Salesforce Integration  
**Data Source:** https://www.theaims.ac.in  
**Hosting:** Embedded widget on college website  

---

## 1. CURRENT STATE ANALYSIS

### What's Already Defined:
- **Frontend Stack:** React + TypeScript (framework chosen)
- **Backend Stack:** Python FastAPI (chosen but not implemented)
- **Domain:** College information chatbot
- **Integration Requirement:** Salesforce CRM

### What's Missing:
- Entire backend system (all 10 modules below)
- Database schema and vector store implementation
- Web scraping infrastructure
- API contracts and integration points
- Deployment/infrastructure code
- Monitoring and logging system
- Security implementation
- Testing framework
- Documentation

### Initial Risks (Honest Assessment):
1. **Scope Creep:** 10 feature sets is MASSIVE for MVP—you'll overshoot timeline
2. **Data Quality:** College websites are messy; scraping will be a constant maintenance burden
3. **Accuracy:** RAG + LLM can hallucinate; you need strong guardrails
4. **Salesforce Sync:** CRM integrations are fragile; data synchronization is non-trivial
5. **Scaling:** You don't have infrastructure code yet; "cloud-ready" is abstract
6. **Compliance:** Student data collection has privacy implications (GDPR, India privacy laws)
7. **Cost:** Vector DBs, LLM API calls, Salesforce licenses = significant monthly bill

**Reality Check:** This is 6-12 months of work for 2-3 senior engineers, NOT a one-person project.

---

## 2. FULL SYSTEM BREAKDOWN

### Module Architecture Overview:
```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + TypeScript)                  │
│           (Chat Widget + Lead Capture + Analytics Dashboard)      │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                  API Gateway (FastAPI)                           │
│         (Request routing, auth, rate-limiting, logging)          │
└─────────────────────────────────────────────────────────────────┘
                               ↓
        ┌──────────────────────┬──────────────────────┐
        ↓                      ↓                      ↓
   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
   │  Query      │      │  CRM Sync   │      │  Analytics  │
   │  Engine     │      │  Service    │      │  Service    │
   └─────────────┘      └─────────────┘      └─────────────┘
        ↓                      ↓                      ↓
   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
   │  Vector DB  │      │ Salesforce  │      │  Timescale  │
   │  (Pinecone) │      │  API Client │      │  DB         │
   └─────────────┘      └─────────────┘      └─────────────┘
        ↓
   ┌─────────────┐
   │  Embeddings │
   │  Cache      │
   └─────────────┘
```

---

### MODULE 1: WEB SCRAPING & DATA INGESTION

**Purpose:**  
Extract knowledge base from college website daily, handle updates, deduplicate content.

**Tech Stack:**
- **Tool:** Scrapy (production-grade) or BeautifulSoup + Selenium for JS-heavy pages
- **Scheduling:** Apache Airflow (complex) OR simple APScheduler (for MVP)
- **Storage:** Raw documents in S3 → PostgreSQL metadata table
- **Validation:** Schema validation, content sanity checks

**Input/Output:**
- **Input:** Website URLs (admissions, programs, faculty, fees, campus info)
- **Output:** Structured documents with metadata (source URL, last_scraped, content_hash)

**Data Volume Estimates:**
- ~500-1000 pages from typical college website
- ~50-100 KB average per page = 25-100 MB raw data
- Daily incremental scrapes = ~5-10% change rate

**Challenges:**
- Website changes without notice (frequent)
- JavaScript-rendered content (need headless Chrome)
- PDF documents (need OCR for embedded images)
- Dynamic content (forms, ratings) not applicable
- **Recommendation:** Start with BeautifulSoup for static HTML, add Selenium later

**Key Decisions Needed:**
- How frequently to scrape? (Daily? Trigger on website changes?)
- How to detect actual content changes vs. noise?
- How to handle PDFs, images, tables?
- Fallback if scraping fails?

---

### MODULE 2: DATA PREPROCESSING & CHUNKING

**Purpose:**  
Clean, normalize, and chunk documents for embedding.

**Tech Stack:**
- **Tool:** Python (langchain/llama-index for chunking strategies)
- **Language Model for cleaning:** spaCy (fast, offline)
- **Validation:** Rule-based checks + human review

**Input/Output:**
- **Input:** Raw HTML documents from scraper
- **Output:** Normalized chunks (200-500 tokens each) with metadata

**Processing Pipeline:**
```
Raw HTML 
  ↓ (Remove HTML tags, normalize whitespace)
Cleaned Text
  ↓ (Extract structure: heading → content mapping)
Semantic Units
  ↓ (Split by token count, preserve context)
Chunks with Metadata
  ↓ (Add source attribution)
Ready for Embedding
```

**Chunk Strategy (CRITICAL):**
- **Window Size:** 256-512 tokens (LLM context limit is 8K, leave room for query + response)
- **Overlap:** 50-100 tokens (preserve context boundaries)
- **Metadata:** Source URL, heading hierarchy, original position
- **Example Chunk:**
  ```
  {
    "id": "doc_001_chunk_03",
    "text": "B.Tech Computer Science: 4-year program...",
    "metadata": {
      "source_url": "https://theaims.ac.in/programs/btech-cs",
      "heading": "Academic Programs > B.Tech > Computer Science",
      "chunk_position": 3,
      "token_count": 287
    }
  }
  ```

**Challenges:**
- Table extraction from HTML (pandas can help)
- Maintaining semantic coherence across chunks
- Detecting duplicate content across pages
- **Recommendation:** Implement deduplication using content hash + semantic similarity

---

### MODULE 3: EMBEDDING GENERATION & MANAGEMENT

**Purpose:**  
Convert text chunks into vector embeddings for semantic search.

**Tech Stack:**
- **Embedding Model:** OpenAI text-embedding-3-small (cheapest + good performance)
  - Cost: $0.02 per 1M tokens = ~$1-2/month for 500 pages
  - Dimensions: 1536
  - Latency: ~100ms per request (batch 100 chunks for efficiency)
- **Alternative:** Sentence-Transformers (all-MiniLM-L6-v2) for self-hosted
- **Caching:** Redis for frequently used embedding lookups
- **Batch Processing:** Queue-based system (Celery + Redis)

**Input/Output:**
- **Input:** Text chunks (from preprocessing)
- **Output:** Vector embeddings + vectors stored in DB

**Process:**
```
Chunk (256 tokens)
  ↓ (Batch 100 chunks)
OpenAI API Call
  ↓ (1536-dim vector returned)
Store in Vector DB
  ↓ (Pinecone, Weaviate, or Milvus)
Index for retrieval
```

**Cost Breakdown:**
- OpenAI Embeddings: $1-5/month (low volume)
- Vector DB (Pinecone): $10-50/month for 10K vectors

**Challenges:**
- API rate limits (300 requests/min with OpenAI)
- Embedding drift if model changes (vendor lock-in)
- **Recommendation:** Cache embeddings in PostgreSQL + Redis for resilience

---

### MODULE 4: VECTOR DATABASE & RETRIEVAL

**Purpose:**  
Store embeddings, enable semantic search at scale.

**Options (Ranked by Risk vs. Simplicity):**

| Option | Setup Time | Cost | Scaling | Best For |
|--------|-----------|------|---------|----------|
| **Pinecone** | 1 hour | $10-50/mo | High | Production MVP |
| **Weaviate** | 2 hours | Self-hosted | Medium | Custom control |
| **Milvus** | 4 hours | Self-hosted | High | Large scale |
| **Qdrant** | 2 hours | Self-hosted | High | Modern, minimal |
| **pgvector** (PostgreSQL) | 30 min | Free | Low-Medium | Simple start |

**RECOMMENDATION FOR YOUR CONSTRAINTS:**
- **MVP (Month 1-2):** PostgreSQL pgvector (free, simple, sufficient for <10K vectors)
- **Scale to production (Month 3+):** Pinecone (managed, infinitely scalable)

**Schema (PostgreSQL pgvector):**
```sql
CREATE TABLE embeddings (
  id UUID PRIMARY KEY,
  chunk_id TEXT UNIQUE NOT NULL,
  text TEXT NOT NULL,
  embedding vector(1536) NOT NULL,
  source_url TEXT NOT NULL,
  heading TEXT,
  token_count INT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

**Retrieval Logic:**
```python
# Retrieve top-K similar chunks
embedding_query = get_embedding(user_query)  # Query from OpenAI
results = vector_db.query(
  embedding_query,
  top_k=5,  # Return top 5 chunks
  distance_threshold=0.7  # Only relevance > 70%
)
```

**Challenges:**
- Vector dimension mismatch if embedding model changes
- Stale embeddings after data updates
- **Recommendation:** Implement versioning (embedding_model_version field)

---

### MODULE 5: LLM QUERY ENGINE & RESPONSE GENERATION

**Purpose:**  
Take user query, retrieve relevant chunks, generate natural responses with citations.

**Tech Stack:**
- **LLM:** OpenAI GPT-4 (accuracy), GPT-3.5-turbo (cost)
- **Framework:** LangChain (query chaining, memory, retrieval)
- **Guardrails:** Prompt engineering + response validation

**Flow:**
```
User Query: "What are admission requirements?"
  ↓
Embedding generation
  ↓
Vector DB retrieval (top 5 chunks)
  ↓
Prompt assembly with retrieved context
  ↓
LLM call with guardrails
  ↓
Response validation (is it grounded in retrieved chunks?)
  ↓
Fallback trigger (if confidence low or no relevant chunks)
  ↓
Return response + citations
```

**Prompt Template (CRITICAL FOR ACCURACY):**
```
You are a college information chatbot. Answer ONLY based on the provided context.

CONTEXT:
{retrieved_chunks_here}

USER QUESTION: {user_query}

RULES:
1. If the answer is in the context, provide it with citations
2. If the answer is NOT in context, respond with fallback message
3. Be concise (max 3 sentences)
4. Always include source URLs

RESPONSE:
```

**Example Response:**
```
"B.Tech CS admissions require 12th pass with Math and English. 
Minimum 60% aggregate. See details: https://theaims.ac.in/admissions/btech"
```

**Confidence Scoring:**
```python
def is_confident_answer(retrieved_chunks, response):
  # Semantic similarity between response and chunks
  response_embedding = get_embedding(response)
  chunk_embeddings = [get_embedding(c) for c in retrieved_chunks]
  max_similarity = max(cosine_similarity(response_embedding, ce) 
                       for ce in chunk_embeddings)
  return max_similarity > 0.75  # Threshold tunable
```

**Cost Estimate:**
- OpenAI API: ~$0.01 per query with retrieval
- 10K queries/month = $100/month

**Challenges:**
- LLM hallucinations (claims false information)
- Token limit overflow (context too large)
- Latency (LLM calls slow, ~1-2 seconds)
- **Mitigation:** Strict validation, max token limits, response caching

---

### MODULE 6: FALLBACK & ESCALATION SYSTEM

**Purpose:**  
Route unanswerable questions to human support.

**Triggers for Fallback:**
1. No relevant chunks found (vector similarity < 0.5)
2. LLM confidence score < 0.7
3. Timeout on LLM (>5 seconds)
4. Manual user request ("Talk to human")

**Fallback Responses:**
```python
def generate_fallback_response(query, reason="unknown"):
  if retrieval_failed:
    return f"{query}? I don't have specific information. 
    Contact admissions: +91-XXXX or info@theaims.ac.in"
  
  if llm_low_confidence:
    return f"I'm not confident about this answer. 
    Please contact our admissions office for accurate info."
  
  if escalation_requested:
    # Queue in CRM, send to Salesforce
    return "Connecting you with our team..."
```

**CRM Escalation:**
- Create Salesforce Case/Lead with query + context
- Notify support team via email
- Track resolution time in analytics

---

### MODULE 7: STUDENT DATA CAPTURE & LEAD MANAGEMENT

**Purpose:**  
Collect student information, push to Salesforce CRM.

**Data Collection Points:**
1. Chat initiation (optional)
2. When asking about admissions/applications
3. Explicit form submission
4. Exit behavior (exit intent popup)

**Captured Fields:**
```
{
  "session_id": "uuid",
  "name": "string",
  "email": "string",
  "phone": "string",
  "interested_program": ["B.Tech CS", "B.Tech ECE"],
  "qualification": "12th/Grad/Other",
  "state": "string",
  "source": "direct/organic/ads/referral",
  "chat_transcript": "string",
  "interaction_quality": "high/medium/low",
  "lead_score": 0-100,  # Calculated from engagement
  "captured_at": "ISO timestamp"
}
```

**Salesforce Integration:**
```python
def push_to_salesforce(lead_data):
  sf = Salesforce(
    username=env.SF_USERNAME,
    password=env.SF_PASSWORD,
    consumer_key=env.SF_CLIENT_ID,
    consumer_secret=env.SF_CLIENT_SECRET
  )
  
  # Create or update Lead
  lead = {
    'FirstName': lead_data['name'].split()[0],
    'LastName': lead_data['name'].split()[-1],
    'Email': lead_data['email'],
    'Phone': lead_data['phone'],
    'Description': f"Program: {lead_data['interested_program']}",
    'LeadScore__c': lead_data['lead_score'],
    'Source__c': lead_data['source']
  }
  
  sf.Lead.create(lead)
```

**Privacy & Consent:**
```
[ ] I consent to receive updates about admissions
[ ] I have read the privacy policy
```

**Challenges:**
- Salesforce API rate limits (10K calls/24hrs)
- Data sync delays (async queuing needed)
- Duplicate detection (email matching)
- **Mitigation:** Batch processing, deduplication, queue-based sync

---

### MODULE 8: ANALYTICS & MONITORING

**Purpose:**  
Track chatbot usage, identify trends, measure performance.

**Metrics to Track:**
```
1. Query Metrics:
   - Total queries/day
   - Query types (admission, placement, fees, etc.)
   - Top 10 questions
   - Unanswered queries (confidence < threshold)

2. User Metrics:
   - Unique sessions/day
   - Session duration (avg, median)
   - Location distribution
   - Device type (mobile, desktop)
   - Conversion rate (% who provide contact info)

3. Performance Metrics:
   - LLM response latency (p50, p95, p99)
   - Retrieval latency
   - API error rates
   - Cache hit rate

4. Business Metrics:
   - Leads generated/day
   - Lead quality score distribution
   - Cost per lead (total spend / leads)
   - Admission correlation (did chat lead to application?)
```

**Tech Stack:**
- **Database:** TimescaleDB (PostgreSQL time-series extension)
- **Visualization:** Metabase or Grafana (open-source dashboards)
- **Real-time Alerts:** Prometheus + AlertManager

**Schema:**
```sql
CREATE TABLE chat_events (
  id UUID PRIMARY KEY,
  session_id UUID NOT NULL,
  event_type ENUM('query', 'response', 'fallback', 'escalation'),
  user_query TEXT,
  response TEXT,
  confidence_score FLOAT,
  retrieval_chunks INT,
  latency_ms INT,
  llm_model TEXT,
  created_at TIMESTAMP NOT NULL
) PARTITION BY RANGE (created_at);

SELECT 
  DATE_TRUNC('hour', created_at) AS hour,
  COUNT(*) AS query_count,
  AVG(latency_ms) AS avg_latency,
  COUNT(CASE WHEN confidence_score < 0.7 THEN 1 END) AS low_confidence_count
FROM chat_events
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY hour
ORDER BY hour DESC;
```

**Dashboard KPIs:**
- Queries/hour (trend)
- Avg response time (target: <2s)
- Low confidence rate (target: <15%)
- Escalation rate (target: <10%)
- Lead capture rate (target: >5%)

---

### MODULE 9: RECOMMENDATION ENGINE

**Purpose:**  
Suggest related questions, improve engagement.

**Two Approaches:**

**Option A: Content-Based (Simple)**
```python
def get_recommendations(current_chunk_id):
  current_embedding = get_embedding(current_chunk_id)
  # Find semantically similar chunks
  similar = vector_db.query(current_embedding, top_k=3)
  return ["Q: " + extract_question(s) for s in similar]
```

**Option B: Collaborative + Contextual (Advanced)**
```python
def recommend_questions(session_context):
  # Analyze session conversation history
  session_embedding = aggregate_embeddings(session_context['queries'])
  
  # Find chunks similar to session theme
  thematic_chunks = vector_db.query(session_embedding, top_k=10)
  
  # Score by popularity + relevance
  recommendations = score_and_rank(thematic_chunks)
  
  return top_3_recommendations
```

**Examples:**
- User asks "What are B.Tech specializations?" 
  → Recommend: "What's the placement rate for CS?", "What are internship opportunities?"
- User asks "Are hostels available?"
  → Recommend: "What's the hostel fee?", "Can day scholars get parking?"

**Challenges:**
- Cold start (new sessions with no history)
- Recommendation fatigue (same suggestions repeatedly)
- **Mitigation:** Random recommendations for cold start, rotate suggestions

**ROI:** ~5-10% engagement improvement, measurable through analytics

---

### MODULE 10: INFRASTRUCTURE & DEPLOYMENT

**Purpose:**  
Host backend, manage databases, ensure reliability.

**Tech Stack (Recommended):**
- **Compute:** AWS EC2 (t3.medium = $30/month) OR Docker on managed service (ECS, Railway)
- **Database:** AWS RDS PostgreSQL (db.t3.micro = $20/month)
- **Vector DB:** Pinecone (managed, $10-50/month) OR self-hosted Milvus
- **API Gateway:** AWS API Gateway OR Nginx
- **CDN:** CloudFlare (free tier)
- **Monitoring:** Datadog (expensive) OR Prometheus + Grafana (free)
- **Logging:** ELK Stack OR Loki + Promtail
- **Message Queue:** Redis (for async tasks)

**Deployment Architecture:**
```
[Frontend - S3 + CloudFront]
              ↓
       [CloudFlare CDN]
              ↓
       [API Gateway / Nginx]
              ↓
  [FastAPI App (Docker, ECS)]  ← Load balanced across 2-3 instances
       ↓              ↓
   [RDS PostgreSQL]  [Redis Cache]
                         ↓
              [AWS Secrets Manager]
                         ↓
              (Salesforce API key, OpenAI key)
```

**Cost Breakdown (Monthly):**
- EC2 instances: $60-100
- RDS PostgreSQL: $20-40
- Pinecone Vector DB: $20-100
- OpenAI API: $100-300 (depends on volume)
- Salesforce license: $75-165 (per seat)
- CloudFlare/CDN: $0-50
- **Total:** $275-755/month for MVP

**Deployment Strategy:**
- **Local Dev:** Docker Compose (PostgreSQL + Redis + FastAPI)
- **Staging:** Identical to production
- **Production:** Multi-instance with auto-scaling

---

## 3. GAP ANALYSIS

### Critical Gaps (Not Yet Designed):

| Component | Gap | Risk | Decision Needed |
|-----------|-----|------|-----------------|
| **Web Scraping** | No scraper defined. How handle JS? PDFs? | High | Scrapy vs. BeautifulSoup+Selenium? |
| **Deduplication** | No plan for duplicate content detection | Medium | Fuzzy matching? Whole-document hash? |
| **Auth/API Security** | No authentication, CORS policy, rate limits | High | API key? OAuth? JWT? |
| **Database Schema** | Only rough sketches provided | Medium | Finalize schema for all modules |
| **Prompt Engineering** | Generic template shown, not optimized | High | Domain-specific prompt tuning? |
| **Monitoring/Alerts** | No alerting infrastructure | Medium | Prometheus? Datadog? |
| **Testing** | No test strategy | High | Unit? Integration? E2E? |
| **Compliance** | GDPR/India privacy laws not addressed | High | Data retention? Consent management? |
| **Salesforce Sync** | Basic sync shown, no conflict resolution | Medium | Deduplication? Merge strategy? |
| **Caching Strategy** | Not clearly defined | Low | Redis for embeddings? Query cache? |
| **Error Handling** | Generic try/catch not sufficient | High | Retry logic? Circuit breakers? |
| **Load Testing** | No capacity planning | Medium | How many concurrent users? |

### Unclear Decisions:

1. **Embedding Model Strategy:**
   - OpenAI (simplest, vendor locked)
   - Self-hosted (cheaper, more control)
   - Fine-tuned model (best, expensive)

2. **LLM Model:**
   - GPT-4 (best accuracy, $0.03/call)
   - GPT-3.5-turbo (cheap, $0.001/call, lower quality)
   - Open-source (Llama 2, Mistral—requires GPU)

3. **Vector DB:**
   - Managed (Pinecone—easy, expensive)
   - Self-hosted (Milvus, Qdrant—complex, cheap)
   - Hybrid (pgvector for small, migrate later)

4. **Escalation Workflow:**
   - Auto-create Salesforce Case
   - Notify support team how? (email, Slack, webhook?)
   - SLA for response?

5. **Data Retention:**
   - How long keep chat history? (Legal requirement?)
   - How long keep embeddings?
   - How long keep analytics?

---

## 4. IMPLEMENTATION PLAN (PHASED)

### PHASE 1: MVP (8-10 weeks, 2-3 engineers)

**Goal:** Functional chatbot with RAG, live on college website, basic lead capture.

**Week 1-2: Infrastructure & Foundation**
```
Parallel tracks:
  - Set up AWS account, RDS PostgreSQL, ECR for Docker images
  - Configure CI/CD pipeline (GitHub Actions → ECR → ECS)
  - Create FastAPI boilerplate with logging, error handling
  - Set up local development environment (Docker Compose)

Deliverables:
  - Backend deployed and accessible
  - CI/CD pipeline working
  - Database migrations

Owner: DevOps / Senior Backend Engineer
```

**Week 2-3: Web Scraping**
```
Track 1: Scraper Development
  - Analyze college website structure
  - Build BeautifulSoup scraper for main pages
  - Add Selenium for JS-heavy pages if needed
  - Implement duplicate detection (hash-based)
  - Schedule with APScheduler (daily crawl at 2 AM)

Track 2: Data Storage
  - Design document metadata schema
  - Create S3 bucket for raw documents
  - Store document metadata in PostgreSQL

Deliverables:
  - Daily scraping working
  - ~500 documents ingested
  - Metadata queryable in DB

Owner: Backend Engineer
```

**Week 3-4: Preprocessing & Embeddings**
```
Track 1: Preprocessing Pipeline
  - HTML cleaning (BeautifulSoup)
  - Text normalization (regex, spaCy)
  - Semantic chunking strategy (256-512 tokens)
  - Implement chunk overlap logic
  - Extract metadata (heading hierarchy, source URL)

Track 2: Embedding Generation
  - Integrate OpenAI Embedding API
  - Batch processing (100 chunks per call)
  - Implement caching (Redis)
  - Store embeddings in PostgreSQL pgvector

Deliverables:
  - 500 documents → 2000 chunks
  - All chunks embedded (1536-dim vectors)
  - Retrieval latency < 100ms

Owner: Backend Engineer
```

**Week 4-5: Vector DB & Retrieval**
```
Implement Vector Search
  - Create pgvector indexes
  - Test similarity search (cosine distance)
  - Implement top-K retrieval logic
  - Add distance threshold filtering (0.7+)

Deliverables:
  - Vector search working
  - Top 5 relevant chunks retrieved in <100ms

Owner: Backend Engineer
```

**Week 5-6: LLM Integration & Guardrails**
```
Build Query Engine
  - Integrate OpenAI GPT-3.5-turbo (cheaper for MVP)
  - Implement prompt template with retrieved context
  - Add confidence scoring logic
  - Implement response validation (grounded in chunks)
  - Add fallback triggers (low confidence, no results)

Deliverables:
  - End-to-end query → response working
  - Confidence scoring implemented
  - Fallback to contact info working

Owner: Backend Engineer
```

**Week 6-7: Frontend Integration & Lead Capture**
```
Track 1: API Contracts
  - Design API endpoints:
    - POST /chat → query, response
    - POST /leads → student info capture
    - GET /analytics → summary stats

Track 2: Frontend Development (React)
  - Build chat widget (question input, response display, citations)
  - Implement lead capture form (name, email, phone, program interest)
  - Add follow-up question suggestions
  - Connect to backend API

Track 3: Embedding Integration
  - Build web embed SDK (single <script> tag)
  - Style widget to match college website
  - Test on sample page

Deliverables:
  - Chat widget embedded on test page
  - Lead capture working
  - API requests/responses logged

Owner: Frontend + Backend Engineer
```

**Week 7-8: Salesforce Integration**
```
Setup Salesforce
  - Create Salesforce Dev Org
  - Design Lead object schema
  - Build OAuth2 authentication
  - Implement lead push service (async, with retry logic)
  - Test end-to-end: chat → lead capture → Salesforce

Deliverables:
  - Leads automatically created in Salesforce
  - De-duplication by email working
  - Async queue prevents API rate limit errors

Owner: Backend Engineer + Salesforce Admin
```

**Week 8-9: Basic Analytics & Monitoring**
```
Analytics
  - Create chat_events table (TimescaleDB)
  - Log all queries, responses, latencies
  - Build basic dashboard (Metabase): queries/hour, avg latency, low confidence %
  - Implement health check endpoint

Deliverables:
  - Analytics dashboard live
  - Monitoring & alerting for downtime

Owner: Backend + DevOps Engineer
```

**Week 9-10: Testing & Hardening**
```
Testing
  - Unit tests for all core functions (80%+ coverage)
  - Integration tests (scraper → chunks → retrieval)
  - Load testing (100 concurrent users)
  - Security testing (API, prompt injection)

Hardening
  - Add CORS, rate limiting, API authentication
  - Implement request validation
  - Set up error tracking (Sentry)
  - Document API & deployment

Deliverables:
  - MVP live on staging
  - Ready for production (pending launch decision)

Owner: All
```

### PHASE 2: Scale & Enhancement (4-6 weeks, ongoing maintenance)

**Weeks 11-14:**
```
1. Production Deployment
   - Launch chat widget on live college website
   - Monitor for issues, fix bugs
   - Gradual rollout (20% → 50% → 100% traffic)

2. Recommendation Engine
   - Implement content-based recommendations
   - A/B test recommendation prompts
   - Measure engagement lift

3. Analytics Enhancement
   - Attribution tracking (chat → application)
   - Funnel analysis (where leads drop off)
   - Heatmaps on website

4. Vector DB Migration
   - Evaluate Pinecone for scaling
   - Migrate embeddings from pgvector to Pinecone
   - Benchmark performance

5. Prompt Optimization
   - Collect low-confidence cases
   - Iterate on prompt template
   - Fine-tune domain-specific responses

Metrics:
  - Uptime: 99.5%
  - Avg response time: <2s
  - Lead capture rate: >5%
  - Hallucination rate: <5%
```

### PHASE 3: Production Excellence (Ongoing)

**Months 4-6:**
```
1. Advanced Features
   - Multi-language support (transliteration for regional languages)
   - Chatbot personality/tone tuning
   - Context-aware follow-ups ("You asked X, might also want to know Y")

2. Scaling Preparation
   - Load test for 1000+ concurrent users
   - Implement auto-scaling policies
   - Database optimization (indexes, query rewriting)

3. Compliance & Security
   - GDPR/India privacy audit
   - Data retention policies
   - Encryption at rest / in transit
   - SOC 2 compliance path

4. Cost Optimization
   - Caching layer analysis (CloudFlare)
   - LLM call reduction (cache common questions)
   - Embedding model cost analysis

Ongoing:
  - Scraper maintenance (website changes)
  - Model fine-tuning
  - Team training (support staff on escalation handling)
```

---

## 5. CODE ARCHITECTURE

### 5.1 Folder Structure

```
chat-bot/
├── frontend/                  # React TypeScript
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWidget/            # Main chat interface
│   │   │   │   ├── ChatWidget.tsx
│   │   │   │   ├── ChatWidget.module.css
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── InputBox.tsx
│   │   │   │   └── RecommendedQuestions.tsx
│   │   │   ├── LeadCaptureForm/       # Student info form
│   │   │   │   ├── LeadForm.tsx
│   │   │   │   └── ConsentCheckbox.tsx
│   │   │   ├── SourceCitation.tsx     # Display source links
│   │   │   └── FallbackMessage.tsx    # No answer messaging
│   │   ├── services/
│   │   │   ├── chatApi.ts             # API client
│   │   │   ├── analyticsApi.ts        # Event tracking
│   │   │   └── Types.ts
│   │   ├── hooks/
│   │   │   ├── useChat.ts             # Chat logic
│   │   │   └── useLocalStorage.ts
│   │   ├── styles/                    # Global styles
│   │   ├── App.tsx
│   │   └── index.tsx
│   ├── public/
│   │   └── widget-embed.js            # Embed script
│   ├── package.json
│   └── tsconfig.json
│
├── backend/                   # Python FastAPI
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry
│   │   ├── config.py                  # Configuration (env vars)
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py                # Chat endpoint
│   │   │   ├── leads.py               # Lead capture endpoint
│   │   │   ├── analytics.py           # Analytics endpoint
│   │   │   ├── health.py              # Health check
│   │   │   └── middleware.py          # CORS, auth, rate limiting
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── scraper/
│   │   │   │   ├── scraper.py         # Web scraping
│   │   │   │   ├── deduplicator.py    # Content deduplication
│   │   │   │   └── scheduler.py       # APScheduler
│   │   │   │
│   │   │   ├── preprocessing/
│   │   │   │   ├── chunker.py         # Text chunking
│   │   │   │   ├── cleaner.py         # HTML/text cleaning
│   │   │   │   └── metadata.py        # Extract metadata
│   │   │   │
│   │   │   ├── embeddings/
│   │   │   │   ├── embedder.py        # Generate embeddings
│   │   │   │   ├── cache.py           # Redis cache
│   │   │   │   └── batch_processor.py # Batch processing
│   │   │   │
│   │   │   ├── retrieval/
│   │   │   │   ├── vector_db.py       # Vector search
│   │   │   │   ├── ranking.py         # Re-rank results
│   │   │   │   └── filters.py         # Apply distance/date filters
│   │   │   │
│   │   │   ├── llm/
│   │   │   │   ├── query_engine.py    # LLM integration
│   │   │   │   ├── prompt_templates.py # Prompt engineering
│   │   │   │   ├── validators.py      # Response validation
│   │   │   │   └── guardrails.py      # Prevent hallucinations
│   │   │   │
│   │   │   ├── crm/
│   │   │   │   ├── salesforce_client.py # SF integration
│   │   │   │   ├── lead_sync.py        # Async sync
│   │   │   │   └── deduplicator.py    # Prevent duplicates
│   │   │   │
│   │   │   ├── analytics/
│   │   │   │   ├── event_tracker.py    # Log events
│   │   │   │   ├── metrics.py          # Calculate KPIs
│   │   │   │   └── aggregator.py       # Time-series aggregation
│   │   │   │
│   │   │   └── recommendations/
│   │   │       ├── recommender.py      # Suggestion engine
│   │   │       └── ranker.py           # Rank & filter suggestions
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── db_models.py            # SQLAlchemy ORM
│   │   │   │   ├── Document
│   │   │   │   ├── Chunk
│   │   │   │   ├── Embedding
│   │   │   │   ├── ChatEvent
│   │   │   │   ├── Lead
│   │   │   │   └── AnalyticsEvent
│   │   │   │
│   │   │   └── schemas.py              # Pydantic schemas
│   │   │       ├── ChatRequest
│   │   │       ├── ChatResponse
│   │   │       ├── LeadData
│   │   │       └── AnalyticsEvent
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── logger.py              # Logging config
│   │   │   ├── cache.py               # Cache helpers
│   │   │   ├── retry.py               # Retry logic
│   │   │   ├── validators.py          # Input validation
│   │   │   └── exceptions.py          # Custom exceptions
│   │   │
│   │   └── database/
│   │       ├── __init__.py
│   │       ├── connection.py          # DB connection
│   │       ├── migrations/            # Alembic migrations
│   │       └── seeds.py               # Sample data
│   │
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_chunker.py
│   │   │   ├── test_embedder.py
│   │   │   ├── test_retrieval.py
│   │   │   ├── test_llm.py
│   │   │   └── test_validators.py
│   │   │
│   │   ├── integration/
│   │   │   ├── test_scraper_pipeline.py
│   │   │   ├── test_api_endpoints.py
│   │   │   └── test_salesforce_sync.py
│   │   │
│   │   └── fixtures/
│   │       ├── sample_html.py
│   │       ├── mock_embeddings.py
│   │       └── mock_salesforce.py
│   │
│   ├── scripts/
│   │   ├── seed_database.py       # Initial data load
│   │   ├── migrate_vectors.py     # Vector DB migration
│   │   └── analyze_logs.py        # Log analysis
│   │
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .env.example
│
├── infra/                         # Infrastructure as Code
│   ├── terraform/
│   │   ├── main.tf                # AWS resources
│   │   ├── rds.tf                 # PostgreSQL config
│   │   ├── ec2.tf                 # App server
│   │   ├── iam.tf                 # Security roles
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   ├── docker-compose.yml         # Local dev setup
│   ├── kubernetes/                # (Phase 2) K8s manifests
│   └── CI-CD/
│       ├── .github/
│       │   └── workflows/
│       │       ├── test.yml        # Run tests on PR
│       │       ├── build.yml       # Build Docker image
│       │       └── deploy.yml      # Deploy to AWS
│       └── Makefile
│
├── docs/
│   ├── API.md                     # API documentation
│   ├── ARCHITECTURE.md            # System design (this file)
│   ├── SETUP.md                   # Development setup
│   ├── DEPLOYMENT.md               # Production deployment
│   └── TROUBLESHOOTING.md
│
├── README.md
├── LICENSE
└── .gitignore
```

---

### 5.2 Database Schema (PostgreSQL)

```sql
-- ============================================
-- CORE TABLES
-- ============================================

-- Documents (raw scraped content)
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  url TEXT UNIQUE NOT NULL,
  title TEXT,
  content TEXT NOT NULL,
  content_hash VARCHAR(64) NOT NULL,  -- SHA-256 for deduplication
  scraped_at TIMESTAMP DEFAULT NOW(),
  last_updated TIMESTAMP DEFAULT NOW(),
  status ENUM('active', 'archived', 'deleted') DEFAULT 'active',
  UNIQUE(url, content_hash)
);

CREATE INDEX idx_documents_url ON documents(url);
CREATE INDEX idx_documents_content_hash ON documents(content_hash);

-- ============================================

-- Chunks (preprocessed text segments)
CREATE TABLE chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL,  -- Position in document
  text TEXT NOT NULL,
  token_count INT,
  heading TEXT,  -- Semantic context
  heading_hierarchy TEXT,  -- e.g., "Programs > B.Tech > Computer Science"
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(document_id, chunk_index)
);

CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_chunks_token_count ON chunks(token_count);

-- ============================================

-- Embeddings (vector store)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
  embedding vector(1536) NOT NULL,  -- OpenAI embedding dimension
  embedding_model TEXT DEFAULT 'text-embedding-3-small',
  embedding_model_version INT DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(chunk_id)
);

-- Create index for vector similarity search
CREATE INDEX idx_embeddings_vector ON embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================

-- Chat Events (query logging)
CREATE TABLE chat_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL,  -- User session
  user_query TEXT NOT NULL,
  retrieved_chunks INT,  -- How many chunks returned
  retrieved_chunk_ids UUID[],
  llm_response TEXT,
  confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
  latency_ms INT,
  llm_model TEXT,
  embedding_latency_ms INT,
  retrieval_latency_ms INT,
  llm_latency_ms INT,
  is_fallback BOOLEAN DEFAULT FALSE,
  fallback_reason TEXT,  -- 'no_results', 'low_confidence', 'timeout'
  user_feedback ENUM('helpful', 'not_helpful', 'null') DEFAULT 'null',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chat_events_session_id ON chat_events(session_id);
CREATE INDEX idx_chat_events_created_at ON chat_events(created_at);

-- TimescaleDB hypertable for performance
SELECT create_hypertable('chat_events', 'created_at', if_not_exists => TRUE);

-- ============================================

-- Leads (student data)
CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT,
  interested_programs TEXT[],  -- ['B.Tech CS', 'B.Tech ECE']
  qualification ENUM('12th', 'graduate', 'other') DEFAULT 'other',
  state TEXT,
  city TEXT,
  source TEXT DEFAULT 'chat',  -- 'chat', 'form_submission', 'exit_intent'
  chat_transcript TEXT,  -- Full conversation
  interaction_quality ENUM('high', 'medium', 'low'),
  lead_score FLOAT CHECK (lead_score >= 0 AND lead_score <= 100),
  consent_marketing BOOLEAN DEFAULT FALSE,
  salesforce_id VARCHAR(255),  -- SF Lead ID
  sf_sync_status ENUM('pending', 'synced', 'failed') DEFAULT 'pending',
  sf_sync_error TEXT,
  sf_last_sync_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(email, first_name, last_name)  -- Prevent duplicates
);

CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_salesforce_id ON leads(salesforce_id);
CREATE INDEX idx_leads_sf_sync_status ON leads(sf_sync_status);

-- ============================================

-- Analytics Events (custom events)
CREATE TABLE analytics_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL,
  event_type TEXT,  -- 'query', 'response', 'lead_capture', 'recommendation_click'
  event_data JSONB,  -- Flexible event properties
  created_at TIMESTAMP DEFAULT NOW()
);

SELECT create_hypertable('analytics_events', 'created_at', if_not_exists => TRUE);

-- ============================================

-- API Audit Log
CREATE TABLE api_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  endpoint TEXT,
  method TEXT,
  status_code INT,
  response_time_ms INT,
  error_message TEXT,
  user_agent TEXT,
  ip_address TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

SELECT create_hypertable('api_audit_log', 'created_at', if_not_exists => TRUE);

-- ============================================

-- Recommendations Cache
CREATE TABLE recommendation_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
  recommended_chunk_ids UUID[],  -- Top 3 related chunks
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  UNIQUE(chunk_id)
);

-- ============================================
-- VIEWS FOR ANALYTICS
-- ============================================

CREATE VIEW daily_chat_stats AS
SELECT
  DATE_TRUNC('day', created_at) AS day,
  COUNT(*) AS total_queries,
  COUNT(DISTINCT session_id) AS unique_sessions,
  AVG(latency_ms) AS avg_response_time,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95_latency,
  COUNT(CASE WHEN is_fallback THEN 1 END) AS fallback_count,
  COUNT(CASE WHEN confidence_score < 0.7 THEN 1 END) AS low_confidence_count,
  ROUND(100.0 * COUNT(CASE WHEN is_fallback THEN 1 END) / COUNT(*), 2) AS fallback_rate
FROM chat_events
GROUP BY day
ORDER BY day DESC;

CREATE VIEW hourly_performance AS
SELECT
  DATE_TRUNC('hour', created_at) AS hour,
  COUNT(*) AS query_count,
  AVG(latency_ms) AS avg_latency,
  AVG(embedding_latency_ms) AS avg_embedding_latency,
  AVG(retrieval_latency_ms) AS avg_retrieval_latency,
  AVG(llm_latency_ms) AS avg_llm_latency
FROM chat_events
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY hour
ORDER BY hour DESC;

CREATE VIEW lead_conversion_funnel AS
SELECT
  DATE_TRUNC('day', ce.created_at) AS day,
  COUNT(DISTINCT ce.session_id) AS total_chats,
  COUNT(DISTINCT CASE 
    WHEN EXISTS (SELECT 1 FROM leads l WHERE l.session_id = ce.session_id) 
    THEN ce.session_id 
  END) AS leads_captured,
  ROUND(100.0 * COUNT(DISTINCT CASE 
    WHEN EXISTS (SELECT 1 FROM leads l WHERE l.session_id = ce.session_id) 
    THEN ce.session_id 
  END) / NULLIF(COUNT(DISTINCT ce.session_id), 0), 2) AS conversion_rate
FROM chat_events ce
GROUP BY day
ORDER BY day DESC;
```

---

### 5.3 API Endpoints (FastAPI)

```python
# backend/app/api/chat.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import time

router = APIRouter(prefix="/api/v1", tags=["chat"])

class ChatRequest(BaseModel):
    query: str
    session_id: str
    user_context: dict = {}  # Optional: previous messages

class SourceCitation(BaseModel):
    url: str
    heading: str
    snippet: str

class ChatResponse(BaseModel):
    response: str
    confidence_score: float
    sources: list[SourceCitation]
    recommendations: list[str]  # Follow-up questions
    is_fallback: bool
    fallback_reason: str = None

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint. 
    Flow: Query → Embed → Retrieve → LLM → Response
    """
    session_id = request.session_id
    user_query = request.query
    
    start_time = time.time()
    
    try:
        # 1. Validate input
        if len(user_query.strip()) < 3:
            raise HTTPException(status_code=400, detail="Query too short")
        
        # 2. Generate embedding
        embedding_start = time.time()
        query_embedding = await embedding_service.embed(user_query)
        embedding_latency = time.time() - embedding_start
        
        # 3. Retrieve relevant chunks
        retrieval_start = time.time()
        chunks = await vector_db.search(
            embedding=query_embedding,
            top_k=5,
            min_similarity=0.7
        )
        retrieval_latency = time.time() - retrieval_start
        
        # 4. If no results, trigger fallback
        if not chunks:
            response = generate_fallback_response(
                query=user_query,
                reason="no_relevant_chunks"
            )
            return ChatResponse(
                response=response,
                confidence_score=0.0,
                sources=[],
                recommendations=[],
                is_fallback=True,
                fallback_reason="no_relevant_chunks"
            )
        
        # 5. Generate LLM response
        llm_start = time.time()
        llm_result = await llm_engine.query(
            user_query=user_query,
            context_chunks=chunks,
            max_tokens=300
        )
        llm_latency = time.time() - llm_start
        
        # 6. Validate response grounding
        confidence_score = await validate_response(
            response=llm_result['text'],
            context_chunks=chunks
        )
        
        # Check confidence threshold
        if confidence_score < 0.7:
            response = generate_fallback_response(
                query=user_query,
                reason="low_confidence"
            )
            return ChatResponse(
                response=response,
                confidence_score=confidence_score,
                sources=extract_citations(chunks),
                recommendations=[],
                is_fallback=True,
                fallback_reason="low_confidence"
            )
        
        # 7. Generate recommendations
        recommendations = await recommendation_service.get_recommendations(
            current_chunks=chunks,
            session_id=session_id
        )
        
        # 8. Log event
        total_latency = time.time() - start_time
        await analytics_service.log_chat_event(
            session_id=session_id,
            user_query=user_query,
            response=llm_result['text'],
            confidence_score=confidence_score,
            retrieval_count=len(chunks),
            total_latency_ms=int(total_latency * 1000),
            embedding_latency_ms=int(embedding_latency * 1000),
            retrieval_latency_ms=int(retrieval_latency * 1000),
            llm_latency_ms=int(llm_latency * 1000),
            is_fallback=False
        )
        
        return ChatResponse(
            response=llm_result['text'],
            confidence_score=confidence_score,
            sources=extract_citations(chunks),
            recommendations=recommendations,
            is_fallback=False
        )
    
    except asyncio.TimeoutError:
        # LLM timeout (> 5s)
        await analytics_service.log_chat_event(
            session_id=session_id,
            user_query=user_query,
            is_fallback=True,
            fallback_reason="llm_timeout"
        )
        return ChatResponse(
            response="I'm taking longer than usual. Please contact support.",
            confidence_score=0.0,
            sources=[],
            recommendations=[],
            is_fallback=True,
            fallback_reason="timeout"
        )
    
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        return ChatResponse(
            response="An error occurred. Please try again.",
            confidence_score=0.0,
            sources=[],
            recommendations=[],
            is_fallback=True,
            fallback_reason="internal_error"
        )

# ============================================

class LeadData(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str = None
    interested_programs: list[str]
    qualification: str
    state: str
    consent_marketing: bool

@router.post("/leads")
async def capture_lead(lead_data: LeadData, session_id: str):
    """Capture student info and push to Salesforce"""
    try:
        # 1. Validate email (not already captured this session)
        existing = await db.fetch_one(
            "SELECT id FROM leads WHERE email = $1 AND session_id = $2",
            lead_data.email, session_id
        )
        if existing:
            return {"status": "duplicate", "message": "Already captured"}
        
        # 2. Get chat transcript for this session
        chat_transcript = await analytics_service.get_session_transcript(session_id)
        
        # 3. Calculate lead score (engagement-based)
        lead_score = calculate_lead_score(
            chat_transcript=chat_transcript,
            program_interest=lead_data.interested_programs
        )
        
        # 4. Insert into DB
        lead_id = await db.execute("""
            INSERT INTO leads (
                session_id, first_name, last_name, email, phone,
                interested_programs, qualification, state,
                chat_transcript, interaction_quality, lead_score,
                consent_marketing
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING id
        """, 
            session_id, lead_data.first_name, lead_data.last_name,
            lead_data.email, lead_data.phone,
            lead_data.interested_programs, lead_data.qualification,
            lead_data.state, chat_transcript, interaction_quality,
            lead_score, lead_data.consent_marketing
        )
        
        # 5. Queue Salesforce sync (async)
        await crm_service.queue_sync(
            lead_id=lead_id,
            lead_data=lead_data
        )
        
        return {"status": "success", "lead_id": str(lead_id)}
    
    except Exception as e:
        logger.error(f"Lead capture error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to capture lead")

# ============================================

@router.get("/analytics/dashboard")
async def get_analytics_dashboard(
    time_range: str = "7d"  # '1d', '7d', '30d'
):
    """Get analytics dashboard data"""
    
    days = {"1d": 1, "7d": 7, "30d": 30}.get(time_range, 7)
    
    stats = await db.fetch_one("""
        SELECT
          COUNT(*) as total_queries,
          COUNT(DISTINCT session_id) as unique_sessions,
          AVG(latency_ms) as avg_response_time,
          COUNT(CASE WHEN is_fallback THEN 1 END) as fallback_count,
          COUNT(CASE WHEN confidence_score < 0.7 THEN 1 END) as low_confidence_count
        FROM chat_events
        WHERE created_at > NOW() - INTERVAL $1
    """, f"{days} days")
    
    leads = await db.fetch_one("""
        SELECT
          COUNT(*) as total_leads,
          COUNT(DISTINCT email) as unique_leads,
          ROUND(AVG(lead_score), 2) as avg_lead_score
        FROM leads
        WHERE created_at > NOW() - INTERVAL $1
    """, f"{days} days")
    
    return {
        "period": time_range,
        "chat_stats": dict(stats),
        "lead_stats": dict(leads),
        "fallback_rate": round(100 * stats['fallback_count'] / stats['total_queries'], 2)
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "db": await check_db_connection(),
        "vector_db": await check_vector_db_connection(),
        "salesforce": await check_salesforce_connection()
    }
```

---

## 6. COMPLETE DATA FLOW PIPELINE

### End-to-End Flow Diagram:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                                  │
│                                                                           │
│  1. User Opens Chat Widget on College Website                            │
│  2. Types Question: "What are B.Tech admission requirements?"             │
│  3. System generates unique session_id (UUID)                            │
└──────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────────────┐
│                     QUERY ENCODING (100ms)                               │
│                                                                           │
│  Input: "What are B.Tech admission requirements?"                         │
│  ↓ (OpenAI API)                                                          │
│  Output: 1536-dimensional vector                                         │
│  [0.123, 0.456, ..., 0.789]                                             │
│  Cached in Redis for 1 hour (deduplication)                             │
└──────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────────────┐
│               VECTOR SIMILARITY SEARCH (50ms)                            │
│                                                                           │
│  Query Vector: [0.123, 0.456, ..., 0.789]                              │
│  ↓ (Cosine distance in pgvector)                                        │
│  Retrieved: [Chunk_001, Chunk_002, Chunk_003, Chunk_004, Chunk_005]    │
│                                                                          │
│  Chunk_001: "B.Tech Computer Science requires 12th pass with Math..."  │
│  similarity: 0.89 ✓                                                     │
│                                                                          │
│  Chunk_002: "Minimum 60% aggregate in 12th standard"                   │
│  similarity: 0.87 ✓                                                     │
│                                                                          │
│  [3 more chunks...]                                                      │
└──────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────────────┐
│             LLM PROMPT ASSEMBLY (200ms)                                  │
│                                                                           │
│  Prompt:                                                                 │
│  """                                                                     │
│  You are a college information chatbot.                                 │
│  Answer ONLY based on the provided context.                            │
│                                                                          │
│  CONTEXT:                                                               │
│  [Chunk_001 text]                                                       │
│  [Chunk_002 text]                                                       │
│  [Chunk_003 text]                                                       │
│  [Chunk_004 text]                                                       │
│  [Chunk_005 text]                                                       │
│                                                                          │
│  QUESTION: What are B.Tech admission requirements?                      │
│                                                                          │
│  RESPONSE:                                                              │
│  """                                                                     │
│  ↓ (OpenAI GPT-3.5-turbo, ~1500 tokens)                                │
└──────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────────────┐
│             LLM RESPONSE (1000-2000ms)                                   │
│                                                                           │
│  Response Generated:                                                     │
│  "B.Tech admission requires:                                            │
│   - 12th pass with Math and English                                     │
│   - Minimum 60% aggregate score                                         │
│   - Valid entrance exam score                                           │
│   See details: https://theaims.ac.in/admissions"                        │
│                                                                          │
│  Computation:                                                            │
│  - Input tokens: 1200                                                   │
│  - Output tokens: 85                                                    │
│  - Cost: $0.0035                                                        │
└──────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────────────┐
│         RESPONSE VALIDATION & CONFIDENCE SCORING (100ms)                │
│                                                                           │
│  1. Generate embedding of response                                      │
│  2. Compare with context chunk embeddings                              │
│  3. Calculate max semantic similarity:                                 │
│     max_similarity = 0.83 (between response and Chunk_001)            │
│  4. Confidence score = 0.83 > 0.70 threshold ✓ (confident)            │
│                                                                         │
│  If confidence < 0.70:                                                 │
│    Trigger FALLBACK: "I'm not certain. Contact admissions@..."        │
└──────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────────────┐
│       RECOMMENDATION ENGINE (50ms)                                       │
│                                                                           │
│  Session context: ["What are admission requirements?"]                 │
│  Theme extracted: ["Admissions", "Requirements", "12th"]               │
│                                                                         │
│  Top 3 related questions:                                              │
│  1. "What documents needed for admission?" (sim: 0.92)                │
│  2. "What's the placement rate?" (sim: 0.78)                         │
│  3. "Are scholarships available?" (sim: 0.75)                        │
│                                                                         │
│  Return top 3 recommendations                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────────────┐
│         USER SEES RESPONSE (Frontend Rendering)                          │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────┐            │
│  │ Chatbot: B.Tech admission requires:                     │            │
│  │ - 12th pass with Math and English                       │            │
│  │ - Minimum 60% aggregate score                           │            │
│  │ - Valid entrance exam score                             │            │
│  │                                                          │            │
│  │ Source: https://theaims.ac.in/admissions [LINK]        │            │
│  │                                                          │            │
│  │ Related Questions:                                       │            │
│  │ [ ] What documents needed for admission?               │            │
│  │ [ ] What's the placement rate?                         │            │
│  │ [ ] Are scholarships available?                        │            │
│  │                                                          │            │
│  │ [👍 Helpful]  [👎 Not helpful]  [💬 Talk to human]    │            │
│  └─────────────────────────────────────────────────────────┘            │
│                                                                          │
│  Total latency: ~3secs (target: <2s for better UX)                    │
└──────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────────────┐
│           ANALYTICS LOGGING (Asynchronous, ~10ms)                        │
│                                                                           │
│  Log in chat_events table:                                              │
│  {                                                                       │
│    "session_id": "550e8400-e29b-41d4-a716-446655440000",              │
│    "user_query": "What are B.Tech admission requirements?",            │
│    "retrieved_chunks": 5,                                              │
│    "llm_response": "[response text]",                                  │
│    "confidence_score": 0.83,                                           │
│    "latency_ms": 3100,                                                 │
│    "embedding_latency_ms": 100,                                        │
│    "retrieval_latency_ms": 50,                                         │
│    "llm_latency_ms": 1500,                                             │
│    "is_fallback": false,                                               │
│    "user_feedback": null,  (← User will provide this)                 │
│    "created_at": "2024-04-19T10:30:45.123Z"                          │
│  }                                                                      │
│                                                                         │
│  Analytics dashboard will aggregate this                               │
└──────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────────────┐
│           OPTIONAL: LEAD CAPTURE (If user interested)                   │
│                                                                           │
│  User clicks "Interested in this program?"                              │
│  Form appears:                                                          │
│  - First Name: John                                                    │
│  - Last Name: Doe                                                      │
│  - Email: john@example.com                                             │
│  - Phone: +91-9999999999                                               │
│  - Interested Programs: [B.Tech CS]                                    │
│  - Qualification: 12th pass                                            │
│  - State: Maharashtra                                                  │
│  - [ ] Consent to marketing emails                                     │
│                                                                          │
│  Click "Submit"                                                         │
│  ↓                                                                       │
│  POST /api/v1/leads                                                    │
└──────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────────────┐
│          LEAD PROCESSING & CRM SYNC (Asynchronous)                      │
│                                                                           │
│  1. Insert into PostgreSQL leads table:                                │
│     - Session ID linked to chat events                                │
│     - Calculate lead_score based on engagement                        │
│     - interaction_quality: "high" (10+ chat messages)                 │
│     - Retrieve full chat transcript, attach                           │
│                                                                         │
│  2. Queue Salesforce sync task (Celery + Redis):                      │
│     {                                                                   │
│       "task": "salesforce_sync",                                       │
│       "lead_id": "123e4567-e89b-12d3-a456-426614174000",            │
│       "priority": "high",                                              │
│       "retry_count": 0                                                 │
│     }                                                                   │
│                                                                         │
│  3. Wait for Salesforce sync worker to process:                       │
│     - Check for duplicate (query by email)                            │
│     - If exists: update existing Lead in SF                           │
│     - If new: create Lead in SF with:                                 │
│       * Name, Email, Phone                                            │
│       * Custom fields: interested_programs, lead_score, source        │
│     - Return SF Lead ID → store in DB (salesforce_id)                 │
│     - Update sync_status = 'synced'                                    │
│                                                                         │
│  4. If sync fails (SF API error):                                     │
│     - Retry with exponential backoff (5sec, 30sec, 5min)              │
│     - After 3 retries: alert admissions team via email                │
│     - Store error in sf_sync_error field                              │
│                                                                         │
│  Lead now visible in Salesforce dashboard                             │
│  Admissions team can:                                                  │
│    - Check lead score (prioritize high-score leads)                  │
│    - Read chat transcript (know what they asked)                     │
│    - Track conversion (when they apply/enroll)                       │
└──────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────────────┐
│              CONTINUOUS MONITORING & ALERTS                             │
│                                                                           │
│  Prometheus scrapes metrics every 15 seconds:                          │
│  - chat_requests_total{status="success"} = 1250                        │
│  - chat_latency_seconds{quantile="0.95"} = 2.5                        │
│  - fallback_rate = 10%                                                 │
│  - leads_captured_total = 85                                           │
│  - salesforce_sync_failures = 2                                        │
│                                                                          │
│  Alert Rules:                                                           │
│  - IF avg_latency > 3s for 5 minutes → Slack alert                   │
│  - IF fallback_rate > 20% → Email admins                              │
│  - IF SF sync failures > 5 → Page on-call engineer                    │
│  - IF 4xx errors > 100 → Investigate malicious traffic               │
└──────────────────────────────────────────────────────────────────────────┘
```

### Key Timing Breakdown:
```
Query → Embedding:    ~100ms   (OpenAI API)
Embedding → Retrieval: ~50ms   (pgvector IVFFlat)
LLM Processing:      ~1500ms   (OpenAI GPT-3.5)
Validation:           ~100ms   (Embedding comparison)
Total P50:           ~1750ms
Total P95:           ~2500ms
Target:              <2000ms
```

---

## 7. FAILURE & EDGE CASES

### Critical Failure Scenarios:

| Failure Mode | Impact | Probability | Mitigation |
|-------------|--------|-------------|-----------|
| **Website Offline** | Scraper returns 0 docs daily | Low (if AIMS reliable) | Keep 30-day doc history; serve stale results with warning |
| **Scraper Crashes** | Knowledge base becomes stale | Medium | APScheduler restart logic; alert on 24hr no update; manual trigger endpoint |
| **Embedding API Down (OpenAI)** | New queries can't be embedded | Low (SLA 99.9%) | Cache old embeddings; queue queries in Redis; process when API back |
| **Vector DB Corrupted** | Retrieval fails for all queries | Very Low | PostgreSQL WAL backups; daily exports to S3; test restore weekly |
| **LLM Hallucination** | Chatbot gives false admissions info | **HIGH** | Strict prompt guardrails; confidence threshold (0.7); always require citations; random sampling of responses for QA |
| **Prompt Injection Attack** | Attacker manipulates LLM via chat | **HIGH** | Input sanitization; limit query length; detect suspicious patterns (SQL, escape quotes); rate limiting |
| **Rate Limit Hit** | API calls rejected, chatbot slow | Medium | Implement queue; retry with backoff; fallback to cached responses |
| **Salesforce Sync Failure** | Leads not saved to CRM | Medium | Async queue with retry; dual-write pattern; periodic reconciliation |
| **Data Privacy Breach** | Student emails/phone exposed | **CRITICAL** | Encrypt at rest (AES-256); TLS for transmission; minimal retention; audit logging |
| **Session ID Collision** | User sees another user's chat | Extremely Rare | Use UUID v4 (128 bits); collision probability ~1 in 5.3×10^36 |
| **No Results Found** | User gets escalation every time for valid question | Medium | Re-tune chunking + embeddings; analyze queries → add missing content scraping; improve prompt |
| **Token Overflow** | Prompt exceeds 4K token limit | Low (with 5-chunk retrieval) | Implement token counting; trim oldest chunks if needed; dynamic chunk selection |
| **Concurrent User Spike** | API times out during surge | Medium | Auto-scaling on CPU >70%; implement queue; cache common questions |
| **Database Connection Pool Exhausted** | "Too many connections" error | Low | Set max_connections intelligently; use connection pooling (PgBouncer); monitor pool usage |
| **Salesforce Auth Token Expired** | CRM sync silently fails | Medium | Use OAuth refresh tokens; validate before each sync; automatic re-auth |

### Edge Cases:

```python
# Edge Case 1: Empty or whitespace-only query
if not user_query.strip() or len(user_query.strip()) < 3:
    return ChatResponse(
        response="Please ask a specific question.",
        is_fallback=True
    )

# Edge Case 2: Question in non-English language
query = detect_language_and_translate(user_query)
if detected_lang != 'en':
    user_query = translate_to_english(user_query)
    response_lang = detected_lang
    # Translate response back before sending

# Edge Case 3: Duplicate lead capture in same session
existing_lead = db.query(
    "SELECT id FROM leads WHERE email = $1 AND session_id = $2",
    email, session_id
)
if existing_lead:
    return {"status": "duplicate", "message": "Lead already captured"}

# Edge Case 4: Extremely long chat history (>100K tokens)
messages = get_last_n_messages(session_id, limit=5)  # Keep only recent
session_embedding = average_embeddings([embed(m) for m in messages])

# Edge Case 5: User clicks "Mark unhelpful" on response with 0.95 confidence
# → Trigger manual review queue; update training data
if user_feedback == 'not_helpful' and confidence_score > 0.9:
    queue_for_manual_review(chat_event)

# Edge Case 6: Salesforce returns duplicate lead ID
sf_leads = search_salesforce_leads(email=lead_email)
if len(sf_leads) > 1:
    # Pick most recent and log warning
    selected_lead = max(sf_leads, key=lambda x: x['created_at'])
    logger.warning(f"Multiple SF leads found for {email}")

# Edge Case 7: Vector DB returns 0 results but retrieval succeeds (?)
# This shouldn't happen, but handle gracefully
if not chunks and retrieval_status == 'ok':
    # Fallback
    pass

# Edge Case 8: User asks personal/sensitive question
sensitive_patterns = [
    r"credit card|ssn|national id|password",
    r"personal finance|bank account"
]
if any(re.search(p, user_query, re.I) for p in sensitive_patterns):
    return ChatResponse(
        response="I can't help with sensitive personal information. "
                 "Contact admissions directly.",
        is_fallback=True
    )

# Edge Case 9: Network timeout on LLM call mid-stream
try:
    async with asyncio.timeout(5):  # 5-second timeout
        response = await openai.ChatCompletion.acreate(...)
except asyncio.TimeoutError:
    # Return best-effort response from retrieved chunks
    return ChatResponse(
        response="Response taking longer than usual. "
                 "Here's what I found:\n" + format_chunks(chunks),
        is_fallback=True,
        fallback_reason="timeout"
    )
```

---

## 8. SCALING STRATEGY

### Current State (MVP):
```
Assumptions:
- 100 concurrent users
- ~500 requests/day
- ~50 leads/day
- ~5GB of data (500 docs × 10MB avg)
```

### Phase 1 → Phase 2 Scaling (1000 concurrent, 5K req/day):

**Database:**
```
MVP: Single RDS PostgreSQL t3.micro
  ├─ Single instance (single point of failure)
  ├─ Storage: 50GB
  ├─ IOPS: 1000
  └─ Cost: $25/month

Scale: RDS t3.small + read replica
  ├─ Primary: t3.small (write)
  ├─ Read replica: t3.micro (analytics queries)
  ├─ Automated backups: Daily
  ├─ Multi-AZ failover
  └─ Cost: $75/month
```

**Vector Database:**
```
MVP: PostgreSQL pgvector
  └─ No scaling issues yet (10K vectors = tiny)

Scale to ~100K vectors:
  Option 1: Pinecone (Managed)
    ├─ Pro: Infinitely scalable, low maintenance
    ├─ Cost: $25-100/month (depends on vector count)
    ├─ Migration: 2 days development
    └─ Recommendation: Switch here
  
  Option 2: Self-hosted Milvus
    ├─ Pro: Full control, cheaper at scale
    ├─ Cost: $50/month (EC2 t3.medium)
    ├─ Maintenance burden: Moderate
    └─ Recommendation: For >1M vectors
```

**API Layer:**
```
MVP: Single EC2 t3.medium (1 instance)
  ├─ ~500 req/s capacity (with caching)
  ├─ CPU: 2 vCPU, Memory: 4GB
  └─ Cost: $30/month

Scale: Load-balanced multi-instance
  ├─ 2-3 EC2 t3.medium instances (auto-scale 2→4)
  ├─ Elastic Load Balancer (NLB for low latency)
  ├─ CloudWatch auto-scaling rules:
  │   ├─ Scale up if CPU > 70% for 2min
  │   └─ Scale down if CPU < 30% for 10min
  ├─ Caching layer (CloudFront + Redis)
  └─ Cost: $100-150/month
```

**Caching Strategy:**
```
Layer 1: Frontend Cache (CloudFront)
  ├─ Cache response for same query: 1 hour
  ├─ Hit rate: ~30% (repeated questions)
  ├─ Reduce: LLM calls
  └─ Cost savings: ~20% of OpenAI bill

Layer 2: Redis Cache (Backend)
  ├─ Cache embeddings: 24 hours
  ├─ Cache common retrievals: 6 hours
  ├─ Hit rate: ~40%
  ├─ Reduce: OpenAI Embedding API calls
  └─ Cost: $15/month (elasticache.t3.micro)

Layer 3: Database Query Cache
  ├─ Prepared statements
  ├─ Connection pooling (PgBouncer)
  └─ Reduce: DB load 40%
```

**Embedding Generation at Scale:**
```
MVP: On-demand embedding
  └─ Time: 1536 chunks × 0.1s = 153 seconds (batch)
  
Scale: Batch daily embedding
  ├─ Process new chunks in batch every day
  ├─ Time: 30 chunks/batch × 10 calls = 3 seconds
  ├─ Cost: Same (but off-peak)
  └─ Saves: Nothing but improves reliability
  
Alternative: Fine-tuned model
  ├─ Reduce to 768 dimensions
  ├─ Cost: -50% embedding cost
  ├─ Trade-off: Slightly worse retrieval quality
  └─ Training time: 2 weeks
```

### Cost Breakdown Scaling:

| Component | MVP | 1K Users | 10K Users | 100K Users |
|-----------|-----|----------|-----------|------------|
| **EC2/Compute** | $30 | $120 | $400 | $1200 |
| **RDS PostgreSQL** | $25 | $75 | $200 | $500 |
| **Vector DB** | $0 | $25 | $100 | $500 |
| **Redis Cache** | $0 | $15 | $50 | $150 |
| **OpenAI Embeddings** | $10 | $50 | $200 | $1000 |
| **OpenAI LLM (GPT-3.5)** | $50 | $300 | $1500 | $7500 |
| **Salesforce License** | $75 | $150 | $300 | $1000 |
| **CloudFront/CDN** | $10 | $30 | $100 | $500 |
| **Monitoring (Datadog alt)** | $15 | $30 | $50 | $200 |
| **Misc (storage, etc)** | $20 | $50 | $100 | $300 |
| **TOTAL / Month** | **$235** | **$825** | **$3000** | **$11,350** |

### Bottleneck Analysis:

**1. LLM Latency (Bottleneck)**
```
Current: ~1500ms per LLM call
Problem: Can't parallelize (sequential processing)
Solution A: Cache common responses
  └─ Reduce LLM calls 30% → save $150/month
Solution B: Use cheaper model (Llama 2)
  └─ But requires GPU ($200+ month) + maintenance
Solution C: Request batching
  └─ Hold queries 5 seconds → batch with others
  └─ Reduces concurrent calls but adds latency
```

**2. Database Connections**
```
Current: Single DB, single connection pool
At 1K users: ~100 concurrent connections
At 10K users: ~1000 concurrent connections (exceeds default 100)
Solution:
  - Use PgBouncer connection pooling
  - Set max_connections = 200 (RDS t3.medium supports ~180)
  - Implement circuit breaker (queue requests if pool exhausted)
```

**3. Vector Search Latency**
```
Current: pgvector + IVFFlat index ≈50ms for 2K vectors
At 100K vectors: ≈200-300ms (gets slower)
At 1M vectors: ≈500ms+ (unacceptable)
Solution:
  - Migrate to Pinecone (constant ~50ms regardless of size)
  - Or: Milvus with GPU-accelerated indexing
```

**4. Concurrent API Requests**
```
Current: Single t3.medium = ~500 req/s capacity
At 1000 concurrent users: Need 2-3 instances
Scaling: Auto-scale 2→4 instances based on CPU
Cost: Linear scaling ($30 × N instances)
```

### Optimization Priorities (ROI):

1. **Query Response Caching** (Week 10)
   - Effort: 2 days
   - Savings: $150/month (20% LLM reduction)
   - ROI: Immediate

2. **Vector DB Migration to Pinecone** (Week 15)
   - Effort: 1 week
   - Benefit: Infinite scaling without complexity
   - Cost: +$25/month (but saves maintenance)
   - ROI: High (simplicity + reliability)

3. **Cheaper Embedding Model** (Week 20)
   - Effort: 3 days (re-embed all docs)
   - Savings: $50/month (switch to text-embedding-3-small)
   - Trade-off: Slightly lower accuracy
   - ROI: High (validated on retrieval metrics)

4. **LLM Model Tuning** (Week 25)
   - Effort: 2 weeks (collect data, fine-tune)
   - Savings: $300/month (fine-tuned smaller model)
   - Trade-off: Domain-specific, lower flexibility
   - ROI: Very high if successful

---

## 9. SECURITY & COMPLIANCE

### Data Security:

```python
# 1. ENCRYPTION AT REST
# RDS PostgreSQL with encryption enabled
resource "aws_db_instance" "main" {
  storage_encrypted = true
  kms_key_id = aws_kms_key.rds.arn
}

# S3 bucket with encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "docs" {
  bucket = aws_s3_bucket.docs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# 2. ENCRYPTION IN TRANSIT
# Enforce HTTPS / TLS 1.3
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

# 3. SECRETS MANAGEMENT
# Use AWS Secrets Manager (rotate every 30 days)
import boto3
secrets_manager = boto3.client('secretsmanager')

openai_key = secrets_manager.get_secret_value(
    SecretId='prod/openai/api-key'
)['SecretString']

# 4. DATABASE CREDENTIALS
# Never hardcode. Use environment variables + IAM roles
# EC2 instance has IAM role → access RDS directly (no password)
class DatabaseConfig:
    DATABASE_URL = environ.get('DATABASE_URL')
    # Validation: Must start with postgresql://
    assert DATABASE_URL.startswith('postgresql://'), "Invalid DB URL"
```

### API Security:

```python
# 1. RATE LIMITING
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.post("/chat")
@limiter.limit("10/minute")  # Max 10 queries per minute per IP
async def chat(request):
    pass

@router.post("/leads")
@limiter.limit("5/minute")  # Stricter for lead capture
async def capture_lead():
    pass

# 2. AUTHENTICATION (API Key for frontend)
from fastapi.security import APIKeyHeader
api_key_header = APIKeyHeader(name="X-API-Key")

@router.post("/chat")
async def chat(api_key: str = Depends(api_key_header)):
    # Verify API key
    if not verify_api_key(api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
    pass

# 3. CORS POLICY
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://theaims.ac.in", "https://www.theaims.ac.in"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
    max_age=3600
)

# 4. INPUT VALIDATION & SANITIZATION
from pydantic import BaseModel, validator

class ChatRequest(BaseModel):
    query: str
    session_id: str
    
    @validator('query')
    def validate_query(cls, v):
        # Limit length
        assert len(v) <= 1000, "Query too long"
        
        # Check for prompt injection patterns
        injection_patterns = [
            r'forget.*instructions',
            r'ignore.*context',
            r'system.*prompt',
            r'reveal.*system'
        ]
        if any(re.search(p, v, re.I) for p in injection_patterns):
            raise ValueError("Suspicious query pattern detected")
        
        return v.strip()

# 5. CSRF PROTECTION
@app.middleware("http")
async def csrf_middleware(request, call_next):
    if request.method in ["POST", "PUT", "DELETE"]:
        # Verify CSRF token (for form submissions)
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token or not verify_csrf_token(csrf_token):
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF validation failed"}
            )
    return await call_next(request)

# 6. LOGGING FOR AUDIT TRAIL
logger.info(
    "Lead captured",
    extra={
        "email": lead_email,  # Don't log full email in logs
        "session_id": session_id,
        "timestamp": datetime.now(),
        "ip_address": request.client.host
    }
)
```

### Prompt Injection Prevention:

```python
# STRICT PROMPT TEMPLATE (Defense #1: Isolation)
SAFE_PROMPT_TEMPLATE = """
You are a college admissions chatbot for AIMS College.

[RETRIEVED CONTEXT STARTS HERE]
{context}
[RETRIEVED CONTEXT ENDS HERE]

User Question: {user_query}

IMPORTANT RULES:
1. ONLY answer based on the context above
2. If the answer is NOT in the context, say "I don't have that information"
3. NEVER make up or assume information
4. ALWAYS include source URLs from the context
5. Be concise (max 3 sentences)

Response:
"""

# Input Sanitization (Defense #2: Input filtering)
def sanitize_user_input(query: str) -> str:
    # Remove dangerous patterns
    dangerous_keywords = [
        'system_prompt', 'context_override', 'forget_instructions',
        'execute_code', 'curl_command', 'bash_script'
    ]
    
    for keyword in dangerous_keywords:
        if keyword.lower() in query.lower():
            raise ValueError(f"Query contains forbidden keyword: {keyword}")
    
    # Limit length
    if len(query) > 1000:
        raise ValueError("Query exceeds maximum length")
    
    # Remove common SQL injection patterns
    sql_patterns = [r"';\\s*DROP", r"';\\s*DELETE", r"';\\s*UPDATE"]
    if any(re.search(p, query, re.I) for p in sql_patterns):
        raise ValueError("Suspicious pattern detected")
    
    return query.strip()

# Response Validation (Defense #3: Output filtering)
def validate_llm_response(response: str, context_chunks: list) -> float:
    """
    Validate that response is grounded in context.
    Returns confidence score 0-1.
    """
    # Check if response contains hallucinations
    response_embedding = get_embedding(response)
    
    max_similarity = 0
    for chunk in context_chunks:
        chunk_embedding = get_embedding(chunk['text'])
        similarity = cosine_similarity(response_embedding, chunk_embedding)
        max_similarity = max(max_similarity, similarity)
    
    # If response is too dissimilar from context, it's likely a hallucination
    if max_similarity < 0.7:
        return 0.5  # Low confidence
    
    return max_similarity

# Fallback on Low Confidence (Defense #4: Graceful degradation)
def generate_safe_fallback(query: str) -> str:
    """Return safe response when confidence is low"""
    return (
        f"I couldn't find a confident answer to your question about '{query}'. "
        f"Please contact our admissions team for accurate information:\n"
        f"📧  admissions@theaims.ac.in\n"
        f"📞  +91-XXXX-XXXX-00"
    )
```

### Data Privacy & Compliance:

```python
# 1. DATA RETENTION POLICY
# Delete data older than 90 days
async def cleanup_old_data():
    # Delete old chat events
    await db.execute("""
        DELETE FROM chat_events 
        WHERE created_at < NOW() - INTERVAL '90 days'
    """)
    
    # Delete analytics events
    await db.execute("""
        DELETE FROM analytics_events 
        WHERE created_at < NOW() - INTERVAL '180 days'
    """)
    
    # Archive old leads (don't delete, but move to archive table)
    await db.execute("""
        INSERT INTO leads_archive 
        SELECT * FROM leads 
        WHERE created_at < NOW() - INTERVAL '1 year'
    """)
    
    # Run daily via APScheduler at 2 AM IST
    scheduler.add_job(
        cleanup_old_data,
        trigger='cron',
        hour=2,
        minute=0,
        timezone='Asia/Kolkata'
    )

# 2. CONSENT MANAGEMENT
class LeadData(BaseModel):
    first_name: str
    email: str
    consent_marketing: bool  # Explicit opt-in
    consent_terms: bool      # Must accept terms

@router.post("/leads")
async def capture_lead(lead_data: LeadData):
    if not lead_data.consent_terms:
        raise HTTPException(status_code=400, detail="Must accept terms")
    
    # Store consent timestamp for audit
    lead_id = await db.execute("""
        INSERT INTO leads (... , consent_marketing, consent_timestamp)
        VALUES (..., $1, NOW())
    """, lead_data.consent_marketing)

# 3. RIGHT TO BE FORGOTTEN (GDPR)
@router.delete("/user/{session_id}")
async def delete_user_data(session_id: str, request: Request):
    # Verify user (could be verification email, etc.)
    
    # Delete all data for this session
    await db.execute("DELETE FROM chat_events WHERE session_id = $1", session_id)
    await db.execute("DELETE FROM leads WHERE session_id = $1", session_id)
    await db.execute("DELETE FROM analytics_events WHERE session_id = $1", session_id)
    
    # Log deletion for compliance
    logger.info(f"User data deleted for session {session_id}")

# 4. PRIVACY POLICY
# Must display on website:
# - What data we collect (name, email, chat history)
# - Why we collect it (lead generation, analytics)
# - How long we keep it (90 days for chat, 1 year for leads)
# - Who has access (admissions team via Salesforce)
# - How to request deletion

# 5. DATA PROTECTION OFFICER (DPO)
# Assign responsibility:
DPO_EMAIL = "dpo@theaims.ac.in"
# Data breach notification within 72 hours (GDPR)
```

### India-Specific Compliance (DPDP Act):

```python
# Digital Personal Data Protection (DPDP) Act, 2023
# Effective: Sept 2023

# 1. PURPOSE LIMITATION
# Only use data for admitted purpose (lead generation, admissions)
# Can't sell/share data without explicit consent

# 2. LEGITIMATE INTEREST
eligibility_criteria = [
    "Lead is interested in admissions",
    "Data needed to process inquiry"
]

# 3. DATA MINIMIZATION
# Collect only necessary fields
required_fields = ['email', 'phone', 'interested_program']
optional_fields = ['first_name', 'state', 'class_12_percentage']

# 4. STORAGE LIMITATION
store_for_days = 365  # 1 year max (unless legal requirement)

# 5. CONSENT & WITHDRAWAL
lead.update(
    consent_at=datetime.now(),
    consent_withdrawn_at=None
)

# User can withdraw anytime → DELETE data immediately
async def withdraw_consent(email: str):
    lead = await db.fetch_one(
        "SELECT id FROM leads WHERE email = $1", email
    )
    await db.execute("DELETE FROM leads WHERE id = $1", lead['id'])
    return {"status": "withdrawn"}
```

---

## 10. FINAL VERDICT

### Is This System Realistically Buildable?

**YES, but with major caveats:**

✅ **What's Achievable:**
- RAG-based chatbot with LLM ← Well-defined, battle-tested stack
- Web scraping + knowledge base ← Straightforward but maintenance-heavy
- Salesforce CRM integration ← Standard OAuth, doable
- Analytics dashboard ← Simple aggregations
- Multi-thousand user capacity ← Scalable architecture designed

❌ **What's Hard:**
1. **Production-grade accuracy** (preventing hallucinations)
2. **Keeping scraped data fresh** (constant website changes)
3. **Maintaining low latency** (LLM calls are slow, can't parallelize)
4. **Cost management** (OpenAI bills add up with volume)
5. **Team scalability** (debugging production LLM behavior is hard)

---

### The Hardest Parts (Ranked by Risk):

**Tier 1 - CRITICAL (Can break entire system):**

```
1. LLM Hallucinations
   Problem: GPT-3.5-turbo will occasionally make up facts
   Example: "Only 50 students admitted per year" (when it's 500)
   Impact: Students get wrong admissions info, blame college
   
   Mitigation (hard):
   - Strict confidence scoring (>0.8 only)
   - Manual review of <confidence responses
   - A/B test prompt templates
   - Collect user feedback loop → retrain
   
   Cost: 2-3 engineers × 3 months of tuning
   ─────────────────────────────────────────

2. Salesforce Data Sync at Scale
   Problem: CRM integrations are fragile
   - SF API rate limits (10K calls/24hrs)
   - Duplicate detection (same person, multiple emails?)
   - Update conflicts (user submits twice in 1 hour)
   
   Mitigation:
   - Implement comprehensive deduplication logic
   - Queue-based batch sync (nightly, not immediate)
   - Retry logic with exponential backoff
   - Reconciliation reports (daily, compare counts)
   
   Cost: 1 engineer × 4 weeks + ongoing maintenance
   ─────────────────────────────────────────

3. Web Scraping Fragility
   Problem: College website can change structure anytime
   - New page formats break CSS selectors
   - JavaScript rendering fails
   - PDFs don't extract properly
   
   Result: Knowledge base becomes stale
   
   Mitigation:
   - Alerts on scraping failures (no docs scraped in 24hrs)
   - Manual backup sources (PDF brochures from college)
   - Regular monitoring of scraped content quality
   - Support ticket: "Chatbot doesn't know about [topic]"
   
   Cost: 0.5 engineer × ongoing (weekly fixes)
```

**Tier 2 - HIGH RISK (Causes degradation):**

```
4. Latency (User frustration)
   Current: ~2-3 seconds per response (chain: Embed → Retrieve → LLM)
   Problem: Can't parallelize LLM (sequential dependency)
   
   Solutions:
   - Cache common questions (will handle maybe 30%)
   - Use cheaper/faster model (GPT-3.5 vs GPT-4)
   - Pre-compute popular responses
   
   Trade-off: Lower quality responses
   ─────────────────────────────────────────

5. Cost Explosion
   10K queries/month → $500+ just on LLM API
   100K queries/month → $5K+
   
   Problem: Unpredictable cost at scale
   
   Mitigation:
   - Implement aggressive caching
   - Use cheaper embedding model
   - Set up cost alerts in AWS
   - Consider fine-tuned smaller model
   ─────────────────────────────────────────

6. Keeping Feature Parity
   As college updates programs, adds new departments
   Chatbot outdated → leads with wrong information
   
   Mitigation:
   - Daily scraping (but can only detect changes, not understand intent)
   - College admin panel? (extra work)
   - Quarterly manual knowledge base review
```

**Tier 3 - MEDIUM RISK (Operational issues):**

```
7. Debugging Production Issues
   - "Chatbot says campus has 50K students (actual: 5K)"
   - Which component failed? Scraper? LLM? Prompt?
   - Need detailed tracing + logging
   
8. Supporting Multiple Programs
   - Different majors need different FAQ data
   - Recommendation engine needs to know program relationships
   - Analytics should slice by program

9. Licensing & Vendor Lock-in
   - OpenAI API changes → must adapt
   - Salesforce updates → compatibility issues
   - No off-the-shelf solutions for this exact problem
```

---

### What Should You Focus On First?

**Month 1 (Foundation):**
```
Priority 1: Web Scraping (CRITICAL)
  └─ You can't build anything without data
  ├─ Start with BeautifulSoup (simple, fast)
  ├─ Scrape: Homepage, Admissions page, Programs, Fees
  └─ Validate: Manual QA that content looks right

Priority 2: Vector DB + Retrieval
  └─ PostgreSQL + pgvector (free, sufficient for MVP)
  ├─ Test: Can you retrieve relevant chunks?
  └─ Measure: Precision & recall of retrieval

Priority 3: Basic LLM Integration
  └─ GPT-3.5-turbo (cheapest, "good enough")
  ├─ Test: Does LLM answer based on chunks?
  └─ Monitor: Spot-check responses for accuracy
```

**Month 2 (MVP Working):**
```
Priority 4: Frontend Widget
  └─ React component that talks to API
  ├─ Deploy on test domain
  └─ User testing with real students

Priority 5: Lead Capture
  └─ Form + Salesforce sync
  ├─ Test: Can you create leads in SF?
  └─ Validate: Leads appear in admissions dashboard

Priority 6: Basic Analytics
  └─ Dashboard showing queries/day, fallback rate
  ├─ Monitor: Is chatbot working?
  └─ Alert: When latency > 3s or error rate > 5%
```

**Month 3 (Polish & Launch):**
```
Priority 7: Production Hardening
  └─ Security (rate limiting, input validation)
  ├─ Monitoring & alerting
  └─ Error handling for all edge cases

Priority 8: Performance Optimization
  └─ Caching layer (CloudFront)
  ├─ Load testing (can it handle 100 users?)
  └─ Cost optimization (embedding caching)

Priority 9: QA & Accuracy Testing
  └─ Create test set: 100 questions + expected answers
  ├─ Measure: % of correct/confident responses
  └─ Iterate: Tune prompts based on failures
```

**Focus on: ACCURACY FIRST, not features**
- Users will forgive slow chatbot
- Users will NOT forgive wrong information
- Test extensively before launch
- Have support team review escalated queries

---

### Technical Debt to Expect:

1. **Prompt Engineering** (~60 hours)
   - Default templates don't work for every domain
   - Will need 10+ iterations to get right
   
2. **Deduplication Logic** (~40 hours)
   - Detecting duplicate leads (same person, diff emails)
   - Deduplicating content across pages
   
3. **Error Handling** (~80 hours)
   - Each failure mode needs specific recovery logic
   - Not glamorous but critical for production
   
4. **Testing & QA** (~100 hours)
   - Manual testing of use cases
   - Load testing
   - Security testing

**Total: ~280 hours (7 weeks) for one engineer** → Hire 2-3 engineers

---

### Reality Check: Timeline

**Optimistic (everything goes smoothly):**
- Month 1: Backend MVP
- Month 2: Frontend + CRM
- Month 3: Production launch
- **Total: 3 months**

**Realistic (expect issues):**
- Weeks 1-4: Scraping, vector DB ← Debugging website weirdness
- Weeks 5-8: LLM + frontend ← Prompt tuning takes forever
- Weeks 9-12: CRM + launch ← Data sync issues
- **Total: 3-4 months**, with 2 engineers

**Pessimistic (things break):**
- Vector retrieval returns wrong results → re-chunk entire DB
- Salesforce sync has duplicates → debug deduplication for 2 weeks
- Hallucination rate unacceptable → hire prompt engineering consultant
- **Total: 5-6 months**, with full team

---

### Budget Estimate (MVP to Production):

```
Personnel (3-4 engineers × 4 months):
  Senior backend engineer:    $60K (16 weeks)
  Backend engineer #2:        $50K (16 weeks)
  Frontend engineer:          $45K (16 weeks)
  Devops/Infrastructure:      $40K (8 weeks)
  ────────────────────────────────────
  Subtotal:                   ~$195K

Infrastructure & Services (Month 1-4):
  AWS (EC2, RDS, S3):        $400
  OpenAI API tokens:         $1K
  Salesforce licenses:       $300
  Pinecone (vector DB):      $100
  Tools (GitHub, Slack, etc): $200
  ────────────────────────────────────
  Subtotal:                  ~$2K/month × 4 = $8K

Operational (ongoing):
  Infrastructure:            $500/month
  LLM API calls:            $300/month (10K queries)
  Salesforce:               $300/month (3 seats)
  Monitoring/logging:       $100/month
  ────────────────────────────────────
  Subtotal:                 ~$1200/month

TOTAL INVESTMENT:           ~$203K (dev) + $1200/month (ops)
```

This is **medium-scale startup** budget, not simple project.

---

### Final Recommendation:

✅ **BUILD IT IF:**
- You have committed team (2-3+ engineers, 4+ months)
- Budget for infrastructure + API costs (~$1.5K/month)
- Leadership expects iterative improvement (not perfection day 1)
- Admissions team ready to review/refine prompts
- Website relatively stable (not changing daily)

❌ **DON'T BUILD IF:**
- Expecting one engineer to lead this
- Expecting chatbot to be 100% accurate with zero tuning
- Budget constraints tight (API costs add up FAST)
- Expecting launch in <8 weeks
- No support for ongoing maintenance (website changes)

---

### What I'd Do First (Your Action Items):

**Week 1:**
```
□ Audit college website
  - How many pages?
  - JavaScript required? (JS = harder to scrape)
  - Any PDFs or special content?
  - Structure consistent across pages?

□ Choose tech stack
  - Embedding model: OpenAI vs self-hosted?
  - LLM: GPT-4 (better) vs GPT-3.5-turbo (cheaper)?
  - Vector DB: Pinecone (easy) vs pgvector (free)?

□ Setup infrastructure
  - AWS account + IAM roles
  - GitHub repo with basic structure
  - Local development environment
```

**Week 2-3:**
```
□ Build scraper
  - Pick BeautifulSoup + Selenium
  - Test on 10 key pages
  - Verify no content loss (manual spot-check)

□ Build embeddings pipeline
  - OpenAI Embeddings API
  - Redis cache
  - Batch processing

□ Build vector search
  - PostgreSQL + pgvector
  - Test retrieval quality
```

**Week 4:**
```
□ Build LLM integration
  - Prompt template
  - Confidence scoring
  - Test on 50 generated queries

□ Quality assurance
  - Does chatbot give correct answers?
  - Any hallucinations?
  - Iterate on prompts
```

Then: Frontend, CRM, Launch.

---

## CONCLUSION

**Your college chatbot system is REALISTICALLY BUILDABLE in 3-4 months with the right team**, but it's no small project:

1. **Not a weekend hack** - Real architecture, real complexity
2. **Not a simple LLM wrapper** - RAG requires careful data engineering
3. **Not maintenance-free** - Scraping breaks, prompts need tuning, costs grow
4. **Definitely worth it** - Engaged students, better lead quality, 24/7 support

**Start with MVP accuracy over features.** Once chatbot is reliably correct, then add recommendations, analytics, scaling.

**Biggest risks:** Hallucinations, scraping fragility, latency, cost explosion.
**Biggest opportunities:** High-quality leads, student engagement, competitive advantage.

**You've got this. But hire the right people, plan for 4 months, and expect to iterate.** 🚀

---

**END OF SYSTEM ARCHITECTURE DOCUMENT**

