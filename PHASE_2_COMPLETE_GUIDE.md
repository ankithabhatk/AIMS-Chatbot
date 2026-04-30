# Phase 2 Complete Guide - Language Coverage

**This is your complete roadmap for Phase 2.**

---

## What Phase 2 Is

**NOT**: Debugging or fixing code  
**IS**: Building a language normalization layer based on real user data

---

## The 3-Layer System

### Layer 1: Normalization (NEW)
```
User: "how much does it cost"
Normalize: "how much does it fees"
```

### Layer 2: Intent Detection (You have this)
```
"fees" → fees intent
```

### Layer 3: Response Generation (You have this)
```
fees intent → fees information
```

**Right now you're missing Layer 1. That's your 64% fallback.**

---

## Phase 2 Timeline

### Week 1: Deploy & Observe (Days 1-7)
```
✓ Deploy to 10-20 beta users
✓ Collect ~25 queries
✓ Monitor for crashes
✓ Verify logging is working
```

### Week 2: Analyze & Build (Days 8-14)
```
✓ Collect ~25 more queries (50 total)
✓ Extract synonym clusters
✓ Extract phrase patterns
✓ Build normalization map
✓ Plan soft fallback improvements
```

### Week 3: Implement & Verify (Days 15-21)
```
✓ Add normalization layer
✓ Add soft fallback messages
✓ Re-deploy
✓ Collect ~20 more queries
✓ Verify improvements
```

### Week 4: Stabilize (Days 22-28)
```
✓ Lock normalization rules
✓ Document patterns
✓ Prepare for production
```

---

## What You'll Extract from Logs

### Synonym Clusters
```
From 50 queries, you'll see:

FEES cluster:
- "cost" appears 7 times
- "price" appears 3 times
- "charges" appears 2 times
- "expensive" appears 2 times

→ These all mean the same thing
→ Build normalization rule: "cost" → "fees"
```

### Phrase Patterns
```
From 50 queries, you'll see:

Pattern: "how to ___"
- "how to apply" (5 times)
- "how to join" (3 times)
- "how to enroll" (2 times)

→ All indicate admission intent
→ Build phrase rule: r"how to\s+(apply|join|enroll)" → admission
```

### Mixed Intent Patterns
```
From 50 queries, you'll see:

"I like coding what should I choose"
→ This is guidance + courses (not just keywords)

"fees for bca and mba"
→ This is fees + courses (multiple intents)

→ These need special handling in routing
```

---

## Building the Normalization Map

### Step 1: Extract from Logs
```
Week 2 analysis shows:
- "cost" missed 7 times (should be "fees")
- "price" missed 3 times (should be "fees")
- "apply" missed 5 times (should be "admission")
```

### Step 2: Add to normalization.py
```python
SYNONYM_NORMALIZATION = {
    "cost": "fees",
    "price": "fees",
    "charges": "fees",
    "apply": "admission",
    "join": "admission",
    # ... more
}
```

### Step 3: Apply in Engine
```python
# In engine.py, before intent detection:
working_query = normalize_query(working_query)
intent = detect_intent(working_query)
```

### Step 4: Verify Improvement
```
Before: "how much does it cost" → fallback
After: "how much does it cost" → normalize → "fees" → success
```

---

## Soft Fallback Implementation

### Current Fallback (Blocks User)
```
"I didn't quite understand that. Could you please rephrase?"
```

**Problem**: User feels stuck. Conversation ends.

---

### Soft Fallback (Guides User)
```
"I'm not sure I understood that correctly.

I can help you with:
• Course Information
• Fees & Costs
• Admission Process
• Campus & Facilities

What would you like to know?"
```

**Benefit**: User knows what to ask. Conversation continues.

---

## Files Ready for Phase 2

### 1. normalization.py (Ready)
```python
SYNONYM_NORMALIZATION = {
    # Populated during Phase 2
}

def normalize_query(query: str) -> str:
    # Apply normalization rules
    pass
```

**What to do**: Populate with real data from logs

---

### 2. soft_fallback.py (Ready)
```python
def get_soft_fallback_message() -> str:
    # Return helpful guidance instead of blocking
    pass
```

**What to do**: Use in engine.py when fallback occurs

---

### 3. BETA_LOG_ANALYSIS_SHEET.md (Ready)
```
Template for extracting patterns from logs
Use weekly to identify what to normalize
```

**What to do**: Follow this template religiously

---

## Integration Checklist

- [ ] Deploy with current system (Week 1)
- [ ] Collect 50 queries (Week 2)
- [ ] Extract synonym clusters (Week 2)
- [ ] Extract phrase patterns (Week 2)
- [ ] Populate normalization.py (Week 3)
- [ ] Add soft fallback to engine.py (Week 3)
- [ ] Re-deploy (Week 3)
- [ ] Verify improvements (Week 3)
- [ ] Lock rules (Week 4)

---

## Expected Improvements

### Week 1 Baseline
```
Fallback rate: 64%
User satisfaction: Medium
```

### Week 3 After Normalization
```
Fallback rate: 35-40%
User satisfaction: High
```

### Week 4 After Optimization
```
Fallback rate: 25-30%
User satisfaction: Very High
```

---

## What NOT to Do

❌ **Don't**:
- Add 50 new keywords
- Create complex rules
- Optimize for edge cases
- Add new intents
- Change thresholds

✅ **Do**:
- Extract real patterns
- Build normalization map
- Add soft fallback
- Keep logic simple
- Focus on common cases

---

## Real Example: Complete Cycle

### Week 1: Deploy
```
System deployed to 10 users
Collecting queries...
```

### Week 2: Analyze
```
50 queries collected

Analysis shows:
- "cost" appears 7 times (not detected as fees)
- "apply" appears 5 times (not detected as admission)
- "how to ___" pattern appears 10 times

Normalization map:
{
    "cost": "fees",
    "apply": "admission",
}

Phrase pattern:
r"how to\s+(\w+)" → admission
```

### Week 3: Implement
```
Add to normalization.py:
SYNONYM_NORMALIZATION = {
    "cost": "fees",
    "apply": "admission",
}

Add to engine.py:
working_query = normalize_query(working_query)

Add soft fallback:
Use soft_fallback.get_soft_fallback_message()

Re-deploy
```

### Week 3: Verify
```
Next 20 queries:
- "cost" now detected: 6/7 ✓
- "apply" now detected: 5/5 ✓
- "how to" pattern: 8/10 ✓

Fallback rate: 35% (down from 64%)
```

### Week 4: Stabilize
```
Lock normalization rules
Document patterns
Prepare for production
```

---

## Key Principles

### 1. Data-Driven
```
Don't guess what users want.
Let logs show you.
```

### 2. Simple Rules
```
Don't create complex logic.
Simple normalization rules scale.
```

### 3. Maintainable
```
Don't add 50 keywords.
Add 5 normalization rules instead.
```

### 4. Iterative
```
Don't try to fix everything at once.
Fix one pattern per week.
```

---

## Success Metrics

### Week 1
- [ ] System deployed
- [ ] No crashes
- [ ] Logging working
- [ ] 25 queries collected

### Week 2
- [ ] 50 queries collected
- [ ] Synonym clusters identified
- [ ] Phrase patterns identified
- [ ] Normalization map drafted

### Week 3
- [ ] Normalization layer added
- [ ] Soft fallback implemented
- [ ] System re-deployed
- [ ] Improvements verified

### Week 4
- [ ] Fallback rate < 35%
- [ ] User satisfaction high
- [ ] Rules documented
- [ ] Ready for production

---

## What to Bring Back After Week 2

```
Synonym clusters found:
- FEES: "cost" (7), "price" (3), "charges" (2)
- ADMISSION: "apply" (5), "join" (3)
- COURSES: "program" (4), "degree" (3)

Phrase patterns found:
- "how to ___" (10 queries)
- "what is ___ like" (4 queries)
- "I like ___" (3 queries)

Normalization map to build:
{
    "cost": "fees",
    "price": "fees",
    "apply": "admission",
    "join": "admission",
    "program": "courses",
}
```

---

## Final Status

✅ You understand the gap (language coverage)  
✅ You understand the solution (normalization)  
✅ You have the tools ready (normalization.py, soft_fallback.py)  
✅ You have the process (BETA_LOG_ANALYSIS_SHEET.md)  
✅ You're ready to deploy  

**Next**: Deploy, observe, collect 50 queries, build normalization map.

---

## One Final Thing

**This is not complicated.**

You're not building AI. You're not optimizing algorithms.

You're just:
1. Seeing how users speak
2. Converting their language to your language
3. Keeping it simple and maintainable

**That's it. That's Phase 2.**

Deploy and observe. 🚀
