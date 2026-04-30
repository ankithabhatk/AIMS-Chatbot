# Log to Rule Conversion Workflow

**How to convert raw logs into governed rules.**

---

## The Workflow (4 Steps)

### Step 1: Extract Raw Patterns (Day 1-2)
Extract all patterns from logs without filtering.

### Step 2: Categorize (Day 2-3)
Sort into 3 buckets (keyword gaps, phrase patterns, intent transformation).

### Step 3: Apply Governance (Day 3-4)
Filter by frequency and impact criteria.

### Step 4: Document & Implement (Day 4-5)
Add only approved rules with documentation.

---

## Step 1: Extract Raw Patterns

### From 50 Queries, Extract:

#### Keyword Gaps
```
Query: "how much does it cost"
Missing: "cost" not in FEES_KEYWORDS
Frequency: 12 occurrences
Impact: Fallback (should be fees)
```

#### Phrase Patterns
```
Query: "how much does it cost"
Pattern: "how much" + intent
Frequency: 7 occurrences
Impact: Fallback (should detect fees)
```

#### Intent Transformation
```
Query: "I like coding what should I choose"
Pattern: "I like X" + "what should I choose"
Frequency: 3 occurrences
Impact: Wrong routing (should be guidance + courses)
```

---

## Step 2: Categorize

### Template

```
BUCKET 1 (Keyword Gaps):
- "cost" (12x) → FEES_KEYWORDS
- "apply" (15x) → ADMISSION_KEYWORDS
- "program" (8x) → COURSES_KEYWORDS

BUCKET 2 (Phrase Patterns):
- "how much" (7x) → fees hint
- "how to" (8x) → admission hint
- "what is X like" (4x) → info hint

BUCKET 3 (Intent Transformation):
- "I like X what should I choose" (3x) → exploratory routing
- "fees and hostel" (4x) → multi-intent handling
```

---

## Step 3: Apply Governance

### Governance Criteria

```
Add rule if:
(Frequency >= 3 AND Causes Failure) OR (Frequency >= 5)
```

### Apply to Each Pattern

#### Keyword Gaps
```
"cost" (12x) → Meets criteria (12 >= 5) → ADD ✓
"apply" (15x) → Meets criteria (15 >= 5) → ADD ✓
"program" (8x) → Meets criteria (8 >= 5) → ADD ✓
"tuition" (2x) → Doesn't meet criteria → SKIP ✗
```

#### Phrase Patterns
```
"how much" (7x) → Meets criteria (7 >= 5) → ADD ✓
"how to" (8x) → Meets criteria (8 >= 5) → ADD ✓
"what is X like" (4x) → Doesn't meet criteria → SKIP ✗
```

#### Intent Transformation
```
"I like X what should I choose" (3x, causes failure) → Meets criteria → ADD ✓
"fees and hostel" (4x, causes failure) → Meets criteria → ADD ✓
```

### Result
```
Total rules to add: 7
- Keyword gaps: 3
- Phrase patterns: 2
- Intent transformation: 2

Within governance limit (< 20) ✓
```

---

## Step 4: Document & Implement

### Documentation Template

```python
# KEYWORD GAP: "cost" → "fees"
# Evidence: Week 2 logs, 12 occurrences
# Bucket: 1 (Keyword Gap)
# Frequency: 12 >= 5 ✓
# Impact: Improves fees detection from 33% to 75%
# Added: Week 3, Day 15
# Status: Active
FEES_KEYWORDS.add("cost")

# PHRASE PATTERN: "how much" → fees hint
# Evidence: Week 2 logs, 7 occurrences
# Bucket: 2 (Phrase Pattern)
# Frequency: 7 >= 5 ✓
# Impact: Helps detect fees intent in complex queries
# Added: Week 3, Day 15
# Status: Active
PHRASE_PATTERNS[r"how much"] = "fees"

# INTENT TRANSFORMATION: Exploratory routing
# Evidence: Week 2 logs, 3 occurrences, causes wrong routing
# Bucket: 3 (Intent Transformation)
# Frequency: 3 >= 3 AND Causes Failure ✓
# Impact: Routes "I like X what should I choose" to guidance + courses
# Added: Week 3, Day 15
# Status: Active
def handle_exploratory_query(query):
    return route_to(["guidance", "courses"])
```

---

## Real Example: Complete Workflow

### Week 2: Raw Logs (50 queries)

```
Query 1: "how much does it cost"
Query 2: "what's the price"
Query 3: "how to apply"
Query 4: "how to join"
Query 5: "I like coding what should I choose"
...
```

### Step 1: Extract Patterns

```
KEYWORD GAPS:
- "cost" appears in queries 1, 7, 12, 18, 22, 25, 31, 35, 38, 41, 44, 48 (12x)
- "apply" appears in queries 3, 9, 14, 19, 26, 33, 39, 42, 45, 49, 50, 52, 55, 58, 61 (15x)
- "program" appears in queries 6, 11, 16, 21, 27, 34, 40, 46 (8x)

PHRASE PATTERNS:
- "how much" appears in queries 1, 7, 12, 18, 22, 25, 31 (7x)
- "how to" appears in queries 3, 9, 14, 19, 26, 33, 39, 42 (8x)

INTENT TRANSFORMATION:
- "I like X what should I choose" in queries 5, 13, 28 (3x, causes wrong routing)
- "fees and hostel" in queries 8, 15, 24, 36 (4x, causes multi-intent failure)
```

### Step 2: Categorize

```
BUCKET 1 (Keyword Gaps):
- "cost" (12x) → FEES_KEYWORDS
- "apply" (15x) → ADMISSION_KEYWORDS
- "program" (8x) → COURSES_KEYWORDS

BUCKET 2 (Phrase Patterns):
- "how much" (7x) → fees hint
- "how to" (8x) → admission hint

BUCKET 3 (Intent Transformation):
- "I like X what should I choose" (3x) → exploratory routing
- "fees and hostel" (4x) → multi-intent handling
```

### Step 3: Apply Governance

```
APPROVED FOR ADDITION:
✓ "cost" (12 >= 5)
✓ "apply" (15 >= 5)
✓ "program" (8 >= 5)
✓ "how much" (7 >= 5)
✓ "how to" (8 >= 5)
✓ "I like X" (3 >= 3 AND causes failure)
✓ "fees and hostel" (4 >= 3 AND causes failure)

Total: 7 rules (within limit)
```

### Step 4: Implement

```python
# Week 3 Implementation

# BUCKET 1: Keywords
FEES_KEYWORDS.add("cost")  # 12x evidence
ADMISSION_KEYWORDS.add("apply")  # 15x evidence
COURSES_KEYWORDS.add("program")  # 8x evidence

# BUCKET 2: Phrases
PHRASE_PATTERNS[r"how much"] = "fees"  # 7x evidence
PHRASE_PATTERNS[r"how to"] = "admission"  # 8x evidence

# BUCKET 3: Routing
def handle_exploratory(query):  # 3x evidence
    return route_to(["guidance", "courses"])

def handle_multi_intent(query):  # 4x evidence
    return split_and_combine()
```

---

## Weekly Workflow Template

### Every Friday (Week 2, 3, 4)

```
1. Extract patterns from logs (2 hours)
   - Keyword gaps
   - Phrase patterns
   - Intent transformation

2. Categorize into buckets (1 hour)
   - Bucket 1: Keyword gaps
   - Bucket 2: Phrase patterns
   - Bucket 3: Intent transformation

3. Apply governance criteria (1 hour)
   - Frequency check
   - Impact check
   - Limit check

4. Document approved rules (1 hour)
   - Why each rule exists
   - Log evidence
   - Expected impact

5. Implement (if approved) (2 hours)
   - Add to code
   - Test
   - Deploy

Total: ~7 hours per week
```

---

## Governance Checklist

Before implementing any rule:

- [ ] Appears in logs (3+ or 5+ depending on bucket)
- [ ] Categorized correctly (bucket 1, 2, or 3)
- [ ] Meets governance criteria
- [ ] Documented with evidence
- [ ] Total rules < 20
- [ ] No side effects on existing behavior
- [ ] Tested before deployment

---

## What to Do If Governance Fails

### If You Find Yourself Adding Rules Without Evidence

**STOP.**

Ask:
1. Is this in the logs?
2. How many times?
3. Does it meet the criteria?
4. Can I document it?

If answer to any is "no", don't add it.

---

## Success Metrics

### Week 2
- [ ] 50 queries collected
- [ ] Patterns extracted
- [ ] Categorized into 3 buckets
- [ ] Governance criteria applied
- [ ] 5-10 rules identified

### Week 3
- [ ] 7 rules implemented
- [ ] All documented
- [ ] System re-deployed
- [ ] No crashes
- [ ] Fallback rate improving

### Week 4
- [ ] Fallback rate < 35%
- [ ] All rules documented
- [ ] System stable
- [ ] Ready for production

---

## Final Principle

**Every rule must earn its place through evidence.**

Not through assumption.
Not through intuition.
Not through "best practices."

Through evidence.

---

## Status

✅ Workflow defined  
✅ Governance criteria clear  
✅ Documentation template ready  
✅ Ready to execute  

**Next**: Deploy. Collect logs. Follow this workflow religiously.
