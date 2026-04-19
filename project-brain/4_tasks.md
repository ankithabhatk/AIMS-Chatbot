# Task List & Roadmap

## 🔥 JUST COMPLETED

- [x] RAG pipeline implementation
  - [x] Embedding service (Sentence-Transformers)
  - [x] FAISS retrieval system
  - [x] Response generator (template-based)
  - [x] Web scraper (BeautifulSoup)
  - [x] Data ingestion orchestration
  - [x] Chat endpoint (/api/v1/chat)
  - [x] Sample data loader
  - [x] Test script (test_rag.py)
  - [x] Documentation (RAG_SETUP_GUIDE.md)

---

## 🟢 IMMEDIATE NEXT (Week 1)

- [ ] Test real website scraping
  - [ ] Verify BeautifulSoup extraction
  - [ ] Handle website changes gracefully
  - [ ] Test with actual AIMS website
- [ ] Add database integration
  - [ ] Create PostgreSQL schema from db_models.py
  - [ ] Store documents in database
  - [ ] Load embeddings on startup from DB
- [ ] Improve sample data
  - [ ] Add 20-30 real Q&A pairs
  - [ ] Better chunk quality
  - [ ] Add more topics

---

## 🟡 NEXT PHASE (Week 2)

### Lead Capture
- [ ] Implement /api/v1/leads endpoint
  - [ ] Validate input (email, name, etc.)
  - [ ] Deduplication logic
  - [ ] Save to database
- [ ] Add lead scoring
  - [ ] Interest level from query topic
  - [ ] Qualification based on state/qualification
  - [ ] Score cutoff for CRM sync

### Analytics
- [ ] Implement /api/v1/analytics/dashboard
  - [ ] Query count by topic
  - [ ] Confidence score distribution
  - [ ] Fallback rate
  - [ ] Top questions
  - [ ] Lead generation trends

### Caching
- [ ] Add Redis caching for queries
  - [ ] Cache hit rate target: 20-30%
  - [ ] Cache embedding results
  - [ ] Cache frequent queries

---

## 🔵 INTEGRATION PHASE (Week 3)

### Salesforce CRM
- [ ] Implement Salesforce client
  - [ ] OAuth authentication
  - [ ] Lead creation API
  - [ ] Duplicate detection
  - [ ] Error handling + retry
- [ ] Connect to Celery queue
  - [ ] Async lead sync
  - [ ] Retry logic (5s, 30s, 5min backoff)
  - [ ] Track sync status

### Celery Background Jobs
- [ ] Implement scraper job
  - [ ] Daily re-scrape (2 AM)
  - [ ] Change detection
  - [ ] Alert on website down
- [ ] Implement embedding generation job
  - [ ] Batch process new documents
  - [ ] Update FAISS index
- [ ] Cache cleanup job
  - [ ] Expire old entries (3 AM)

---

## 🟣 FRONTEND (Week 4)

- [ ] Create React chat widget
  - [ ] Chat input + display
  - [ ] Message history
  - [ ] Confidence indicator
  - [ ] Source links
- [ ] Implement lead capture form
  - [ ] Form validation
  - [ ] Submit to backend
  - [ ] Success/error messages
- [ ] Connect to backend API
  - [ ] Real requests to /api/v1/chat
  - [ ] Error handling
  - [ ] Loading states

---

## 🟠 REFINEMENT (Week 5)

### Quality
- [ ] Improve embedding accuracy
  - [ ] Fine-tune model on college data (optional)
  - [ ] Add query preprocessing (lowercase, punctuation)
  - [ ] Improve chunking strategy
- [ ] Better response generation
  - [ ] Add OpenAI option (if budget allows)
  - [ ] Improve templates
  - [ ] Add multi-language support (future)

### Performance
- [ ] Optimize FAISS index
  - [ ] IVFFlat with more centroids
  - [ ] Benchmark: target <100ms search
- [ ] Reduce embedding time
  - [ ] Batch GPU processing (if available)
  - [ ] Cache model in memory

### Monitoring
- [ ] Add Prometheus metrics
  - [ ] Request count
  - [ ] Response time distribution
  - [ ] Error rate
  - [ ] Confidence score distribution
- [ ] Add structured logging
  - [ ] Query logs with metadata
  - [ ] Performance tracking

---

## 🟤 DEPLOYMENT (Week 6)

- [ ] Docker setup
  - [ ] Build FastAPI image
  - [ ] Docker Compose for full stack
  - [ ] Environment variable handling
- [ ] Infrastructure as Code
  - [ ] Terraform for AWS deployment
  - [ ] RDS PostgreSQL
  - [ ] EC2 for FastAPI
  - [ ] CloudFront for static files
- [ ] CI/CD Pipeline
  - [ ] GitHub Actions
  - [ ] Auto-deploy on push to main
  - [ ] Test suite in pipeline

---

## 📋 BACKLOG (Future)

### Long-term Features
- [ ] Multi-turn conversation (memory)
- [ ] Recommendation engine
- [ ] Fine-tuned embedding model
- [ ] Pinecone migration for scale
- [ ] Advanced analytics
- [ ] A/B testing framework
- [ ] Multi-language support
- [ ] Voice input integration

### DevOps
- [ ] Kubernetes deployment
- [ ] Auto-scaling
- [ ] Blue-green deployment
- [ ] Disaster recovery
- [ ] Backup strategy

---

## 📊 BLOCKERS & DEPENDENCIES

### Can Start Now
- ✅ Real website scraping (scraper ready)
- ✅ Database integration (models defined)
- ✅ Lead capture (basic endpoint ready)

### Waiting For
- 🟡 Team decision: Store data in DB or keep local?
- 🟡 Salesforce OAuth setup (credentials needed)
- 🟡 Frontend design (can be parallel)

### Risk Items
- ⚠️ Website scraper fragility (if AIMS changes HTML)
- ⚠️ Poor embedding quality on niche topics
- ⚠️ Performance under load (need benchmarking)

---

## 👁️ PRIORITY MATRIX

```
High Impact / Easy   →  Lead capture + Analytics
High Impact / Hard   →  Salesforce integration
Low Impact / Easy    →  Better templates
Low Impact / Hard    →  Fine-tuned models
```

**Recommended Next**: Test real scraping + Database integration
