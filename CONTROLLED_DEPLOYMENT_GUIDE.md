# Controlled Deployment Guide

**Status**: Ready for 10-20 controlled users  
**Phase**: Reality Validation  
**Goal**: Collect real queries to identify hidden patterns

---

## Pre-Deployment Checklist

- [ ] Backend running
- [ ] Frontend accessible
- [ ] Logging enabled
- [ ] Database connected
- [ ] Test with 5 queries manually

---

## Deployment Instructions

### Step 1: Recruit Users (Today)

**Target**: 10-20 controlled users
- Students from AIMS (if possible)
- Friends/colleagues who understand context
- NOT random internet users

**What to tell them:**
```
"We're testing a new AIMS chatbot. Ask it anything about the college 
— fees, admission, courses, facilities, etc. Be natural. Type like you normally would."
```

**What NOT to tell them:**
- "It's AI-powered" (sets wrong expectations)
- "It's perfect" (they'll be gentle)
- "We're testing spell correction" (biases behavior)

---

## Step 2: Log These 4 Things (CRITICAL)

For **every query**, capture:

```json
{
  "session_id": "user_123",
  "timestamp": "2026-04-28T10:30:00Z",
  "query": "What is AIMS and fees for BCA",
  "detected_intents": ["about_aims", "fees"],
  "final_response": "About AIMS: ... Fees: ...",
  "fallback": false,
  "response_time_ms": 245
}
```

**Why these 4?**
1. **Query** - What user actually asked
2. **Detected intents** - What system understood
3. **Final response** - What user saw
4. **Fallback** - Did system fail?

---

## Step 3: Watch for These Patterns

### Pattern 1: Over-Triggering Rules

**What to look for:**
```
User: "Tell me about AIMS advantages"
System detects: why_aims (correct)
System removes: about_aims (WRONG - rule too strict)
Result: Missing information
```

**Log it as:** `rule_conflict`

### Pattern 2: Missed Natural Language

**What to look for:**
```
User: "What's the accommodation cost?"
System: Doesn't detect hostel (keyword "accommodation" not in rule)
Result: Fallback
```

**Log it as:** `missed_keyword`

### Pattern 3: Rule Conflicts

**What to look for:**
```
User: "Why AIMS and what is AIMS?"
System: Detects both why_aims and about_aims
System: Removes about_aims (rule says remove it)
Result: Incomplete answer
```

**Log it as:** `rule_conflict`

### Pattern 4: Unexpected Phrasing

**What to look for:**
```
User: "hostel price"
System: Doesn't detect hostel (keyword "price" not in hostel keywords)
Result: Fallback
```

**Log it as:** `unexpected_phrasing`

---

## Step 4: Collection Period

**Duration**: 3-5 days  
**Target**: 50-100 queries minimum

**What to monitor:**
- System uptime
- Error rates
- Response times
- User feedback (informal)

**What NOT to do:**
- Don't fix bugs during collection
- Don't change code
- Don't optimize
- Don't add features

---

## Step 5: Analysis (After Collection)

### Extract Query Log

```bash
# Get all queries
cat logs/query_events.jsonl | jq '.query' > queries.txt

# Count total
wc -l queries.txt
```

### Categorize Issues

| Pattern | Count | Examples |
|---------|-------|----------|
| Over-triggering rules | ___ | |
| Missed natural language | ___ | |
| Rule conflicts | ___ | |
| Unexpected phrasing | ___ | |

### Identify Top Issues

Focus on:
1. Most common pattern
2. Highest impact pattern
3. Easiest to fix pattern

---

## What You'll Likely See

### Prediction 1: Over-Triggering Rules (30%)

**Example:**
```
User: "Tell me about AIMS and why it's good"
System detects: about_aims, why_aims
System removes: about_aims (rule says remove it)
Result: User gets incomplete answer
```

**Why:** Rules are too strict for natural language

### Prediction 2: Missed Keywords (40%)

**Example:**
```
User: "What's the accommodation cost?"
System: Doesn't detect hostel (keyword "accommodation" not in rule)
Result: Fallback
```

**Why:** Users don't use exact keywords

### Prediction 3: Unexpected Phrasing (20%)

**Example:**
```
User: "bca cost"
System: Detects fees (good)
But also detects: location (bad - "cost" matched something)
Result: Extra information
```

**Why:** Keywords overlap

### Prediction 4: Edge Cases (10%)

**Example:**
```
User: "fees and hostel and placements"
System: Detects all three
But order is wrong
Result: Confusing response
```

**Why:** Real queries are messier than tests

---

## Success Metrics

### After 50 Queries

| Metric | Target | How to Measure |
|--------|--------|-----------------|
| Fallback rate | < 20% | Count fallback=true |
| Rule conflicts | < 5% | Count rule_conflict logs |
| Missed keywords | < 10% | Count missed_keyword logs |
| Unexpected phrasing | < 10% | Count unexpected_phrasing logs |

### After 100 Queries

| Metric | Target | How to Measure |
|--------|--------|-----------------|
| Fallback rate | < 15% | Count fallback=true |
| Rule conflicts | < 3% | Count rule_conflict logs |
| Missed keywords | < 5% | Count missed_keyword logs |
| Unexpected phrasing | < 5% | Count unexpected_phrasing logs |

---

## Important Reminders

### DO NOT

❌ Add more rules now  
❌ Try to reach 100% accuracy  
❌ Optimize for edge cases  
❌ Fix bugs during collection  
❌ Guide users ("Try asking about fees")  

### DO

✅ Deploy to real users  
✅ Let them type naturally  
✅ Log everything  
✅ Observe patterns  
✅ Stay silent  

---

## After Collection

### Bring to Review

When you have 20-30 real queries:
1. Identify hidden patterns
2. Simplify rules (prevent explosion)
3. Adjust based on reality
4. Prepare for next iteration

---

## Key Principle

**You are now in Reality Validation Phase.**

Not tuning.  
Not fixing.  
Not optimizing.  

**Just observing.**

---

## Timeline

| When | What | Duration |
|------|------|----------|
| Today | Deploy to users | 2 hours |
| This week | Collect 50-100 queries | 3-5 days |
| Next week | Analyze patterns | 2-3 hours |
| Following week | Adjust rules based on data | 1-2 hours |

---

## Final Checklist

- [ ] Users recruited (10-20)
- [ ] Logging configured (4 fields)
- [ ] System deployed
- [ ] Manual test (5 queries)
- [ ] Ready to observe

---

**Status**: Ready for controlled deployment  
**Next**: Deploy and collect real queries

