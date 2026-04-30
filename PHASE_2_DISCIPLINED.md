# Phase 2: Disciplined Approach

**The key rule: DON'T ADD RULES WITHOUT LOG EVIDENCE**

---

## The Risk You're Avoiding

### Bad Approach (Over-Engineering)
```python
NORMALIZATION = {
    "cost": "fees",
    "price": "fees",
    "charges": "fees",
    "amount": "fees",
    "fee structure": "fees",
    "total fee": "fees",
    "tuition": "fees",
    "expense": "fees",
    "expensive": "fees",
    "afford": "fees",
    # ... 50 more rules
}
```

**Result**: Unmaintainable. Fragile. Hard to debug.

---

### Good Approach (Data-Driven)
```python
NORMALIZATION = {
    # Only rules with 10+ occurrences in logs
    "cost": "fees",        # seen 12 times
    "price": "fees",       # seen 8 times (borderline)
    "apply": "admission",  # seen 15 times
    "join": "admission",   # seen 10 times
}
```

**Result**: Maintainable. Scalable. Evidence-based.

---

## The Three Buckets

### 🟢 Bucket 1: Direct Keyword Gaps
```
From logs:
- "cost" appears 12 times, never detected as fees
- "apply" appears 15 times, never detected as admission

Action: Add keyword to intent detection
- Add "cost" to FEES_KEYWORDS
- Add "apply" to ADMISSION_KEYWORDS

NOT normalization. Just keywords.
```

---

### 🟡 Bucket 2: Phrase Patterns
```
From logs:
- "how much does it cost" (7 times)
- "what is the fee" (5 times)
- "how to apply" (8 times)

Pattern: "how [to/much/is]" indicates intent

Action: Add phrase-level detection
- if "how much" in query → hint: fees
- if "how to" in query → hint: admission

This is smarter than word-by-word normalization.
```

---

### 🔴 Bucket 3: Intent Transformation
```
From logs:
- "I like coding what should I choose" (3 times)
- "which course is best for me" (4 times)
- "I'm interested in AI" (2 times)

Problem: NOT a keyword problem
These are exploratory queries that need guidance + courses

Action: Add query_type detection
- if query_type == "exploratory" → route to guidance + courses
- NOT just keyword matching

This is a routing problem, not a normalization problem.
```

---

## Query Types (NEW - Critical Addition)

### Type 1: Direct
```
"BCA fees"
"admission process"
"hostel facilities"

→ User knows what they want
→ Route to specific intent
```

### Type 2: Exploratory
```
"I like coding what should I choose"
"which course is best for me"
"I'm interested in AI"

→ User exploring options
→ Route to guidance + courses
```

### Type 3: Multi-Intent
```
"fees and hostel for BCA"
"admission process and campus facilities"

→ User asking about multiple things
→ Route to multiple intents
```

---

## Detecting Query Type

```python
def detect_query_type(query: str) -> str:
    """Detect if query is direct, exploratory, or multi-intent"""
    
    # Multi-intent: contains "and" or multiple topics
    if " and " in query.lower():
        return "multi_intent"
    
    # Exploratory: contains guidance keywords
    if any(word in query.lower() for word in 
           ["like", "interested", "best", "good", "should", "choose"]):
        return "exploratory"
    
    # Default: direct
    return "direct"
```

---

## Phase 2 Workflow (Disciplined)

### Week 1: Collect (No Changes)
```
Deploy to 10-20 users
Collect 50 queries
Monitor for crashes
Verify logging
```

### Week 2: Analyze (Categorize)
```
Split 50 queries into 3 buckets:

🟢 Bucket 1: Keyword gaps
- "cost" (12 times) → add to FEES_KEYWORDS
- "apply" (15 times) → add to ADMISSION_KEYWORDS

🟡 Bucket 2: Phrase patterns
- "how much" (7 times) → add phrase detector
- "how to" (8 times) → add phrase detector

🔴 Bucket 3: Intent transformation
- "I like coding" (3 times) → add exploratory routing
- "fees and hostel" (4 times) → add multi-intent handling

Total changes: ~10-15 rules
```

### Week 3: Implement (Targeted)
```
Change 1: Add 5-10 keywords
- "cost" → FEES_KEYWORDS
- "apply" → ADMISSION_KEYWORDS
- etc.

Change 2: Add 5-10 phrase patterns
- "how much" → fees hint
- "how to" → admission hint
- etc.

Change 3: Add 1-2 query type handlers
- exploratory → guidance + courses
- multi_intent → multiple responses

Stop. Don't add more.
```

### Week 4: Verify & Stabilize
```
Collect 20 more queries
Verify improvements
Lock rules
Document patterns
```

---

## The Discipline Rules

### Rule 1: Evidence-Based Only
```
❌ "I think users might say 'tuition'"
✅ "Logs show 'tuition' appears 8 times"

Only add rules if seen 5+ times.
```

---

### Rule 2: Keep Normalization Small
```
Target: 10-20 rules max
Not 100+

If you have 50+ rules, you're over-engineering.
```

---

### Rule 3: Prefer Patterns Over Words
```
❌ "cost" → "fees"
   "price" → "fees"
   "charges" → "fees"
   "amount" → "fees"
   (4 separate rules)

✅ if "how much" in query:
       intent_hint = "fees"
   (1 pattern rule)
```

---

### Rule 4: Document Everything
```
For each rule, document:
- What it does
- Why it exists (log evidence)
- When it was added
- How often it's used

Example:
```
NORMALIZATION = {
    # "cost" → "fees" (seen 12 times in Week 2 logs)
    "cost": "fees",
}
```
```

---

## What NOT to Do

❌ **Don't**:
- Add 50 normalization rules
- Guess what users might say
- Optimize for edge cases
- Add rules without log evidence
- Create complex phrase patterns

✅ **Do**:
- Add 10-20 rules max
- Use log evidence only
- Focus on common cases (5+ occurrences)
- Keep rules simple
- Document every rule

---

## Real Example: Disciplined Cycle

### Week 1: Deploy
```
System deployed
50 queries collected
```

### Week 2: Analyze
```
Bucket 1 (Keywords):
- "cost" appears 12 times → add to FEES_KEYWORDS
- "apply" appears 15 times → add to ADMISSION_KEYWORDS
- "program" appears 8 times → add to COURSES_KEYWORDS

Bucket 2 (Phrases):
- "how much" appears 7 times → add phrase detector
- "how to" appears 8 times → add phrase detector

Bucket 3 (Intent Transformation):
- "I like coding" appears 3 times → add exploratory routing

Total: 7 changes
```

### Week 3: Implement
```
Change 1: Add keywords
FEES_KEYWORDS.add("cost")
ADMISSION_KEYWORDS.add("apply")
COURSES_KEYWORDS.add("program")

Change 2: Add phrase detectors
if "how much" in query:
    intent_hint = "fees"

Change 3: Add query type handler
if detect_query_type(query) == "exploratory":
    route_to_guidance_and_courses()

Deploy
```

### Week 3: Verify
```
Next 20 queries:
- "cost" now detected: 11/12 ✓
- "apply" now detected: 14/15 ✓
- "how much" pattern: 6/7 ✓
- Exploratory queries: 3/3 ✓

Fallback rate: 45% (down from 64%)
```

### Week 4: Stabilize
```
Lock all rules
Document patterns
Prepare for production
```

---

## Expected Results

### Week 1 Baseline
```
Fallback rate: 64%
Query types: Unknown
```

### Week 3 After Disciplined Changes
```
Fallback rate: 40-45%
Query types: Detected
Multi-intent: Handled
```

### Week 4 After Stabilization
```
Fallback rate: 30-35%
System: Maintainable
Rules: Documented
```

---

## The One Rule to Rule Them All

**DON'T ADD RULES WITHOUT LOG EVIDENCE**

This single rule will:
- Prevent over-engineering
- Keep system maintainable
- Ensure improvements are real
- Avoid fragility

---

## Files to Update

### 1. normalization.py
```python
# Keep it SMALL
NORMALIZATION = {
    # Only high-frequency patterns with evidence
    "cost": "fees",        # Week 2 logs: 12 occurrences
    "apply": "admission",  # Week 2 logs: 15 occurrences
}
```

### 2. query_type.py (NEW)
```python
def detect_query_type(query: str) -> str:
    """Detect if query is direct, exploratory, or multi-intent"""
    # Simple detection based on keywords
    pass
```

### 3. phrase_patterns.py (NEW)
```python
PHRASE_PATTERNS = {
    # Only patterns with evidence
    "how much": "fees",      # Week 2 logs: 7 occurrences
    "how to": "admission",   # Week 2 logs: 8 occurrences
}
```

---

## Checklist for Phase 2

- [ ] Week 1: Deploy, collect 50 queries
- [ ] Week 2: Analyze into 3 buckets
- [ ] Week 2: Identify 5-10 high-frequency patterns
- [ ] Week 3: Add only evidence-based rules
- [ ] Week 3: Add query type detection
- [ ] Week 3: Re-deploy and verify
- [ ] Week 4: Lock rules and document
- [ ] Week 4: Prepare for production

---

## Final Discipline

**Your system is good.**

Don't make it worse by over-engineering.

Follow the one rule:
**DON'T ADD RULES WITHOUT LOG EVIDENCE**

Everything else follows from that.

---

## Status

✅ Architecture is solid  
✅ Thinking is disciplined  
✅ Ready to deploy  
✅ Ready to learn from real data  

**Next**: Deploy. Collect 50 queries. Analyze with discipline. Add only evidence-based rules.

You're ready. 👍
