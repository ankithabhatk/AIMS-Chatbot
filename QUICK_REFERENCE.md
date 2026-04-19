# QUICK REFERENCE GUIDE

## 1. System Architecture at a Glance

```
FRONTEND (React + TypeScript)
  ├─ Chat Widget Component
  ├─ Lead Capture Form
  └─ Analytics Dashboard

       ↓ (REST API)

FASTAPI BACKEND
  ├─ /api/v1/chat → Query + Response
  ├─ /api/v1/leads → Lead Capture
  ├─ /api/v1/analytics → Stats
  └─ /api/v1/health → Status

       ↓ (ASYNC QUEUE)

SERVICES
  ├─ Embedding Service (OpenAI)
  ├─ Vector Search (PostgreSQL)
  ├─ LLM Query Engine (GPT-3.5)
  ├─ CRM Sync (Salesforce)
  └─ Analytics Logger (TimescaleDB)

EXTERNAL DEPENDENCIES
  ├─ OpenAI API (embeddings + LLM)
  ├─ Salesforce API (lead sync)
  ├─ College Website (content source)
  └─ AWS (hosting)
```

---

## 2. Data Flow (How a Query is Processed)

```
User: "What are B.Tech admission requirements?"
  ↓
1. EMBED QUERY (100ms)
   OpenAI API: query → 1536-dim vector
   
2. SEARCH (50ms)
   PostgreSQL: vector similarity search
   Return: Top 5 relevant chunks
   
3. BUILD PROMPT (0ms)
   Assemble: system prompt + context chunks + user query
   
4. CALL LLM (1500ms)
   OpenAI GPT-3.5: generate response with citations
   
5. VALIDATE (100ms)
   Score confidence: is response grounded in context?
   If score < 0.7: use fallback
   
6. RETURN RESPONSE (0ms)
   Send to frontend: response + citations + recommendations
   
TOTAL: ~1.75 seconds (target <2s)

LOGGING:
  Store in chat_events table:
  - session_id, query, response, confidence_score, latencies
  - Used for analytics + debugging
```

---

## 3. Database Schema (Key Tables)

```sql
-- Documents (scraped web content)
documents {
  id, url, title, content, content_hash, 
  scraped_at, status
}

-- Chunks (preprocessed text segments)
chunks {
  id, document_id, chunk_index, text, 
  token_count, heading, heading_hierarchy
}

-- Embeddings (vectors for semantic search)
embeddings {
  id, chunk_id, embedding[1536], 
  embedding_model, created_at
}

-- Chat Events (query logs)
chat_events {
  id, session_id, user_query, response, 
  confidence_score, latency_ms, is_fallback, 
  created_at
}

-- Leads (student data)
leads {
  id, session_id, email, phone, 
  interested_programs, lead_score, 
  salesforce_id, sf_sync_status, created_at
}

-- Analytics by hour/day (TimescaleDB)
analytics_events {
  event_type, event_data (JSON), 
  created_at (indexed)
}
```

---

## 4. API Endpoints (Complete)

```
Chat Query:
  POST   /api/v1/chat
  Input:  { query, session_id, user_context }
  Output: { response, confidence_score, sources, recommendations }

Lead Capture:
  POST   /api/v1/leads
  Input:  { name, email, phone, interested_programs, ... }
  Output: { status, lead_id }

Analytics:
  GET    /api/v1/analytics/dashboard
  Input:  { time_range: "7d" }
  Output: { query_count, avg_latency, fallback_rate, ... }

Health Check:
  GET    /api/v1/health
  Output: { status, db, vector_db, salesforce }
```

---

## 5. Technology Stack (Final Decision)

| Component | Technology | Why |
|-----------|------------|-----|
| **Language** | Python 3.11 | ML, async, FastAPI ecosystem |
| **Web Framework** | FastAPI | Async, automatic docs (Swagger) |
| **Database** | PostgreSQL 15 | Relational + pgvector |
| **Vector DB** | pgvector | Free, good for MVP |
| **Frontend** | React 18 + TypeScript | React already chosen |
| **Build Tool** | Vite | Fast, modern |
| **Embeddings** | OpenAI text-embedding-3-small | SOTA, cheap |
| **LLM** | OpenAI GPT-3.5-turbo | Best cost/quality |
| **Cache** | Redis 7 | Standard, fast |
| **Queue** | Celery + Redis | Reliable async |
| **Hosting** | AWS EC2 + RDS | Scalable, enterprise |
| **Scraping** | BeautifulSoup + Selenium | Practical |
| **Monitoring** | CloudWatch + open-source | Cost-effective |
| **Logging** | Structlog | Structured, auditable |

---

## 6. Folder Structure (Ready to Clone)

```
chat-bot/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py
│   │   │   ├── leads.py
│   │   │   ├── analytics.py
│   │   │   └── health.py
│   │   ├── services/
│   │   │   ├── scraper/
│   │   │   ├── preprocessing/
│   │   │   ├── embeddings/
│   │   │   ├── retrieval/
│   │   │   ├── llm/
│   │   │   ├── crm/
│   │   │   ├── analytics/
│   │   │   └── recommendations/
│   │   ├── models/
│   │   ├── utils/
│   │   ├── database/
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/ (unit + integration)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWidget/
│   │   │   ├── LeadForm/
│   │   │   └── ...
│   │   ├── services/
│   │   ├── hooks/
│   │   └── App.tsx
│   └── package.json
├── infra/
│   ├── terraform/
│   ├── kubernetes/
│   └── docker-compose.yml
├── docs/
│   ├── SYSTEM_ARCHITECTURE.md ← You are reading this
│   ├── IMPLEMENTATION_CHECKLIST.md
│   ├── TECH_STACK_DECISIONS.md
│   ├── RISK_REGISTER.md
│   └── API_DOCS.md
└── README.md
```

---

## 7. Development Timeline (Critical Path)

```
WEEK 1-2: Infrastructure
  - AWS setup, GitHub repo, CI/CD skeleton
  - Deliverable: Can deploy code

WEEK 2-3: Scraper
  - Scrape college website, store in S3 + DB
  - Deliverable: 500 documents imported

WEEK 3-4: Preprocessing
  - Chunk documents, extract metadata
  - Deliverable: 2000 chunks ready for embedding

WEEK 4-5: Embeddings + Vector DB
  - Generate embeddings, store in pgvector, test retrieval
  - Deliverable: Vector search working

WEEK 5-6: LLM Integration
  - OpenAI API, prompt engineering, confidence scoring
  - Deliverable: End-to-end query → response

WEEK 6-7: Frontend
  - Chat widget, lead form, connect to API
  - Deliverable: Widget on test webpage

WEEK 7-8: CRM
  - Salesforce sync, deduplication, queue logic
  - Deliverable: Leads in Salesforce

WEEK 8-9: Analytics + Monitoring
  - Event logging, dashboard, alerts
  - Deliverable: Can see usage metrics

WEEK 9-10: Testing + Hardening
  - Unit tests, integration tests, load tests, security
  - Deliverable: MVP ready for production

PHASE 2 (Weeks 11-14): Scale
PHASE 3 (Month 5+): Excellence
```

---

## 8. Critical Decisions (Must Make by Week 1)

| Decision | Options | Recommendation |
|----------|---------|-----------------|
| **Embedding Model** | OpenAI vs Self-hosted | OpenAI (simplicity) |
| **LLM Model** | GPT-4 vs GPT-3.5 | GPT-3.5 (cost) |
| **Vector DB** | Pinecone vs pgvector | pgvector → Pinecone Phase 2 |
| **Hosting** | AWS vs GCP vs Azure | AWS (most experience) |
| **Architecture** | Monolith vs Microservices | Monolith (MVP) |
| **Auth** | API Key vs OAuth | API Key (external) |
| **Rollout** | Big bang vs Gradual | Gradual (10% → 100%) |
| **Monitoring** | Datadog vs Open-source | CloudWatch + open-source |

---

## 9. Success Metrics (Track Weekly)

```
Performance:
  ✓ Avg response latency: <2s (p95)
  ✓ System uptime: 99%+
  ✓ Error rate: <1%

Quality:
  ✓ Hallucination rate: <5%
  ✓ Fallback rate: <15% (escalations)
  ✓ User satisfaction: 4+/5 stars

Business:
  ✓ Queries/day: 500+
  ✓ Lead capture rate: >3%
  ✓ Cost per query: <$0.05
  ✓ Cost per lead: <$10

Operational:
  ✓ Deployment success rate: 100%
  ✓ Incident detection time: <5 min
  ✓ Incident resolution time: <30 min
```

---

## 10. Dependencies & Setup (Day 1)

```bash
# Backend dependencies
pip install fastapi uvicorn sqlalchemy psycopg2 redis
pip install openai langchain pydantic
pip install beautifulsoup4 selenium scrapy
pip install pytest pytest-asyncio

# Frontend dependencies
npm install react react-dom typescript
npm install @types/react @types/react-dom
npm install axios zustand

# Infrastructure
brew install terraform docker postgresql redis

# API Keys needed
OPENAI_API_KEY=sk-...
SALESFORCE_CLIENT_ID=...
SALESFORCE_CLIENT_SECRET=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

---

## 11. Failure Recovery Checklist

```
If Scraper Breaks:
  ✓ Alert system triggered (no docs for 24h)
  ✓ Serve stale data with warning
  ✓ Manual fix selector within 48h
  ✓ Weekly audits prevent this

If LLM Hallucinates:
  ✓ Confidence scoring catches low-confidence
  ✓ User feedback triggers manual review
  ✓ Prompt updated within 24h
  ✓ Test on 100 Q&A set for regression

If CRM Sync Fails:
  ✓ Retry queue automatically retries
  ✓ Deduplication prevents duplicates
  ✓ Manual reconciliation weekly
  ✓ Alert if >5 pending after 1h

If Latency Spikes:
  ✓ Caching reduces 30% of calls
  ✓ Load balancer scales horizontally
  ✓ Queue system smooths traffic
  ✓ Timeout fallback returns fastest answer

If Cost Explodes:
  ✓ Cost alerts trigger at $500/month
  ✓ Query quotas enforce limits
  ✓ Aggressive caching reduces 40%
  ✓ Fine-tuning reduces 50% in Phase 2
```

---

## 12. First Week Checklist

**Day 1:**
- [ ] Read all 4 architecture documents
- [ ] Form core team (names assigned)
- [ ] Identify decision maker for approvals

**Day 2-3:**
- [ ] AWS account setup
- [ ] GitHub repo initialized
- [ ] Team has access to AWS + GitHub

**Day 4-5:**
- [ ] Docker + Docker Compose working locally
- [ ] PostgreSQL + Redis running
- [ ] OpenAI API key tested
- [ ] Salesforce sandbox access

**End of Week 1:**
- [ ] PoC: Scrape 10 pages → embed → search
- [ ] PoC: Query backend → get chunks
- [ ] Team knows architecture (can explain RAG)
- [ ] Timeline confirmed (4 months realistic?)

---

## 13. Questions to Ask in Week 1 Sync

**Technical:**
1. "How accurately can we expect the chatbot to answer?"
   → Honest: 85-90% with effort, 80% without
2. "What if the website changes?"
   → Plan: Alerts + manual backup + weekly audit
3. "How will we know if hallucinations are a problem?"
   → Plan: Confidence scoring + user feedback + QA

**Business:**
1. "What's our success metric?"
   → Admissions team says: Lead quality + conversion
2. "What's our launch date?"
   → Honest: 4 months minimum, 5-6 realistic
3. "What if accuracy isn't good?"
   → Plan: Iterate, improve prompts, consider GPT-4

**Operational:**
1. "Who maintains the scraper when it breaks?"
   → Assign: DevOps + on-call rotation
2. "Who fixes bugs in production?"
   → Assign: Senior engineer on-call
3. "How do we prevent duplicate leads in SF?"
   → Built-in: Email-based deduplication + manual checks

---

## 14. Books / Resources to Read

**LLM & RAG:**
- "Building LLM Applications" by Cheng
- LangChain documentation
- OpenAI API docs

**Production Systems:**
- "Site Reliability Engineering" (Google)
- "The Outsiders" by Gino Wickman

**Python Best Practices:**
- "Fluent Python" by Ramalho
- FastAPI documentation

**Database Design:**
- "Designing Data-Intensive Applications" by Kleppmann
- PostgreSQL documentation

---

## 15. Glossary

**RAG:** Retrieval-Augmented Generation (fetch context, then generate response)

**Vector:** Numerical representation of text (1536 numbers for OpenAI)

**Embedding:** Converting text to vector

**Hallucination:** LLM making up false information

**Confidence Score:** How sure are we this response is correct?

**Fallback:** When we don't know, escalate to human

**pgvector:** PostgreSQL extension for vector search

**IVFFlat:** Indexing method for fast vector similarity search

**Chunk:** Small piece of document (256-512 tokens)

**Latency:** Response time (from request to response)

**QPS:** Queries per second (throughput metric)

**SLA:** Service Level Agreement (99.9% uptime, etc)

---

## BEFORE YOU START CODING

**Print this and read it:**
1. EXECUTIVE_SUMMARY.md (1 page summary)
2. SYSTEM_ARCHITECTURE.md (complete design)
3. RISK_REGISTER.md (worst-case scenarios)

**Get approvals for:**
1. Budget ($200K dev + $15K/year ops)
2. Timeline (4-5 months, not 2)
3. Team (2-3 dedicated engineers)
4. Success metrics (what matters most?)

**Setup infrastructure:**
1. AWS account + credentials
2. GitHub repo + access
3. OpenAI API key
4. Salesforce sandbox

**Have first team sync:**
1. Review architecture together
2. Assign ownership (who does what?)
3. Set sprint 1 goals (PoC by end of week)
4. Establish communication rhythm (daily standup?)

---

**NOW YOU'RE READY TO BUILD.**

Start with the scraper PoC. If that works, everything else will follow. 🚀

