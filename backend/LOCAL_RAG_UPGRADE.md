# Local RAG Upgrade

This backend now runs as a fully local, extractive-first assistant.

## What Changed

- Added a deterministic query preprocessing pipeline:
  - lowercase normalization
  - punctuation cleanup
  - slang expansion
  - local spell correction
  - fuzzy course/topic detection
  - synonym mapping
- Reworked session memory so follow-ups inherit active course/topic safely without concatenating whole prior queries.
- Replaced raw FAISS-only lookup in the live chat route with hybrid retrieval:
  - vector similarity
  - keyword overlap
  - metadata-aware boosts and penalties
- Added dynamic confidence scoring and a three-level reliability ladder:
  - clarification for unclear queries
  - best-available snippet for low confidence
  - safe fallback for no reliable match
- Rebuilt the local FAISS pipeline around cosine-compatible indexing.
- Added an offline rebuild script that uses local metadata and bundled official knowledge only.
- Added a local evaluation dataset and evaluator.

## Key Files

- `app/api/chat.py`
- `app/services/query_processing.py`
- `app/services/intelligence_layer.py`
- `app/services/taxonomy.py`
- `app/services/retrieval/hybrid_retriever.py`
- `app/services/retrieval/faiss_index.py`
- `app/services/retrieval/faiss_builder.py`
- `scripts/rebuild_local_index.py`
- `scripts/generate_eval_dataset.py`
- `scripts/evaluate_local_rag.py`

## Offline Rebuild

Run from `backend/`:

```powershell
python scripts\rebuild_local_index.py
```

This rebuilds `app/data/faiss_index/` from local content only.

## Evaluation

Generate dataset:

```powershell
python scripts\generate_eval_dataset.py
```

Run evaluation:

```powershell
python scripts\evaluate_local_rag.py
```

Outputs:

- `scripts/eval_dataset_local.json`
- `scripts/evaluation_log_local.json`
- `scripts/evaluation_report_local.json`

## Notes

- No Ollama is used.
- No external API is required for retrieval or response generation.
- The response engine remains extractive-first to minimize hallucination risk.
