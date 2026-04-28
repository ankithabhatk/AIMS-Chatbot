# Log Analysis Template

**After collecting 100 queries, fill this out to identify patterns.**

---

## Quick Stats

```
Total queries collected: ___
Date range: ___ to ___
Number of users: ___
Average queries per user: ___
```

---

## Success Breakdown

| Category | Count | % | Status |
|----------|-------|---|--------|
| Successful (structured) | ___ | __% | ✅ |
| Successful (tool) | ___ | __% | ✅ |
| Fallback (unknown intent) | ___ | __% | ⚠️ |
| Fallback (error) | ___ | __% | ❌ |
| **TOTAL** | **___** | **100%** | |

**Success rate: ___%**

---

## Top 15 Failed Queries

Copy the queries that triggered fallback or returned wrong answers.

| # | Query | Detected Intent | Should Be | Category |
|---|-------|-----------------|-----------|----------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |
| 10 | | | | |
| 11 | | | | |
| 12 | | | | |
| 13 | | | | |
| 14 | | | | |
| 15 | | | | |

---

## Failure Categories

Count failures by type:

| Category | Count | % | Examples |
|----------|-------|---|----------|
| **Missing keywords** | ___ | __% | "bca cost" (cost not in fees keywords) |
| **New intent** | ___ | __% | "is bca good" (no career advice intent) |
| **Severe typo** | ___ | __% | "colage" (edit distance > 1) |
| **Messy input** | ___ | __% | "bca fees and hostel???" |
| **Ambiguous query** | ___ | __% | "what" (too vague) |
| **Out of domain** | ___ | __% | "what's the weather" |
| **Other** | ___ | __% | |
| **TOTAL** | **___** | **100%** | |

---

## Missing Keywords (Highest Priority)

These are queries that should have matched an intent but didn't because a keyword was missing.

| Intent | Missing Keyword | Example Query | Count |
|--------|-----------------|----------------|-------|
| fees | | | |
| admission | | | |
| placements | | | |
| hostel | | | |
| courses | | | |
| about_aims | | | |
| why_aims | | | |
| aims_features | | | |

**Action:** Add these keywords to `INTENT_KEYWORDS` in `engine.py`

---

## New Intents Discovered (Medium Priority)

These are queries that don't fit existing intents but appear multiple times.

| New Intent | Keywords | Example Queries | Count |
|------------|----------|-----------------|-------|
| | | | |
| | | | |
| | | | |

**Action:** Create new intents if count > 3

---

## Typo Patterns (Medium Priority)

These are typos that SymSpell couldn't correct (edit distance > 1).

| Typo | Correct | Edit Distance | Count |
|------|---------|----------------|-------|
| | | | |
| | | | |
| | | | |

**Action:** Add common misspellings to dictionary or increase edit distance

---

## Messy Input Patterns (Low Priority)

These are queries with punctuation, multiple intents, or unusual formatting.

| Pattern | Example | Count |
|---------|---------|-------|
| Multiple intents + punctuation | "bca fees and hostel???" | |
| Repeated words | "fees fees fees" | |
| Mixed case | "BCA FEES" | |
| Special characters | "bca@fees" | |

**Action:** Improve punctuation handling if count > 5

---

## Recommended Fixes (Priority Order)

### Fix 1: Add Missing Keywords
**Effort:** 5 minutes  
**Impact:** Fixes __% of failures

```python
# In engine.py, update INTENT_KEYWORDS:
INTENT_KEYWORDS["fees"].extend([...])
INTENT_KEYWORDS["admission"].extend([...])
# etc.
```

**Keywords to add:**
- 
- 
- 

### Fix 2: Create New Intent (if needed)
**Effort:** 30 minutes  
**Impact:** Fixes __% of failures

**New intent name:** ___  
**Keywords:** 
- 
- 
- 

**Response template:**
```
[Your response template here]
```

### Fix 3: Improve Typo Handling (if needed)
**Effort:** 1 hour  
**Impact:** Fixes __% of failures

**Common misspellings to add:**
- 
- 
- 

### Fix 4: Messy Input Handling (if needed)
**Effort:** 2 hours  
**Impact:** Fixes __% of failures

**Changes needed:**
- 
- 
- 

---

## Implementation Plan

**Week 1 (After analysis):**
- [ ] Implement Fix 1 (missing keywords)
- [ ] Test with 10 new queries
- [ ] Verify success rate improved

**Week 2:**
- [ ] Implement Fix 2 (new intent) if needed
- [ ] Test with 10 new queries
- [ ] Verify success rate improved

**Week 3:**
- [ ] Implement Fix 3 (typo handling) if needed
- [ ] Test with 10 new queries
- [ ] Verify success rate improved

**Week 4:**
- [ ] Implement Fix 4 (messy input) if needed
- [ ] Test with 10 new queries
- [ ] Verify success rate improved

---

## Success Metrics After Fixes

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Success rate | __% | __% | 95%+ |
| Intent accuracy | __% | __% | 95%+ |
| Typo correction | __% | __% | 90%+ |
| Multi-intent | __% | __% | 85%+ |

---

## Key Insights

**What surprised you?**
- 
- 
- 

**What worked better than expected?**
- 
- 
- 

**What needs most improvement?**
- 
- 
- 

---

## Next Steps

1. Deploy to users
2. Collect 100 queries
3. Fill out this template
4. Implement fixes in priority order
5. Retest and iterate

**This is how real systems improve.**

