# TECH STACK DECISION MATRIX

## Executive Summary

| Component | Recommended | Rationale | Risk Level |
|-----------|-------------|-----------|-----------|
| **Language** | Python (FastAPI) | Perfect for ML/LLM pipelines | Low |
| **Frontend** | React + TypeScript | Already chosen, good ecosystem | Low |
| **Web Scraping** | BeautifulSoup + Selenium | Practical balance of simplicity & power | Medium |
| **Database** | PostgreSQL + pgvector | Free, scalable to 100K vectors | Low |
| **Vector DB** | pgvector → Pinecone (Phase 2) | Start cheap, migrate when needed | Medium |
| **Embeddings** | OpenAI text-embedding-3-small | Cost-effective, high quality | Low |
| **LLM** | OpenAI GPT-3.5-turbo → GPT-4 | Best accuracy/cost ratio | Medium |
| **CRM** | Salesforce REST API | Already required, direct integration | Medium |
| **Cache** | Redis | Standard choice, good performance | Low |
| **Hosting** | AWS (EC2 + RDS) | Scalable, enterprise-grade | Low |

---

## Component-by-Component Breakdown

---

## 1. WEB SCRAPING

### Option A: BeautifulSoup + Selenium (RECOMMENDED) ✅

**Pros:**
- Simple for static HTML (90% of college website)
- Add Selenium only for JS-heavy pages
- Fast iteration, easy debugging
- Huge community, tons of examples
- Low maintenance burden

**Cons:**
- Selenium is slower than headless Chrome
- No built-in JavaScript rendering
- Manual CSS selector maintenance

**Tech Details:**
```python
# Static pages
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')
title = soup.find('h1', class_='program-title').text

# JS-heavy pages
from selenium import webdriver
driver = webdriver.Chrome()
driver.get(url)
html = driver.page_source
```

**Cost:** $0 (open source)
**Setup Time:** 4 hours
**Maintenance:** Low (weekly updates for broken selectors)

---

### Option B: Scrapy (Alternative)

**Pros:**
- Professional-grade framework
- Built-in handling of JS, redirects, retries
- Excellent for large-scale scraping
- Production-ready pipelines

**Cons:**
- Steeper learning curve
- Overkill for single college website
- More complex to debug

**When to Use:** If scraping 50+ websites (multi-college platform)

**Verdict:** NO for MVP, YES for Phase 2 expansion

---

### Option C: Puppeteer / Playwright (Alternative)

**Pros:**
- Modern headless browser automation
- Excellent JS rendering
- Faster than Selenium

**Cons:**
- Node.js (extra language to manage)
- More resource-intensive
- Need to call from Python anyway

**Verdict:** NO, stick with Selenium

---

## 2. DATABASE

### Option A: PostgreSQL + pgvector (RECOMMENDED) ✅

**Pros:**
- Single database for all data (documents, embeddings, analytics)
- pgvector extension supports 1536-dim vectors
- IVFFlat indexing gives ~50ms retrieval for 10K vectors
- Built-in time-series (TimescaleDB) for analytics
- Native ACID compliance
- Backups, replication, free tools

**Cons:**
- Vector search slower than Pinecone at >100K vectors
- Index maintenance overhead
- Single-node limitation (RDS does have read replicas)

**Performance:**
- Vectors: 0-100K ✅ Good
- Vectors: 100K-1M ⚠️ Acceptable (200-300ms latency)
- Vectors: >1M ❌ Not recommended (migrate to Pinecone)

**Tech Details:**
```sql
-- Enable pgvector
CREATE EXTENSION vector;

-- Create embeddings table
CREATE TABLE embeddings (
  id UUID PRIMARY KEY,
  chunk_id UUID NOT NULL,
  embedding vector(1536) NOT NULL
);

-- Create index (IVFFlat)
CREATE INDEX ON embeddings USING ivfflat 
(embedding vector_cosine_ops) WITH (lists = 100);

-- Query
SELECT chunk_id 
FROM embeddings 
ORDER BY embedding <-> query_embedding 
LIMIT 5;
```

**Cost:** $25/month (RDS t3.micro-small)
**Setup Time:** 2 hours
**Maintenance:** Low

---

### Option B: Pinecone (Alternative, for Phase 2+)

**Pros:**
- Managed service (no ops burden)
- Infinitely scalable
- Same latency (<50ms) regardless of vector count
- Built-in metadata filtering
- Automatic backups

**Cons:**
- Vendor lock-in
- Costs increase with vector count
- Overkill for MVP

**When to Use:** When you exceed 100K vectors or want managed service

**Cost:** $10-100/month (depends on vector count + query volume)
**Migration Effort:** 1 week

**Tech Details:**
```python
import pinecone

pinecone.init(api_key="xxx")
index = pinecone.Index("chatbot")

# Upsert vectors
index.upsert(vectors=[
    ("id1", [0.1, 0.2, ...]),  # 1536-dim vector
    ("id2", [0.3, 0.4, ...])
])

# Query
results = index.query([0.1, 0.2, ...], top_k=5)
```

---

### Option C: Weaviate (Alternative)

**Pros:**
- Open-source vector DB
- Could be self-hosted for cheap
- Good API, modern architecture

**Cons:**
- Lower community adoption than Pinecone
- Self-hosting requires ops expertise
- Cloud offering similar price to Pinecone

**Verdict:** Unless you want self-hosting burden, choose Pinecone for Phase 2

---

## 3. EMBEDDING MODEL

### Option A: OpenAI text-embedding-3-small (RECOMMENDED) ✅

**Specs:**
- Dimensions: 1536
- Cost: $0.02 per 1M tokens = ~$1-2/month for 500K tokens
- Latency: ~100ms per request
- Quality: SOTA (state-of-the-art)

**Pros:**
- Highest quality embeddings
- Large training data (knowledge cutoff benefits RAG)
- Simple API
- Vendor support (OpenAI backing)

**Cons:**
- Vendor lock-in (OpenAI only)
- API rate limits (300 requests/min)
- Requires billing setup

**When to Use:** MVP and beyond (it's cheap!)

**Cost:** $1-5/month
**Quality Score:** 9/10

---

### Option B: OpenAI text-embedding-3-large (Alternative)

**Specs:**
- Dimensions: 3072
- Cost: $0.13 per 1M tokens (6.5x more expensive)
- Latency: ~150ms
- Quality: Slightly better than small

**Verdict:** NO for college chatbot (overkill, not worth cost)

---

### Option C: Sentence-Transformers (Self-Hosted) (Alternative)

**Model:** all-MiniLM-L6-v2
**Specs:**
- Dimensions: 384
- Cost: Free (CPU inference)
- Latency: ~100ms (depends on hardware)
- Quality: Good (7/10)

**Pros:**
- No API costs
- No vendor lock-in
- Runs locally

**Cons:**
- Requires GPU for production (adds cost + complexity)
- Lower quality than OpenAI
- Model management overhead

**When to Use:** If cost is critical AND you have engineering capacity

**Cost:** $0 (but needs infrastructure)
**Quality Score:** 7/10

---

### Option D: Cohere Embeddings (Alternative)

**Pros:**
- Good quality (8/10)
- Reasonable pricing
- API similar to OpenAI

**Cons:**
- Smaller company (adoption risk)
- Similar cost to OpenAI

**Verdict:** Stick with OpenAI (safer choice)

---

## 4. LLM MODEL

### Option A: OpenAI GPT-3.5-turbo (RECOMMENDED FOR MVP) ✅

**Specs:**
- Cost: $0.001 per input token, $0.002 per output token
- Avg college query: ~50 input tokens + 100 output tokens = $0.00025
- Latency: ~1-2s
- Quality: Good for college FAQ (7/10)
- Token limit: 4K context (enough for 5 chunks + query)

**Pros:**
- Cheapest quality option
- Fast iteration (outputs in seconds)
- Good for structured queries (admissions, fees)
- Reliable API

**Cons:**
- Hallucinations possible (need confidence filtering)
- Less accurate on nuanced questions
- Lower reasoning capability

**When to Use:** MVP (get to market fast)

**Estimated Cost:** $100-300/month (depends on query volume)
**Quality Score:** 7/10 (sufficient for college FAQ)

---

### Option B: OpenAI GPT-4 (RECOMMENDED FOR PRODUCTION) ✅

**Specs:**
- Cost: $0.05 per input token, $0.15 per output token
- Avg college query: $0.0075 (30x more expensive than 3.5)
- Latency: ~3-5s
- Quality: Excellent (9/10)
- Token limit: 8K context (plenty of room)

**Pros:**
- Much better at reasoning
- Fewer hallucinations
- Better handling of edge cases
- Can handle complex queries

**Cons:**
- Expensive (can exceed $1K/month)
- Slower (3-5s vs 1-2s)
- May be overkill for simple FAQ

**When to Use:** 
- Phase 2+ when established customer base
- Questions requiring high accuracy
- If budget allows

**Estimated Cost:** $1000+/month (heavy volume)
**Quality Score:** 9/10

---

### Option C: Anthropic Claude (Alternative)

**Pros:**
- Excellent reasoning
- Very low hallucination rate
- Safety-focused design

**Cons:**
- More expensive than GPT-3.5
- Slower than GPT-4
- Different API (learning curve)

**Verdict:** Good alternative if hallucination is major issue. Test in Phase 2.

**Estimated Cost:** Similar to GPT-4

---

### Option D: Open-Source (Llama 2, Mistral) (Alternative)

**Pros:**
- Free model weights
- Full control + no vendor lock-in
- Can fine-tune

**Cons:**
- Requires GPU (A100: $2.50/hour = too expensive)
- Lower quality than GPT-4
- Model ops overhead (deployment, caching)
- Not mature for production

**When to Use:** Phase 3+ if cost becomes critical AND you have ML team

**Estimated Cost:** $500-1000/month (infrastructure) + team effort

**Verdict:** NO for MVP/Phase 2

---

## 5. INFERENCE OPTIMIZATION

### If using GPT-3.5, target cost reduction:

**Strategy 1: Response Caching** (Easiest)
```
Implementation: Cache responses for identical/similar queries
Impact: Reduce LLM calls by ~20-30%
Savings: $20-50/month
Setup Time: 2 days
```

**Strategy 2: Prompt Compression**
```
Implementation: Use fewer examples in prompt, compress context
Impact: Reduce tokens/request by ~30%
Savings: $30/month
Setup Time: 1 week (testing)
```

**Strategy 3: Hybrid Model**
```
Implementation: Use GPT-3.5 for 80% queries, GPT-4 for complex 20%
Impact: Better accuracy + lower cost
Savings: N/A (actually costs less than all GPT-4)
Setup Time: 1 week (routing logic)
```

**Strategy 4: Fine-Tuned GPT-3.5**
```
Implementation: Fine-tune on college FAQ data (100+ examples)
Impact: Better college-specific responses, lower hallucination
Savings: Potential quality improvement worth cost
Cost: $0.008 per input token (cheaper than base), +training cost
Setup Time: 3 weeks (collect data, train, validate)
Recommendation: Phase 2, if hallucination rate too high
```

---

## 6. CACHING ARCHITECTURE

### Multi-Layer Caching Strategy:

```python
# Layer 1: Query Response Cache (Frontend/CloudFront)
# Cache identical responses for 1 hour
# Hit rate: ~20-30% (many repeated questions)

cache_key = hash(user_query_normalized)
if cache.exists(cache_key):
    return cache.get(cache_key)  # Cached response
else:
    response = call_backend_api()
    cache.set(cache_key, response, ttl=3600)  # 1 hour
    return response

# Layer 2: Embedding Cache (Redis)
# Cache embeddings for 24 hours
# Hit rate: ~40% (same words = same embedding)

embedding_cache_key = f"embedding:{user_query}"
if redis.exists(embedding_cache_key):
    embedding = redis.get(embedding_cache_key)
else:
    embedding = openai.Embedding.create(input=user_query)
    redis.set(embedding_cache_key, embedding, ex=86400)  # 24 hours

# Layer 3: Retrieval Cache (Database query results)
# Cache chunk retrieval for 6 hours
# Hit rate: ~30% (same intent = nearby chunks)

# Layer 4: LLM Response Cache
# Cache LLM outputs for identical context/query combos
# Hit rate: ~10-15% (very low, but helps edge cases)
```

**Expected Cost Reduction:** 40-50% with all layers

---

## 7. ARCHITECTURE DECISION SUMMARY TABLE

```
┌─────────────────────┬──────────────────┬─────────────────┬──────────────┐
│ Component           │ MVP Choice       │ Phase 2 Choice  │ Phase 3 Choice│
├─────────────────────┼──────────────────┼─────────────────┼──────────────┤
│ API Framework       │ FastAPI          │ FastAPI         │ FastAPI      │
│ Database            │ PostgreSQL       │ PostgreSQL      │ PostgreSQL   │
│ Vector DB           │ pgvector         │ Pinecone*       │ Pinecone     │
│ Embeddings          │ text-embed-3-sm  │ text-embed-3-sm │ Fine-tuned   │
│ LLM                 │ GPT-3.5-turbo    │ GPT-3.5/4 mix   │ Fine-tuned   │
│ Cache               │ Redis            │ Redis +         │ Redis +      │
│                     │                  │ CloudFront      │ CloudFront   │
│ Message Queue       │ Redis            │ Redis/RabbitMQ  │ Kafka        │
│ Monitoring          │ CloudWatch       │ Prometheus      │ Datadog      │
│ Scraping            │ BS4 + Selenium   │ BS4 + Selenium  │ Scrapy       │
└─────────────────────┴──────────────────┴─────────────────┴──────────────┘
* Only if > 100K vectors or need managed service
```

---

## 8. COST OPTIMIZATION ROADMAP

### Month 1-2 (MVP):
```
Fixed Costs:
  AWS (EC2 + RDS):      $30/month
  Pinecone:             $0 (using pgvector)
  
Variable Costs:
  OpenAI Embeddings:    ~$1/month (small volume)
  OpenAI LLM:           ~$50/month (1K queries)
  ---
  Total:                ~$80/month
```

### Month 3-6 (Scaling):
```
Fixed:
  AWS:                  $100/month (multi-instance)
  Pinecone:             $25-50 (if migrated)
  Salesforce:           $300/month (licenses)
  
Variable:
  OpenAI:               $300/month (5K queries)
  ---
  Total:                ~$750/month
```

### Month 6+ (Cost Reduction Phase):

```
Optimization 1: Response Caching
  Savings: -$50/month (reduce LLM calls 20%)

Optimization 2: Cheaper Embedding Model
  Savings: -$30/month (text-embedding-3-small already cheap)

Optimization 3: Fine-tuned Model
  Savings: -$100/month (domain-specific better quality + efficiency)
  Cost: +$50/month (fine-tuning overhead)
  Net: -$50/month

Optimization 4: Self-hosted Vector DB
  Savings: -$25/month (pgvector if Pinecone adopted)
  Cost: +$50/month (operational overhead)
  Net: +$25/month (not recommended)

Total Optimized Cost: ~$650/month (vs $750)
```

---

## 9. RISK-ADJUSTED RECOMMENDATIONS

### What if OpenAI API becomes unavailable?

```
Contingency 1: Fallback to Claude
  Setup Time: 2 days (new API integration)
  Performance: Similar to GPT-3.5
  Cost: Similar
  
Contingency 2: Fallback to Open-Source (Mistral)
  Setup Time: 3 weeks (GPU procurement + tuning)
  Performance: Lower quality
  Cost: Higher (GPU infrastructure)
  
Recommendation: Have Claude API keys ready (backup)
```

### What if embedding costs explode?

```
Current: $1-2/month (cheap)
Risk: If query volume → 100K/month, could be $100+/month

Mitigations:
  1. Fine-tune smaller embedding model (50% cost reduction)
  2. Implement deduplication (reduce embedding calls)
  3. Use Sentence-Transformers (free)

Recommendation: Build caching ASAP
```

---

## FINAL TECH STACK (LOCKED FOR MVP)

```yaml
Frontend:
  Language: TypeScript + React
  Build: Vite
  State: React Hooks
  Styling: TailwindCSS
  Deployment: S3 + CloudFront

Backend:
  Language: Python 3.11
  Framework: FastAPI
  Database: PostgreSQL + pgvector
  Cache: Redis
  Task Queue: Celery (Redis backend)
  
ML Stack:
  Embeddings: OpenAI text-embedding-3-small
  LLM: OpenAI GPT-3.5-turbo
  Retrieval: pgvector IVFFlat
  Validation: Custom confidence scoring

DevOps:
  Container: Docker + Docker Compose
  Orchestration: ECS (or K8s Phase 2)
  IaC: Terraform
  CI/CD: GitHub Actions
  Monitoring: CloudWatch + open-source options
  
Integration:
  CRM: Salesforce REST API
  Web Scraping: BeautifulSoup + Selenium
  Logging: Structlog + ELK (or S3)
  Secrets: AWS Secrets Manager

Development:
  IDE: VS Code
  Language Server: Pylance (Python), ESLint (JS)
  Testing: pytest (backend), Jest (frontend)
  Code Quality: Black, Flake8 (Python), Prettier (JS)
  Version Control: GitHub
```

---

## GO/NO-GO DECISION CHECKLIST

Before starting, verify:

- [ ] Team has Python expertise (FastAPI)
- [ ] Team has React expertise (TypeScript)
- [ ] AWS account created + permissions
- [ ] OpenAI API key obtained + tested
- [ ] Salesforce trial account created
- [ ] College website stable (not changing daily)
- [ ] Budget approved (~$1K/month)
- [ ] Timeline realistic (4 months minimum)

**If ANY are NO:** Reassess or descope features.

