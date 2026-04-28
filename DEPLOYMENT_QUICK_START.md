# QUICK START: Production Deployment

## 1️⃣ Understand (5 minutes)

Read these IN THIS ORDER:
1. [CRITICAL_FIXES_APPLIED.md](CRITICAL_FIXES_APPLIED.md) — What changed
2. [FINAL_PIPELINE_INTEGRATION.md](FINAL_PIPELINE_INTEGRATION.md) — How to integrate
3. [OBSERVABILITY_LAYER.md](OBSERVABILITY_LAYER.md) — How to monitor

## 2️⃣ Integrate (10 minutes)

Apply changes from FINAL_PIPELINE_INTEGRATION.md to `chat_phase4.py`:
- Replace import statements
- Update chat endpoint to use ProductionPipeline
- Test locally

```bash
cd backend
python -m uvicorn app.main:app --reload  # Verify no errors
```

## 3️⃣ Baseline (5 minutes)

Run evaluation before deploying:

```bash
cd backend
python eval_harness.py
# Saves: eval_results.json, eval_summary.json, eval_health.json
```

Check health status:
```bash
cat eval_health.json | jq '.overall'
# Should show: "HEALTHY"
```

## 4️⃣ Deploy (5 minutes)

Push to production with confidence.

## 5️⃣ Monitor (Ongoing)

After deployment, run harness regularly:

```bash
# Weekly or after changes
python eval_harness.py

# Compare with baseline
diff baseline_summary.json eval_summary.json

# Check if health degraded
cat eval_health.json | jq '.overall'
```

---

## Key Metrics to Watch

| Metric | Good | Warning | Bad |
|--------|------|---------|-----|
| fallback_rate | < 10% | 10-15% | > 15% |
| avg_score | > 0.75 | 0.60-0.75 | < 0.60 |
| latency_ms | < 2000 | 2000-3000 | > 3000 |
| slow_response_pct | < 5% | 5-10% | > 10% |
| weak_answer_pct | < 10% | 10-20% | > 20% |

---

## If Something Breaks

**High fallback rate?**
```bash
# See which queries are failing:
cat eval_results.json | jq '.[] | select(.fallback == true) | .query'
# → Add missing data to KB → Re-index → Re-test
```

**Low score?**
```bash
# See weak answers:
cat eval_summary.json | jq '.weak_samples'
# → Check LLM output → Improve prompt → Re-test
```

**Slow responses?**
```bash
# See slow queries:
cat eval_summary.json | jq '.slow_samples'
# → Enable caching → Check LLM tier → Re-test
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `final_pipeline.py` | Core pipeline (9-step) |
| `chat_phase4.py` | API endpoint |
| `eval_harness.py` | Testing + monitoring |
| CRITICAL_FIXES_APPLIED.md | What changed |
| FINAL_PIPELINE_INTEGRATION.md | How to integrate |
| OBSERVABILITY_LAYER.md | How to monitor |
| PRODUCTION_READY.md | Full guide |

---

## Success Criteria

✅ Harness shows: HEALTHY  
✅ fallback_rate < 10%  
✅ avg_score > 0.75  
✅ latency_ms < 2000  
✅ No regressions after changes  

---

## TL;DR

1. Read 3 docs (15 min)
2. Apply code changes (10 min)
3. Run baseline test (5 min)
4. Deploy (5 min)
5. Monitor with harness (ongoing)

**Total time to production: ~35 minutes**

🚀 You're ready to deploy.
