# Beta Deployment Guide

**Status**: Ready to deploy  
**Target Users**: 10-20 beta testers  
**Duration**: 2-4 weeks  
**Goal**: Collect real user behavior patterns

---

## Pre-Deployment Checklist

- [x] All 3 fixes implemented
- [x] Nonsense detection refined (domain words protected)
- [x] System tested with corrected test
- [x] Fallback rate documented (64.3%)
- [ ] Staging deployment
- [ ] Manual smoke test
- [ ] Beta user recruitment
- [ ] Logging setup
- [ ] Weekly review scheduled

---

## What to Deploy

**Files Modified**:
1. `backend/app/services/input_handler.py` - Enhanced nonsense detection
2. `backend/app/services/structured_knowledge.py` - Program intent mapping
3. `backend/app/services/orchestration/engine.py` - Program fallback routing

**No breaking changes** - all modifications are additive and backward compatible.

---

## Deployment Steps

### Step 1: Staging Deployment
```bash
# Deploy to staging environment
# Run smoke tests with 5 sample queries
```

### Step 2: Manual Smoke Test
Test these 5 queries:
1. "What are the fees for MBA?" → Should get fees info
2. "Tell me about BCA" → Should get course info
3. "asdfgh" → Should fallback gracefully
4. "hi" → Should greet
5. "admisson process" → Should correct typo and show admission info

### Step 3: Beta User Recruitment
- Recruit 10-20 users
- Preferably students/parents interested in AIMS
- Mix of tech-savvy and non-tech users

### Step 4: Logging Setup
Add logging for 3 metrics per query:
```python
{
    "query": "user input",
    "useful": true/false,  # Did they find answer helpful?
    "fallback": true/false,  # Did system fallback?
    "intent": "what user actually meant"  # Free text
}
```

### Step 5: Weekly Review
- Collect queries from week
- Identify patterns
- Note language variations
- Plan next week's improvements

---

## What to Expect

### Good Signs ✅
- Users can ask questions naturally
- Most queries get useful answers
- Fallback is graceful (doesn't confuse users)
- Users provide feedback

### Warning Signs ⚠️
- Users ask same question multiple ways (language variation)
- Specific topics get consistent fallbacks
- Users get frustrated with fallback messages
- Typos cause failures

### Red Flags 🔴
- System crashes
- Completely wrong answers
- Users can't recover from fallback
- High bounce rate

---

## Data Collection Format

For each query, log:

```json
{
    "timestamp": "2026-04-28T18:45:00Z",
    "user_id": "user_123",
    "query": "what are the fees for bca",
    "response": "BCA fees are...",
    "useful": true,
    "fallback": false,
    "intent": "fees_inquiry",
    "notes": "User satisfied with answer"
}
```

---

## Weekly Review Template

### Week 1 Review
```
Total queries: X
Useful responses: Y%
Fallback rate: Z%

Top patterns:
1. Users ask "cost" instead of "fees"
2. Users ask "stay" instead of "hostel"
3. Users ask "placement" instead of "job"

Weird queries:
1. "is bca worth it"
2. "which course is best"
3. "can i get scholarship"

Failures:
1. "python course" → fallback (should be curriculum)
2. "campus life" → fallback (should be campus info)
3. "how to apply" → unclear routing
```

---

## What NOT to Do During Beta

❌ **Don't**:
- Add new intent rules mid-beta
- Change thresholds
- Add keywords
- Implement new features
- Optimize based on single queries

✅ **Do**:
- Observe patterns
- Take notes
- Collect data
- Ask users for feedback
- Stay consistent

---

## Success Metrics

### Primary (Track Weekly)
- Useful response rate (target: > 70%)
- Fallback rate (target: < 50% by end of beta)
- User satisfaction (qualitative)

### Secondary (Track for patterns)
- Most common query types
- Most common fallback triggers
- Language variations for same intent
- Typo patterns

### Don't Track (Too early)
- Confidence scores
- Intent detection accuracy
- System performance metrics
- Keyword match rates

---

## After Beta (Week 3-4)

### Analyze Patterns
- What queries failed most?
- What language variations appeared?
- What intents were missing?

### Make 1-2 Changes
- Add 1-2 new intent mappings (based on real data)
- Adjust 1-2 keywords (based on real queries)
- Remove 1-2 unused paths (simplify)

### Stabilize
- Lock final behavior
- Document patterns
- Prepare for production

---

## Fallback Message

Current fallback is:
```
"I didn't quite understand that. Could you please rephrase your question about AIMS college?"
```

This is:
- ✅ Clear
- ✅ Helpful (suggests rephrasing)
- ✅ Not frustrating

Keep it as-is during beta.

---

## Communication with Beta Users

### Onboarding
"We're testing a new AI assistant for AIMS. Please ask questions naturally. Your feedback helps us improve."

### During Beta
"Thank you for using the assistant. If you get unclear answers, please let us know what you meant."

### Feedback Collection
"What did you think of the assistant? What could we improve?"

---

## Contingency Plan

### If Fallback Rate > 70%
- Review logging data
- Check if system is working correctly
- Verify no regressions
- Consider extending beta

### If Users Report Confusion
- Improve fallback message
- Add clarification prompts
- Simplify routing logic

### If Specific Intent Fails Consistently
- Note the pattern
- Plan fix for post-beta
- Don't fix mid-beta

---

## Timeline

**Week 1**: Deploy, observe, collect data  
**Week 2**: Continue observing, identify patterns  
**Week 3**: Analyze, plan 1-2 improvements  
**Week 4**: Implement improvements, stabilize  

---

## Key Principle

**Observe first, improve second.**

Don't optimize based on assumptions. Let real users show you what matters.

---

## Status

✅ System ready for beta  
✅ Logging ready  
✅ Checklist ready  
✅ Ready to learn from real users  

**Next**: Deploy and observe.
