# AIMS College Chatbot - Production RAG Implementation

Complete, working Retrieval Augmented Generation (RAG) chatbot for college inquiries.

## 🚀 Status: WORKING ✅

- ✅ Chat endpoint fully functional (`/api/v1/chat`)
- ✅ RAG pipeline implemented (semantic search + response generation)
- ✅ Vector embeddings working (Sentence-Transformers local model)
- ✅ FAISS index operational
- ✅ Sample data pre-loaded
- ✅ Confidence scoring + fallback logic
- ✅ Source attribution
- ✅ Processing time: ~200-300ms per query

---

## 🏗️ Architecture

### RAG Pipeline (Backend)

```
User Query
    ↓
[1] Embedding via Sentence-Transformers (local, 384-dim)
    ↓
[2] FAISS Vector Search (L2 distance)
    ↓
[3] Top-5 Semantic Retrieval
    ↓
[4] Response Generation (template or OpenAI)
    ↓
[5] Confidence Scoring
    ↓
JSON Response + Sources + Time
```

### Frontend (Next.js)

The frontend is built with [Next.js](https://nextjs.org).

---

## 📋 Quick Start

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
python test_rag.py  # Test RAG Pipeline
uvicorn app.main:app --reload
```

Backend API: http://localhost:8000/docs

### 2. Frontend Setup

```bash
npm install
npm run dev
```

Frontend UI: http://localhost:3000

---

## 📊 Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js (App Router) |
| Embeddings | Sentence-Transformers (local) |
| Vector DB | FAISS |
| Framework | FastAPI |
| Server | Uvicorn |

---

## 📚 Full Documentation

See [RAG_SETUP_GUIDE.md](RAG_SETUP_GUIDE.md) for detailed backend setup.
-application/deploying) for more details.
