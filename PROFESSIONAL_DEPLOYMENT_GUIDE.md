# 🚀 AIMS Chatbot - Professional Deployment Guide

Complete guide to deploying and operating the AIMS college chatbot system.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [System Architecture](#system-architecture)
3. [Component Setup](#component-setup)
4. [Data Enrichment](#data-enrichment)
5. [Testing & Validation](#testing--validation)
6. [Operations](#operations)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
pip install -r backend/requirements.txt
```

### Start Everything (3 Terminal Windows)

**Terminal 1 - Backend API:**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend Server:**
```bash
python serve_frontend.py
# Serves http://localhost:8001
```

**Terminal 3 - Test/Monitor:**
```bash
# Option A: Quick test
python backend/scripts/fast_test.py

# Option B: Browser integration test  
python backend/scripts/integration_test.py

# Option C: Professional frontend test
python backend/scripts/test_professional_frontend.py
```

### Access the Chatbot
- **Modern UI**: http://localhost:8001/index.html
- **Professional UI**: http://localhost:8001/professional.html

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     BROWSER                                 │
│                   (User Interface)                          │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP Requests
                         │ (Fetch API)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            FRONTEND SERVER (Port 8001)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ /index.html          - Modern gradient design        │  │
│  │ /professional.html   - AIMS-branded professional UI  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ POST /api/chat
                         │ (JSON)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           BACKEND API SERVER (Port 8000)                    │
│                     (FastAPI)                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ POST /api/chat          - Main chat endpoint         │  │
│  │ GET  /api/health        - System health check        │  │
│  │ GET  /api/analytics     - Usage statistics           │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────┬───────────────────────────────┬────────────────┘
             │                               │
             ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│  EMBEDDING SERVICE       │    │  LLM RESPONSE MODULE     │
│  (sentence-transformers) │    │  (GPT/Claude synthesis)  │
│  - 384-dim vectors       │    │  - Answer generation     │
│  - Query embedding       │    │  - Confidence scoring    │
└──────────┬───────────────┘    └──────────┬───────────────┘
           │                               │
           ▼                               │
┌──────────────────────────┐               │
│   VECTOR DATABASE        │               │
│   (FAISS)                │               │
│   /tmp/chatbot_faiss/    │◄──────────────┤
│  - index.faiss (69KB)    │  Document     │
│  - metadata.json (125KB) │  Retrieval    │
│  - 46 documents indexed  │               │
│  - 384-dim vectors       │               │
└──────────────────────────┘               │
                                           │
                    ┌──────────────────────┘
                    │ Retrieved Documents
                    │ (Top 3-5 chunks)
                    │
                    ▼
            ┌──────────────┐
            │ Response     │
            │ - Answer     │
            │ - Confidence │
            │ - Sources    │
            │ - Suggestions│
            └──────────────┘
```

---

## 🔧 Component Setup

### 1. Backend Setup

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Set environment variables
export FAISS_INDEX_PATH=/tmp/chatbot_faiss

# Start backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Health Check:**
```bash
curl http://localhost:8000/api/health
# Expected response:
# {"status": "healthy", "documents": 46, "faiss_synced": true}
```

### 2. Frontend Server Setup

```bash
# Start frontend server (Python built-in)
python serve_frontend.py
# Listens on http://localhost:8001
```

**Access Frontends:**
- Modern UI: http://localhost:8001/index.html
- Professional UI: http://localhost:8001/professional.html

### 3. FAISS Vector Database

Located at: `/tmp/chatbot_faiss/`

**Contents:**
```
/tmp/chatbot_faiss/
├── index.faiss          # FAISS index with 384-dim vectors
└── metadata.json        # Document metadata (46 docs)
```

**Check Status:**
```bash
python -c "
import json
with open('/tmp/chatbot_faiss/metadata.json') as f:
    meta = json.load(f)
    print(f'📚 Total documents: {len(meta)}')
    print(f'📏 Index size: {os.path.getsize(\"/tmp/chatbot_faiss/index.faiss\") / 1024:.1f} KB')
"
```

---

## 📊 Data Enrichment Pipeline

### Current Status
- **Documents Indexed**: 46 (from AIMS website)
- **Current Confidence**: 20-68% (generic data)
- **Target Confidence**: 70%+ (with institutional data)

### Data Enrichment Steps

#### Step 1: Deep Web Scraping (Optional)
```bash
# Scrape all AIMS website pages
python backend/scripts/scrape_aims_website.py

# Output: /tmp/aims_scraped_data.json
```

#### Step 2: Load Institutional Documents

**Required Documents from AIMS:**
1. Official fee structure (PDF/Excel)
2. Placement statistics (PDF/Report)
3. Campus facility details (PDF)
4. Scholarship information (PDF)
5. Admission requirements (PDF)

**Email Template:** See `DATA_REQUEST_EMAIL_TEMPLATE.md`

**Send to:** admissions@theaims.ac.in

#### Step 3: Ingest New Documents
```bash
# Ingest new documents
python backend/scripts/ingest.py /path/to/new/documents

# Example with downloaded PDFs:
python backend/scripts/ingest.py ~/Downloads/AIMS_Fees.pdf ~/Downloads/Placements.pdf
```

#### Step 4: Rebuild FAISS Index
```bash
# Automatic - runs during ingestion
# But can manually rebuild:
python backend/scripts/test_faiss_health.py
```

#### Step 5: Validate Improvements
```bash
# Run 30-query validation test
python backend/scripts/test_reliability_30queries.py

# Expected improvement: 32% → 70%+ average confidence
```

---

## ✅ Testing & Validation

### 1. Quick API Test
```bash
python backend/scripts/fast_test.py
```

**What it tests:**
- API connectivity
- Response format
- Confidence score accuracy
- Response time (<100ms)

**Expected output:**
```
✅ Query 1: "What programs?" - 68% confidence
✅ Query 2: "What fees?" - 20% confidence (incomplete data)
✅ Query 3: "Placement?" - 48% confidence
⏱️  All responses in ~50ms
```

### 2. Integration Test (Playwright)
```bash
python backend/scripts/integration_test.py
```

**What it tests:**
- Frontend + Backend integration
- CORS configuration
- Response rendering in browser
- Screenshot verification

**Makes browser**: Headless Chromium, loads UI, submits queries, captures results

### 3. Professional Frontend Test
```bash
python backend/scripts/test_professional_frontend.py
```

**What it tests:**
- Professional.html renders correctly
- AIMS branding visible
- Chat functionality works
- API responses appear in UI

**Output:**
- Test results summary
- Screenshot: `/tmp/professional_frontend_test.png`

### 4. Manual Testing
```bash
# Open in browser
http://localhost:8001/professional.html

# Try queries:
1. "What programs?"
2. "Placement statistics"
3. "Fees and costs"
4. "Campus facilities"
5. "How to apply?"
```

---

## 🎯 Operations

### Monitoring

**Check System Health:**
```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "documents": 46,
  "faiss_synced": true,
  "last_indexed": "2024-04-19T10:30:00Z"
}
```

### Usage Analytics

**View Chat Statistics:**
```bash
curl http://localhost:8000/api/analytics
```

**Response:**
```json
{
  "total_queries": 156,
  "avg_confidence": 48.5,
  "queries_today": 23,
  "top_questions": [
    {"query": "What programs?", "count": 12},
    {"query": "How to apply?", "count": 8},
    {"query": "Fees?", "count": 7}
  ]
}
```

### Logs

**Backend logs:**
```bash
# See in terminal running FastAPI
# Look for: [timestamp] - [level] - [message]
```

**Query logs:**
```bash
cat backend/logs/queries.log | tail -20
```

### Performance Metrics

**Key metrics to monitor:**
- **Query Response Time**: <100ms (excellent)
- **Average Confidence**: >70% (target with full data)
- **Document Retrieval Rate**: 3-5 docs per query (expected)
- **Uptime**: Track in monitoring dashboard

---

## 🔧 Troubleshooting

### Issue: "Error: Failed to fetch"

**Cause**: CORS not configured or frontend not on correct port

**Solution**:
```bash
# Verify CORS in backend/app/main.py includes:
# "http://localhost:8001"
# "http://127.0.0.1:8001"

# Restart backend:
python -m uvicorn app.main:app --reload
```

### Issue: Confidence scores all 0%

**Cause**: API field name mismatch or embedding service error

**Solution**:
```bash
# Check API response format
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Look for "confidence" field (not "confidence_score")

# Check embedding service
python backend/scripts/test_harness.py
```

### Issue: FAISS index not found

**Cause**: Knowledge base not initialized

**Solution**:
```bash
# Initialize FAISS index
python -c "
from backend.services.retrieval.faiss_index import FAISSIndex
index = FAISSIndex()
index.build()
print('✅ FAISS initialized')
"
```

### Issue: Slow responses (>500ms)

**Cause**: Large knowledge base or slow embedding model

**Solution**:
```bash
# 1. Monitor CPU/Memory
top | grep python

# 2. Optimize FAISS search
# Reduce index size or increase cache

# 3. Use faster hardware or optimize queries
```

### Issue: ChatBot returns "No answer available"

**Cause**: Question not in knowledge base or too different from training data

**Solution**:
```bash
# 1. Add documents covering the topic
python backend/scripts/ingest.py /path/to/document.pdf

# 2. Check if question is ambiguous
# Rephrase and try again

# 3. View available topics
cat /tmp/chatbot_faiss/metadata.json | jq '.[].heading' | sort -u
```

---

## 📚 API Reference

### Chat Endpoint
```
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "query": "What programs does AIMS offer?",
  "session_id": "optional-uuid"
}

Response (200):
{
  "answer": "AIMS offers MBA, BBA, and Bachelor of Aviation...",
  "confidence": 68,
  "sources": [
    {
      "title": "Master of Business Administration",
      "url": "https://theaims.ac.in/...",
      "content": "MBA program details..."
    }
  ],
  "suggestions": [
    "What are MBA specializations?",
    "What is the placement rate?"
  ]
}
```

### Health Endpoint
```
GET http://localhost:8000/api/health

Response (200):
{
  "status": "healthy",
  "documents": 46,
  "faiss_synced": true
}
```

### Analytics Endpoint
```
GET http://localhost:8000/api/analytics

Response (200):
{
  "total_queries": 150,
  "avg_confidence": 48.5,
  "queries_today": 20,
  "top_questions": [...]
}
```

---

## 📈 Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Query Response Time** | <100ms | ~50ms | ✅ Excellent |
| **Confidence Score (basic data)** | - | 20-68% | ⚠️ Acceptable |
| **Confidence Score (with full data)** | 70%+ | TBD | ⏳ After data enrichment |
| **Document Retrieval** | 3-5/query | 3-5/query | ✅ Good |
| **Uptime** | 99.9% | TBD | ⏳ Monitor |
| **Concurrent Users** | 50+ | TBD | ⏳ Test load |

---

## 🎓 Learning Resources

- **RAG Architecture**: See `RAG_SETUP_GUIDE.md`
- **System Architecture**: See `SYSTEM_ARCHITECTURE.md`
- **Data Pipeline**: See `ANSWER_SOURCE_TRACE.md`
- **Integration Details**: See `INTEGRATION_TEST_COMPLETE.md`

---

## 📞 Support

For issues or questions:
1. Check `TROUBLESHOOTING` section
2. Review system logs
3. Run diagnostic scripts
4. Contact development team

---

**Last Updated**: April 19, 2024
**Version**: 1.0.0
**Status**: Production Ready
