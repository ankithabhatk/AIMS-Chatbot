# Data Ingestion Execution Checklist

**Status:** Waiting for college data  
**Started:** April 19, 2026  
**Goal:** Improve answer rate from 32% → 70%+

---

## Phase 1: Data Collection (Week 1)

### ✅ Requested Data
- [ ] Fee structure document (PDF/Excel)
- [ ] Placement report (last 3 years, PDF/Excel)
- [ ] Campus facilities guide (PDF or document)
- [ ] Admission requirements (PDF or text)
- [ ] Scholarship/financial aid information (PDF/JSON/structured)

### ✅ File Organization
```
/data/
├── raw/
│   ├── fees/
│   │   └── [place fee documents here]
│   ├── placements/
│   │   └── [place placement reports here]
│   ├── facilities/
│   │   └── [place facility guides here]
│   ├── admissions/
│   │   └── [place admission docs here]
│   └── scholarships/
│       └── [place scholarship info here]
├── processed/
│   └── [output from document_processor.py]
└── ingestion_logs/
    └── [merge logs and snapshots]
```

---

## Phase 2: Processing (Once data arrives)

### ✅ Extraction
```bash
# Run document processor
python backend/scripts/ingest.py --source-dir /data/raw --output-file /data/processed/extracted.json
```

**Expected output:**
- `extracted.json` with structured chunks
- Each chunk: `{source, type, section, text, metadata}`
- Total chunks: 100–200 (from college data)

### ✅ Merge Safety
```bash
# Check for duplicates before merge
python backend/app/services/ingestion/merge_external_data.py --check-duplicates /data/processed/extracted.json
```

### ✅ Merge with Rollback
```bash
# Safe merge with auto-snapshot
python backend/app/services/ingestion/merge_external_data.py --merge /data/processed/extracted.json
```

**Expected outcome:**
- FAISS expanded from 46 → 150+ documents
- Auto-snapshot created at `/tmp/chatbot_faiss/snapshots/`
- All metadata updated

---

## Phase 3: Validation (Week 2)

### ✅ Re-test Same 30 Queries
```bash
# Run validation test
python backend/scripts/test_reliability_30queries.py
```

**Success metrics:**
- Answer rate: 32% → 50%–70%+
- Fallback rate: 68% → 30%–50%
- Avg confidence: 0.367 → 0.50+

### ✅ Focus Areas to Re-test
```text
Fee queries:         "What is MBA fees?" (currently 0% answer)
Placement queries:   "What is placement rate?" (currently 0% answer)
Facility queries:    "Does AIMS have gym?" (currently 0% answer)
Scholarship queries: "Are there scholarships?" (currently 0% answer)
```

### ✅ Track Improvements
```json
{
  "before": {
    "answer_rate": 0.32,
    "fallback_rate": 0.68,
    "avg_confidence": 0.367
  },
  "after": {
    "answer_rate": "TBD",
    "fallback_rate": "TBD",
    "avg_confidence": "TBD"
  }
}
```

---

## Phase 4: Production Deployment (Week 3)

### ✅ Verification
- [ ] No regressions (previous answers still work)
- [ ] New answers are accurate (random sample)
- [ ] API response time < 200ms
- [ ] Database synced and stable

### ✅ Deployment
- [ ] Restart API with new FAISS index
- [ ] Monitor `/api/v1/stats` for query patterns
- [ ] Log any failures

---

## Tools & Commands Ready

### Document Processor
```python
from backend.app.services.ingestion.document_processor import get_document_processor

processor = get_document_processor()
results = processor.batch_ingest_directory("/data/raw")
# Returns: {total_chunks, files_processed, errors}
```

### Merge Pipeline
```python
from backend.app.services.ingestion.merge_external_data import IncrementalMergePipeline

pipeline = IncrementalMergePipeline()
result = pipeline.safe_merge("extracted.json", snapshot_name="before_college_data")
# Returns: {success, before_doc_count, after_doc_count, merge_time}
```

### Test Suite
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Stats check
curl http://localhost:8000/api/v1/stats

# Query test
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is MBA fees?"}'
```

---

## Troubleshooting

### If merge fails:
1. Check snapshot exists: `ls /tmp/chatbot_faiss/snapshots/`
2. Rollback: `python backend/app/services/ingestion/merge_external_data.py --rollback`
3. Fix source data and retry

### If answer rate doesn't improve:
1. Check extraction quality: `head -50 /data/processed/extracted.json`
2. Verify chunks are meaningful
3. Re-run with better preprocessing

### If API crashes:
1. Check logs: `tail -100 /tmp/chatbot_logs/queries.jsonl`
2. Verify FAISS index: `curl http://localhost:8000/api/v1/health`
3. Restart: `python -m uvicorn backend.app.main:app --reload`

---

## Success Criteria

```text
✅ ALL 5 data categories extracted
✅ Answer rate improved to 50%+
✅ No regressions in existing answers
✅ API stable (no crashes)
✅ Metadata complete for all chunks
```

---

## Timeline

```
NOW (Apr 19):       Send data request to college
Week 1 (Apr 22):    Receive documents
Week 2 (Apr 29):    Process & merge data
Week 3 (May 6):     Validate & deploy
```

---

## Notes

- Do NOT modify FAISS while waiting (it's stable)
- Do NOT add new features until data improves answer rate
- Do save this checklist and track progress
- Do celebrate when answer rate hits 70%+ ✅

