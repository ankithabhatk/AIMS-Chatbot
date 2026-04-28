# Real User Testing Plan

**Objective**: Deploy to controlled users, collect 100 queries, analyze patterns, fix systematically.

**Timeline**: This week (deploy) → Next week (analyze & fix)

---

## Phase 1: Deployment Setup (Today)

### What to Deploy

Your current system is ready. No changes needed.

**Deployment checklist:**
- [ ] Backend running on production server
- [ ] Frontend accessible to test users
- [ ] Logging enabled (already done)
- [ ] Database connected
- [ ] Error tracking working

### Who to Test With

**Target: 10-20 controlled users**

- Students from AIMS (if possible)
- Friends/colleagues who understand the context
- NOT random internet users (yet)

**Why controlled?**
- You can ask follow-up questions
- You can observe behavior
- You can identify patterns quickly

### What to Tell Them

**Simple brief:**
> "We're testing a new AIMS chatbot. Ask it anything about the college — fees, admission, courses, facilities, etc. Be natural. Type like you normally would."

**Don't say:**
- "It's AI-powered" (sets wrong expectations)
- "It's perfect" (they'll be gentle)
- "We're testing spell correction" (biases behavior)

---

## Phase 2: Logging Configuration (Today)

### What You're Already Logging

✅ Query  
✅ Intent  
✅ Mode  
✅ Timestamp  

### What You Need to ADD

Add this to your logging (in `engine.py`):

```python
def log_query_event(query: str, corrected_query: str, intent: str, 
                    multi_intents: List[str], mode: str, 
                    fallback: bool, response: str, session_id: str):
    """Log complete query event for analysis."""
    
    event = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "corrected_query": corrected_query,
        "query_length": len(query),
        "intent": intent,
        "multi_intents": multi_intents,
        "mode": mode,  # "structured", "tool", "counselor", "fallback"
        "fallback": fallback,
        "response_length": len(response),
        "response_preview": response[:100],  # First 100 chars
    }
    
    # Log to file (for analysis)
    logger.info(f"[QUERY_EVENT] {json.dumps(event)}")
    
    # Also save to database for easy querying
    save_query_event_to_db(event)
```

### Log File Location

Create: `logs/query_events.jsonl`

Each line is a complete query event (JSON).

---

## Phase 3: Collection Period (This Week)

### Duration

**Target: 100 queries minimum**

- 10-20 users × 5-10 queries each = 50-200 queries
- Collect for 3-5 days
- Don't rush

### What NOT to Do

❌ Don't fix bugs during collection  
❌ Don't change code  
❌ Don't optimize  
❌ Don't add features  

**Why?** You need to see real behavior, not your assumptions.

### What to Monitor

- System uptime
- Error rates
- Response times
- User feedback (informal)

---

## Phase 4: Analysis (Next Week)

### Step 1: Extract Query Log

```bash
# Extract all queries from logs
cat logs/query_events.jsonl | jq '.query' > queries.txt

# Count total
wc -l queries.txt
```

### Step 2: Categorize Failures

Use this simple sheet:

| Query | Intent | Mode | Fallback? | Issue | Category |
|-------|--------|------|-----------|-------|----------|
| "bca cost" | fees | structured | No | ✅ Works | - |
| "admision process" | admission | structured | No | ✅ Works (typo corrected) | - |
| "hostel price" | ??? | fallback | Yes | ❌ Unknown intent | Missing keyword |
| "aims worth it" | ??? | fallback | Yes | ❌ Unknown intent | New intent |
| "colage fees" | ??? | fallback | Yes | ❌ Typo too severe | Spell correction limit |

### Step 3: Identify Top Issues

**Expected patterns:**

1. **Missing keywords** (40% of failures)
   - "bca cost" → fees (but "cost" not in keywords)
   - "hostel price" → hostel (but "price" not in keywords)

2. **New intents** (30% of failures)
   - "aims worth it" → new intent (value proposition)
   - "is bca good" → new intent (career advice)

3. **Severe typos** (20% of failures)
   - "colage" → college (edit distance > 1)
   - "plcements" → placements (edit distance > 1)

4. **Messy input** (10% of failures)
   - "bca fees and hostel and placements???"
   - Multiple intents + punctuation chaos

### Step 4: Prioritize Fixes

**Fix in this order:**

1. **Add missing keywords** (highest ROI)
   - Takes 5 minutes
   - Fixes 40% of failures

2. **Handle new intents** (if pattern clear)
   - Takes 30 minutes
   - Fixes 30% of failures

3. **Improve typo handling** (if needed)
   - Takes 1 hour
   - Fixes 20% of failures

4. **Messy input handling** (last)
   - Takes 2 hours
   - Fixes 10% of failures

---

## Log Analysis Sheet (Simple Version)

Create this file: `ANALYSIS_AFTER_100_QUERIES.md`

```markdown
# Analysis After 100 Queries

## Summary
- Total queries: 100
- Successful: 85 (85%)
- Fallback: 15 (15%)

## Top 10 Failed Queries

| # | Query | Intent Detected | Should Be | Fix |
|---|-------|-----------------|-----------|-----|
| 1 | "bca cost" | None | fees | Add "cost" keyword |
| 2 | "hostel price" | None | hostel | Add "price" keyword |
| 3 | "aims worth it" | None | NEW | Create new intent |
| ... | ... | ... | ... | ... |

## Issues by Category

| Category | Count | % | Fix Effort | Impact |
|----------|-------|---|------------|--------|
| Missing keywords | 6 | 40% | 5 min | High |
| New intents | 5 | 33% | 30 min | High |
| Severe typos | 2 | 13% | 1 hour | Medium |
| Messy input | 2 | 13% | 2 hours | Low |

## Recommended Fixes (Priority Order)

### Fix 1: Add Keywords (5 minutes)
```python
INTENT_KEYWORDS["fees"].extend(["cost", "price", "charges"])
INTENT_KEYWORDS["hostel"].extend(["price", "accommodation"])
```

### Fix 2: New Intent (30 minutes)
```python
# Add "value_proposition" intent
# Keywords: "worth", "good", "best", "why choose"
```

### Fix 3: Typo Handling (1 hour)
```python
# Increase max_edit_distance to 2 for specific words
# Or add common misspellings to protected words
```

## Next Steps
- [ ] Implement Fix 1
- [ ] Test with 10 new queries
- [ ] Implement Fix 2
- [ ] Test with 10 new queries
- [ ] Repeat until 95%+ success rate
```

---

## What You'll Actually See (Realistic Predictions)

### Prediction 1: Missing Keywords (Most Common)

**Query:** "bca cost"  
**Current:** Fallback (no intent detected)  
**Why:** "cost" not in fees keywords  
**Fix:** Add "cost" to fees keywords (1 line)

### Prediction 2: New Intent Emerges

**Query:** "is bca good"  
**Current:** Fallback  
**Why:** No intent for "career advice"  
**Fix:** Create new intent with keywords (5 lines)

### Prediction 3: Typo Limits

**Query:** "colage fees"  
**Current:** Fallback (typo too severe)  
**Why:** "colage" → "college" is edit distance 2  
**Fix:** Add common misspellings to dictionary (10 lines)

### Prediction 4: Messy Input

**Query:** "bca fees and hostel and placements???"  
**Current:** Partial success (detects some intents)  
**Why:** Punctuation + multiple intents  
**Fix:** Better punctuation handling (5 lines)

---

## Success Metrics

### After 100 Queries

| Metric | Target | How to Measure |
|--------|--------|-----------------|
| Success rate | 85%+ | Count non-fallback responses |
| Intent accuracy | 90%+ | Manual review of detected intents |
| Typo correction | 80%+ | Check corrected queries |
| Multi-intent | 70%+ | Count multi-intent queries that worked |

### After Fixes

| Metric | Target | How to Measure |
|--------|--------|-----------------|
| Success rate | 95%+ | Retest with 50 new queries |
| Intent accuracy | 95%+ | Manual review |
| Typo correction | 90%+ | Check corrected queries |
| Multi-intent | 85%+ | Count multi-intent queries that worked |

---

## Deployment Checklist

### Before Deploying

- [ ] Backend running
- [ ] Frontend accessible
- [ ] Logging enabled
- [ ] Database connected
- [ ] Error tracking working
- [ ] Test with 5 queries manually

### During Collection

- [ ] Monitor system uptime
- [ ] Check error logs daily
- [ ] Collect user feedback (informal)
- [ ] Don't make changes

### After Collection

- [ ] Extract query log
- [ ] Categorize failures
- [ ] Identify top issues
- [ ] Prioritize fixes
- [ ] Implement fixes
- [ ] Retest

---

## Timeline

| When | What | Duration |
|------|------|----------|
| Today | Deploy + setup logging | 2 hours |
| This week | Collect 100 queries | 3-5 days |
| Next week | Analyze + fix top issues | 2-3 hours |
| Following week | Retest + iterate | 1-2 hours |

---

## Key Principle

**Observe → Analyze → Fix → Repeat**

Not:

**Predict → Build → Hope → Fail**

---

## Final Checklist

- [ ] Deploy to controlled users (10-20)
- [ ] Collect 100 queries
- [ ] Log everything (query, intent, mode, fallback)
- [ ] Analyze failures
- [ ] Fix top 3 issues
- [ ] Retest
- [ ] Repeat

**This is how real systems improve.**

