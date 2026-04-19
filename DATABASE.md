# 🗄️ Database Integration Guide

## Architecture: FAISS + Supabase

This document explains how the database layer works in the AIMS College Chatbot system.

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────┐
│  User Query                         │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│ 1. Embed Query (Sentence-Transformers)
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│ 2. Search FAISS (Local, Fast)       │
│ Returns: Top-5 similar chunks       │
│ Speed: 10-20ms                      │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│ 3. Fetch Documents from Supabase    │
│ Get: Full content, metadata         │
│ Uses: Document IDs from FAISS       │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│ 4. Generate Response                │
│ Using: Retrieved full documents     │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│ 5. Log to Supabase                  │
│ Store: Query + Response + Metadata  │
│ Purpose: Analytics                  │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│ Response to Client                  │
└─────────────────────────────────────┘
```

---

## 🏗️ Components

### FAISS (Local Vector Search)
- **Purpose:** Fast semantic search
- **Location:** Memory (with disk backup in `/tmp/chatbot_faiss`)
- **Data:** Vector embeddings (384-dim)
- **Speed:** 10-20ms per query
- **Limitation:** Single machine (~1M vectors max)

### Supabase (PostgreSQL)
- **Purpose:** Persistent data storage
- **Tables:**
  - `documents` — Scraped website content
  - `leads` — Student inquiries
  - `chat_logs` — Analytics data
- **Speed:** 50-100ms per query
- **Reliability:** Cloud backup, auto-scale

---

## 📊 Database Schema

### documents Table

```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY,
  content TEXT,                -- Full chunk text
  url TEXT,                    -- Source URL
  heading TEXT,                -- Section heading
  chunk_index INTEGER,         -- Position in document
  source VARCHAR(100),         -- 'website', 'manual', etc
  tokens INTEGER,              -- Token count
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### leads Table

```sql
CREATE TABLE leads (
  id UUID PRIMARY KEY,
  name VARCHAR(255),           -- Full name
  email VARCHAR(255) UNIQUE,   -- Email (unique)
  phone VARCHAR(20),           -- Phone number
  interest TEXT,               -- Programs interested in
  source VARCHAR(100),         -- 'chatbot', 'form', etc
  lead_score FLOAT,            -- 0.0-1.0 score
  status VARCHAR(50),          -- 'new', 'qualified', etc
  last_contact TIMESTAMP,      -- Last interaction
  salesforce_id VARCHAR(255),  -- For CRM sync
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### chat_logs Table

```sql
CREATE TABLE chat_logs (
  id UUID PRIMARY KEY,
  query TEXT,                  -- User question
  response TEXT,               -- System response
  session_id VARCHAR(255),     -- Session identifier
  user_email VARCHAR(255),     -- User (optional)
  confidence_score FLOAT,      -- 0.0-1.0
  processing_time_ms INTEGER,  -- Response time
  is_fallback BOOLEAN,         -- Was fallback used?
  created_at TIMESTAMP
);
```

---

## 🚀 Setup Instructions

### 1. Environment Variables

Create `backend/.env`:

```env
SUPABASE_URL=https://ojyxisvbtfrpbivsexqh.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIs...
```

### 2. Run Migrations

Go to [Supabase Dashboard](https://app.supabase.com):

1. Select your project
2. Go to **SQL Editor**
3. Create new query
4. Copy-paste `migrations/001_init_schema.sql`
5. Click **Run**

Or run the setup script:

```bash
cd backend
python setup_database.py
```

### 3. Verify Connection

```bash
python -c "from app.services.database.supabase_client import SupabaseClient; client = SupabaseClient.get_client(); print('✅ Connected to Supabase')"
```

---

## 💻 Code Examples

### Store a Document

```python
from app.services.database.supabase_client import get_document_store

doc_store = get_document_store()

# Store a document
doc = await doc_store.store_document(
    content="AIMS is a leading college...",
    url="https://theaims.ac.in/about",
    heading="About AIMS",
    chunk_index=0
)

print(f"Stored: {doc['id']}")
```

### Capture a Lead

```python
from app.services.database.supabase_client import get_lead_store

lead_store = get_lead_store()

# Create a lead
lead = await lead_store.create_lead(
    name="John Doe",
    email="john@example.com",
    phone="+91-9876543210",
    interest="B.Tech Computer Science"
)

print(f"Lead created: {lead['id']}")
```

### Log Chat Interaction

```python
from app.services.database.supabase_client import get_chat_log_store

log_store = get_chat_log_store()

# Log a chat
log = await log_store.log_chat(
    query="What is the admission requirement?",
    response="Based on AIMS website...",
    session_id="session-123",
    confidence_score=0.85,
    processing_time_ms=250
)

print(f"Logged: {log['id']}")
```

---

## 📈 Performance Characteristics

### Chat Query Flow

| Step | Component | Time | Notes |
|------|-----------|------|-------|
| 1 | Embedding | 75ms | Local (Sentence-Transformers) |
| 2 | FAISS search | 15ms | Local vector DB |
| 3 | Supabase fetch | 50ms | Fetch 3 docs via API |
| 4 | Response gen | 100ms | Template or LLM |
| 5 | Log chat | 10ms | Async in background |
| **Total** | | **250ms** | ⚡ Fast enough for MVP |

### Scalability

| Metric | MVP | Production |
|--------|-----|-----------|
| Documents | 5-50 | 1,000-10,000 |
| Daily queries | 100 | 10,000+ |
| Storage | < 1MB | < 500MB |
| FAISS limit | N/A | 1M vectors (switch to Pinecone) |

---

## 🔄 Data Flow Examples

### Example 1: Chat with Logging

```python
# 1. User sends query
query = "What is admission fee?"

# 2. Embed (local)
embedding = embed_text(query)

# 3. Search FAISS (local)
chunks = faiss_index.search(embedding, k=5)

# 4. Fetch from Supabase (cloud)
docs = await doc_store.get_documents_by_ids(doc_ids)

# 5. Generate response
response = generator.generate(query, docs)

# 6. Log to Supabase (async)
await log_store.log_chat(
    query=query,
    response=response.text,
    session_id=session_id,
    confidence_score=response.confidence
)
```

### Example 2: Lead Capture with Deduplication

```python
# 1. User fills form
lead_data = LeadData(
    email="john@example.com",
    name="John",
    phone="+911234567890"
)

# 2. Check if exists
existing = await lead_store.get_leads_by_email(lead_data.email)

if existing:
    # Update last contact
    await lead_store.update_lead(existing[0]['id'], ...)
else:
    # Create new
    new_lead = await lead_store.create_lead(
        name=lead_data.name,
        email=lead_data.email,
        phone=lead_data.phone
    )
```

---

## 🛠️ Maintenance

### Regular Tasks

**Daily:**
- Monitor FAISS index size
- Check chat log growth
- Alert on errors

**Weekly:**
- Review lead scores
- Check Supabase quota
- Backup analytics

**Monthly:**
- Archive old logs (>30 days)
- Rebuild FAISS index
- Review performance metrics

### Rebuild FAISS Index

```bash
# From Supabase data
python -c "
from app.services.data_ingestion import ingest_college_data
import asyncio
asyncio.run(ingest_college_data())
"
```

### Export Data

```bash
# Export chat logs
curl 'https://ojyxisvbtfrpbivsexqh.supabase.co/rest/v1/chat_logs' \
  -H 'apikey: YOUR_KEY' \
  -H 'Authorization: Bearer YOUR_JWT'
```

---

## 🚨 Troubleshooting

### Connection Issues

```
Error: "Failed to initialize Supabase"
Solution: Check SUPABASE_URL and SUPABASE_ANON_KEY in .env
```

### Table Not Found

```
Error: "relation 'documents' does not exist"
Solution: Run migrations via Supabase Dashboard
```

### FAISS Index Corrupted

```
Error: "FAISS index corrupted"
Solution: 
  1. rm -rf /tmp/chatbot_faiss
  2. Restart server (rebuilds from Supabase)
```

---

## 📚 References

- [Supabase Docs](https://supabase.com/docs)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Sentence-Transformers](https://www.sbert.net/)

---

## 🔐 Security Notes

- Anon key for public queries (limited access)
- Service role key for admin operations (keep secret!)
- RLS (Row Level Security) can be enabled per table
- Use environment variables for all secrets
- Rotate keys regularly

---

**Last Updated:** 2026-04-19  
**Maintainer:** Solo Dev  
**Status:** ✅ Active
