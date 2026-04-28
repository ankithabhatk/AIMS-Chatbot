# AIMS Chatbot - Production Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Hybrid Decision Engine                 │
├─────────────────────────────────────────────────────────────┤
│  1. OUT-OF-SCOPE GUARD (Entry)                              │
│     → weather, iit bombay, etc. → controlled fallback      │
├─────────────────────────────────────────────────────────────┤
│  2. STRUCTURED KNOWLEDGE (Deterministic)                   │
│     → courses, fees, admission, contact                   │
│     → Hardcoded KB with 95%+ confidence                   │
├─────────────────────────────────────────────────────────────┤
│  3. RAG PIPELINE (Probabilistic)                            │
│     → Intent detection (fuzzy matching)                     │
│     → FAISS retrieval (k=25)                              │
│     → Program-aware filtering (MCA/MBA/BCA)               │
│     → Extract points → structured response                 │
└─────────────────────────────────────────────────────────────┘
```

## Intent Routing

| Intent | Trigger Keywords | Source | Response |
|--------|-----------------|--------|----------|
| courses | course, program, offer | Structured | Program list |
| fees | fee, cost, tuition | Structured | Fee structure |
| admission | apply, eligibility | Structured | Process steps |
| contact | phone, email, address | Structured | Contact info |
| placements | placement, job, salary | RAG | Placement overview |
| campus | hostel, facility, campus | RAG | Facilities info |
| curriculum | subjects, skills, syllabus | RAG | Technical skills |

## NLP Features

### Fuzzy Matching (80% threshold)
- "wat corses" → courses
- "mba feees" → fees  
- "admisn" → admission
- "placemnt" → placements

### Program-Aware Filtering
- Query "MCA subjects" → prioritizes MCA URLs
- Query "MBA skills" → prioritizes MBA URLs

### Out-of-Scope Guard
- weather, iit bombay, iim, cricket → controlled fallback

## Index Data

| Program | Pages | Chunks |
|---------|-------|--------|
| BBA | 2 | 24 |
| BCA | 1 | 11 |
| BCom | 1 | 13 |
| BHM | 1 | 11 |
| MBA | 1 | 10 |
| MCA | 1 | 11 |
| MCom | 1 | 9 |
| PhD | 1 | 9 |
| Placement | 1 | 4 |
| **TOTAL** | **10** | **102** |

## Fire-Test Results

| # | Test Case | Result | Status |
|---|----------|--------|--------|
| 1 | "wat corses do u hav" | Course list | ✅ |
| 2 | "What subjects are in MCA?" | Cyber Security, Game Dev | ✅ |
| 3 | "tell me about iit bombay" | Controlled fallback | ✅ |
| 4 | "mba feees pls" | ₹50,000-1,00,000 | ✅ |
| 5 | "placemnt recod" | Placement overview | ✅ |
| 6 | "what programs are offered" | Structured list | ✅ |

## Files Modified

- `backend/app/services/structured_knowledge.py` - Fuzzy matching + routing rules
- `backend/app/services/llm/intent_aware_composer.py` - Curriculum intent + program filtering
- `backend/app/api/chat_phase4.py` - Out-of-scope guard

## Dependencies

```
rapidfuzz>=3.0
faiss-cpu
sentence-transformers
numpy
```

## API Endpoint

```
POST /api/v1/chat
{
  "query": "What courses do you offer?",
  "session_id": "uuid",
  "user": {"name": "John", "email": "john@example.com"}
}
```

## Production Readiness

| Component | Status |
|-----------|--------|
| Architecture | ✅ Hybrid |
| NLP | ✅ Fuzzy matching |
| Out-of-scope | ✅ Guard |
| Program filtering | ✅ Enabled |
| Fallback handling | ✅ Controlled |
| Index quality | ✅ 102 clean docs |

**Last Updated**: 2026-04-23