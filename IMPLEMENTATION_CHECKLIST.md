# IMPLEMENTATION CHECKLIST & MILESTONES

## PHASE 1: MVP (Weeks 1-10)

### Week 1-2: Infrastructure Setup

**Infrastructure:**
- [ ] AWS Account setup + IAM roles configured
- [ ] VPC, subnets, security groups configured
- [ ] RDS PostgreSQL instance provisioned (db.t3.micro)
- [ ] S3 bucket for document storage + public access blocked
- [ ] ECR repository for Docker images
- [ ] CloudWatch created for monitoring

**Development:**
- [ ] GitHub repo initialized with proper structure
- [ ] Docker + Docker Compose setup for local development
- [ ] Environment variables template (.env.example) created
- [ ] CI/CD pipeline skeleton (GitHub Actions)
- [ ] Logging infrastructure configured (stdout + structured logs)

**Deliverable:** 
- ✅ Backend and frontend can be developed locally
- ✅ Code can be deployed to AWS via CI/CD
- ✅ Teams can understand project structure

---

### Week 2-3: Web Scraping

**Architecture:**
- [ ] Analyze college website structure (manual audit)
- [ ] Create scraper whitelist of URLs to scrape
- [ ] Decide: BeautifulSoup vs Selenium (test both on JS-heavy pages)

**Implementation:**
- [ ] Build base scraper (BeautifulSoup for HTML parsing)
- [ ] Add Selenium for JavaScript-rendered content
- [ ] Implement content deduplication (SHA-256 hashing)
- [ ] Error handling: retry on 5xx, log failures
- [ ] Schedule with APScheduler (daily at 2 AM UTC)

**Testing:**
- [ ] Manual scrape of 10 key pages
- [ ] Verify content is correct (spot-check)
- [ ] Verify no duplicate records in DB
- [ ] Test scraper failure recovery

**Deliverable:**
- ✅ ~500 documents scraped daily
- ✅ Zero duplicate content
- ✅ Automatic scheduling working
- ✅ Failure alerts functional

---

### Week 3-4: Data Preprocessing & Chunking

**Implementation:**
- [ ] HTML cleaning (BeautifulSoup-based)
- [ ] Text normalization (lowercase, whitespace, special chars)
- [ ] Semantic chunking (256-512 tokens, 50% overlap)
- [ ] Metadata extraction (heading hierarchy, source URL)
- [ ] Implement token counting (tiktoken library)

**Database:**
- [ ] Create documents, chunks tables
- [ ] Index chunk_document_id for queries
- [ ] Migration script: scraped docs → chunks

**Testing:**
- [ ] Sample 10 documents → chunks
- [ ] Verify chunk size distribution (should be ~300 tokens avg)
- [ ] Verify no information loss (concatenate chunks = original)
- [ ] Test edge cases: PDFs, tables, code blocks

**Deliverable:**
- ✅ 500 docs → ~2000 chunks
- ✅ Chunks are semantically coherent
- ✅ Metadata correctly extracted

---

### Week 4-5: Embedding Generation & Vector DB

**Embedding Service:**
- [ ] Integrate OpenAI text-embedding-3-small API
- [ ] Batch processing (100 chunks per request)
- [ ] Implement caching (Redis for embeddings)
- [ ] Error handling: retry on API failures

**Vector Database:**
- [ ] Create embeddings table (PostgreSQL pgvector)
- [ ] Build IVFFlat index for fast similarity search
- [ ] Query optimization: test with different list sizes

**Testing:**
- [ ] Embed all 2000 chunks
- [ ] Query with test embeddings (should return relevant chunks)
- [ ] Measure retrieval latency (<100ms target)
- [ ] Measure vector similarity distributi (should be bell-curve)

**Deliverable:**
- ✅ 2000 vectors in pgvector
- ✅ Vector search <100ms
- ✅ Similarity search returning correct results
- ✅ Cost tracking (should be <$2 for MVP)

---

### Week 5-6: LLM Integration & Guardrails

**LLM Service:**
- [ ] Integrate OpenAI GPT-3.5-turbo API
- [ ] Implement prompt template with context
- [ ] Add token counting (don't exceed limits)
- [ ] Error handling: timeout (5s limit), rate limits, API failures

**Confidence Scoring:**
- [ ] Generate embedding of LLM response
- [ ] Compare with context chunk embeddings (cosine similarity)
- [ ] Threshold: confidence > 0.7 for confident responses
- [ ] Log confidence scores for analysis

**Fallback Logic:**
- [ ] No relevant chunks (retrieval < 0.5 similarity)
- [ ] Low confidence (< 0.7)
- [ ] LLM timeout (> 5 seconds)
- [ ] Generate fallback response with contact info

**Testing:**
- [ ] Create test set: 50 questions + expected answers
- [ ] Manual QA: Does chatbot answer correctly?
- [ ] Measure: Hallucination rate, confidence distribution
- [ ] Iterate: Refine prompt based on failures

**Deliverable:**
- ✅ End-to-end query → response working
- ✅ Confidence scoring implemented
- ✅ <5% hallucination rate (target)
- ✅ Response latency <2s (p95)

---

### Week 6-7: Frontend & Lead Capture

**API Contracts (Backend):**
- [ ] POST /api/v1/chat (query, session_id)
- [ ] GET /api/v1/analytics/dashboard (time_range)
- [ ] POST /api/v1/leads (student info)
- [ ] GET /api/v1/health (status check)

**Frontend Component:**
- [ ] Build ChatWidget React component
- [ ] Message display (user & bot)
- [ ] Input box with send button
- [ ] Show source citations below response
- [ ] Display recommended questions
- [ ] Fallback message styling

**Lead Capture Form:**
- [ ] Form fields: name, email, phone, program, state
- [ ] Form validation (email format, phone length)
- [ ] Consent checkboxes
- [ ] Submit button + loading state

**Integration:**
- [ ] Connect to backend API
- [ ] Session management (persistent UUID)
- [ ] Error handling (API timeout, 5xx errors)
- [ ] Test on local backend

**Deliverable:**
- ✅ Chat widget embeddable on webpage
- ✅ Lead capture form working
- ✅ API requests successful

---

### Week 7-8: Salesforce CRM Integration

**Setup:**
- [ ] Salesforce Dev Org (free account)
- [ ] Create Lead object with custom fields:
  - interested_programs (multi-select)
  - qualification (picklist)
  - lead_score (number)
  - chat_transcript (long text)
  - source (picklist: chat, form, referral)

**Implementation:**
- [ ] OAuth2 authentication (get access token)
- [ ] Lead sync service (create/update Lead)
- [ ] Async queue (Celery + Redis)
- [ ] Deduplication by email
- [ ] Retry logic (exponential backoff)

**Testing:**
- [ ] Manual: Submit lead → verify in Salesforce
- [ ] Duplicate detection: Submit same email twice → no duplicate
- [ ] Failure recovery: Stop SF API → verify retry works

**Deliverable:**
- ✅ Leads created in Salesforce within 1 minute
- ✅ Deduplication working
- ✅ Async queue preventing rate limit errors

---

### Week 8-9: Analytics & Monitoring

**Event Logging:**
- [ ] Create chat_events table
- [ ] Log: query, response, latency, confidence, fallback reason
- [ ] Async logging (don't slow down API)

**Dashboard:**
- [ ] Queries/day (trend)
- [ ] Avg response time + p95
- [ ] Fallback rate (target: <15%)
- [ ] Low confidence rate
- [ ] Leads captured/day

**Monitoring:**
- [ ] Health check endpoint (/api/v1/health)
- [ ] CloudWatch alarms:
  - API latency > 3s
  - Error rate > 5%
  - Fallback rate > 20%
- [ ] Email alerts to ops team

**Deliverable:**
- ✅ Dashboard shows real-time stats
- ✅ Alerts working (test with manual trigger)
- ✅ Can answer: "How many queries today?"

---

### Week 9-10: Testing & Production Hardening

**Security:**
- [ ] Rate limiting (10 queries/min per IP)
- [ ] CORS policy (college domain only)
- [ ] Input validation (query length, suspicious patterns)
- [ ] API key authentication (for frontend)

**Testing:**
- [ ] Unit tests (chunker, embedder, retrieval)
- [ ] Integration tests (scraper → chunks → retrieval)
- [ ] Load test (100 concurrent users, 10 req/s)
- [ ] Security test (prompt injection, SQL injection)

**Error Handling:**
- [ ] Graceful degradation (all failure paths)
- [ ] Timeouts on all API calls
- [ ] Circuit breaker (if SF API down, queue requests)
- [ ] Retry logic with exponential backoff

**Documentation:**
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Deployment guide (how to deploy to AWS)
- [ ] Troubleshooting guide (common issues)
- [ ] Architecture decision log (ADR)

**Deliverable:**
- ✅ MVP deployed to staging
- ✅ Load test passed (100 concurrent users)
- ✅ Zero critical security issues
- ✅ Fully documented

---

## PHASE 2: Scale & Enhancement (Weeks 11-14)

### Week 11: Production Deployment

- [ ] Production database backup strategy
- [ ] Multi-AZ failover (RDS)
- [ ] Auto-scaling policies (API layer)
- [ ] Blue-green deployment setup
- [ ] Gradual rollout (10% → 50% → 100% traffic)
- [ ] Incident response plan

### Week 12: Recommendation Engine

- [ ] Content-based recommendations (semantic similarity)
- [ ] Cache popular recommendations (Redis)
- [ ] A/B test recommendation prompts
- [ ] Measure click-through rate

### Week 13: Analytics Enhancement

- [ ] Funnel analysis: chat → lead → application
- [ ] Attribution tracking
- [ ] Heatmaps (which questions most asked?)
- [ ] Segment analysis (by program, state, etc)

### Week 14: Vector DB Migration (Optional)

- [ ] Evaluate Pinecone for scaling
- [ ] Benchmark: pgvector vs Pinecone
- [ ] Migrate embeddings (if needed)
- [ ] Update retrieval service

---

## Key Success Metrics (Track Weekly)

| Metric | Target | Current | Owner |
|--------|--------|---------|-------|
| Uptime | 99.5% | - | DevOps |
| Avg Response Time | <2s | - | Backend |
| Hallucination Rate | <5% | - | ML |
| Lead Capture Rate | >5% | - | Product |
| Fallback Rate | <15% | - | ML |
| SF Sync Success Rate | >99% | - | Backend |
| Cost per Query | <$0.05 | - | Finance |

---

## Risk Mitigation Checklist

- [ ] Scraper fails? Alert after 24 hrs no documents
- [ ] LLM latency spikes? Cache common responses
- [ ] SF API down? Queue requests locally, batch sync later
- [ ] Hallucination detected? Manual review + prompt update
- [ ] Data breach? Encryption at rest + audit logs
- [ ] Cost explosion? Set AWS billing alerts + query quotas

