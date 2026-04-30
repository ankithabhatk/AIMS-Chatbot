# System Governance - The Control Layer

**This is your constitution. Follow it religiously.**

---

## The Core Principle

**DON'T ADD RULES WITHOUT LOG EVIDENCE**

This is not a guideline. This is your governance model.

---

## Why This Matters

### Without Governance
```
Week 1: Add 5 rules
Week 2: Add 8 rules
Week 3: Add 12 rules
Week 4: Add 15 rules

Result: 40 rules, unpredictable behavior, fragile system
```

### With Governance
```
Week 1: 0 rules (observe)
Week 2: 5 rules (with evidence)
Week 3: 5 rules (with evidence)
Week 4: 5 rules (with evidence)

Result: 15 rules, predictable behavior, maintainable system
```

---

## The Rule Addition Criteria

### When to Add a Rule

A rule is added ONLY if:

```
(Frequency >= 3 AND Causes Failure) OR (Frequency >= 5)
```

This means:

- **High-frequency patterns** (5+ occurrences) → Always add
- **Critical patterns** (3+ occurrences AND causes failure) → Add
- **Rare patterns** (< 3 occurrences) → Ignore

---

## The Three Buckets (Governance)

### 🟢 Bucket 1: Keyword Gaps
**Problem**: User says "cost", system doesn't detect as "fees"  
**Cause**: Keyword missing from intent definition  
**Fix**: Add keyword to intent  
**Governance**: Add if appears 3+ times  
**Example**:
```
"cost" appears 12 times → Add to FEES_KEYWORDS
"price" appears 8 times → Add to FEES_KEYWORDS
"tuition" appears 2 times → Don't add (too rare)
```

---

### 🟡 Bucket 2: Phrase Patterns
**Problem**: User says "how much does it cost", system doesn't detect intent  
**Cause**: Phrase structure not recognized  
**Fix**: Add phrase pattern detector  
**Governance**: Add if appears 5+ times  
**Example**:
```
"how much" appears 7 times → Add phrase pattern
"what is the" appears 4 times → Don't add (too rare)
```

---

### 🔴 Bucket 3: Intent Transformation
**Problem**: User says "I like coding what should I choose", system routes wrong  
**Cause**: Intent routing doesn't match user intent  
**Fix**: Add query type handler or routing rule  
**Governance**: Add if appears 3+ times AND causes failure  
**Example**:
```
"I like X what should I choose" appears 3 times, causes wrong routing → Add exploratory handler
"which course is best" appears 2 times, works with current routing → Don't add
```

---

## User Struggle Tracking (Critical Addition)

### What is "Struggle"?

Not just individual queries. But patterns of repeated attempts:

```
User sends:
1. "fees"
2. "bca fees"
3. "what is fee"

This is NOT 3 queries.
This is 1 FAILED interaction.
```

### Signs of Struggle

- User repeats question with different wording
- User sends multiple short queries in sequence
- User rephrases after fallback
- User asks same thing 2+ times

### How to Track

In logs, add:

```json
{
    "query": "fees",
    "struggle_sequence": 1,
    "struggle_topic": "fees",
    "fallback": true
}

{
    "query": "bca fees",
    "struggle_sequence": 2,
    "struggle_topic": "fees",
    "fallback": true
}

{
    "query": "what is fee",
    "struggle_sequence": 3,
    "struggle_topic": "fees",
    "fallback": true
}
```

### Why This Matters

Struggle patterns show:
- What users really want
- Where system is confusing
- What to prioritize fixing

---

## Rule Lifecycle

### Phase 1: Observation (Week 1)
```
Status: No rules added
Action: Deploy, collect queries
Governance: Strict observation only
```

### Phase 2: Evidence Gathering (Week 2)
```
Status: Analyzing logs
Action: Categorize into 3 buckets
Governance: Only document, don't add yet
Output: List of candidate rules with evidence
```

### Phase 3: Controlled Addition (Week 3)
```
Status: Adding rules
Action: Add only rules with evidence
Governance: Max 5-10 rules per week
Criteria: Meets frequency + failure threshold
```

### Phase 4: Stabilization (Week 4)
```
Status: Rules locked
Action: No new rules
Governance: Only bug fixes
Output: Documented, stable system
```

---

## The Rule Addition Checklist

Before adding ANY rule, verify:

- [ ] **Evidence**: Appears in logs (3+ or 5+ depending on bucket)
- [ ] **Impact**: Improves detection or reduces fallback
- [ ] **Scope**: Doesn't break existing behavior
- [ ] **Documentation**: Why this rule exists (log reference)
- [ ] **Limit**: Total rules < 20

---

## What Counts as "Evidence"

### ✅ Valid Evidence
```
"cost" appears 12 times in Week 2 logs
→ Add to FEES_KEYWORDS

"how much" appears 7 times in Week 2 logs
→ Add phrase pattern

"I like X" appears 3 times, causes wrong routing
→ Add exploratory handler
```

### ❌ Invalid Evidence
```
"I think users might say 'tuition'"
→ Don't add (no log evidence)

"This would improve coverage"
→ Don't add (no log evidence)

"Similar systems do this"
→ Don't add (no log evidence)
```

---

## The Governance Hierarchy

### Level 1: Observation (Strict)
- No rules added
- Only data collection
- No assumptions

### Level 2: Analysis (Careful)
- Categorize findings
- Identify patterns
- Plan changes (don't implement)

### Level 3: Implementation (Disciplined)
- Add only evidence-based rules
- Max 5-10 rules per week
- Document everything

### Level 4: Stabilization (Locked)
- No new rules
- Only bug fixes
- System frozen for production

---

## Query Type Governance

### Direct Queries
```
"BCA fees"
"admission process"

Governance: Route to specific intent
No special handling needed
```

### Exploratory Queries
```
"I like coding what should I choose"
"which course is best for me"

Governance: Route to guidance + courses
Add handler if appears 3+ times
```

### Multi-Intent Queries
```
"fees and hostel for BCA"
"admission and placement info"

Governance: Split and combine responses
Improve handling if appears 3+ times
```

---

## Soft Fallback Governance

### Current Soft Fallback
```
"I can help with:
• Course Information
• Fees & Costs
• Admission Process
• Campus & Facilities

What would you like to know?"
```

### Governance
- Don't change fallback message without user feedback
- Track if users respond to soft fallback
- Only improve if logs show confusion

---

## Documentation Requirements

Every rule must have:

```python
NORMALIZATION = {
    # "cost" → "fees"
    # Evidence: Week 2 logs, 12 occurrences
    # Added: Week 3, Day 15
    # Impact: Improves fees detection from 33% to 75%
    "cost": "fees",
}
```

---

## The Metrics That Matter

### Track These
- Fallback rate (target: 64% → 30-35%)
- User struggle patterns (repeated attempts)
- Rule effectiveness (does each rule help?)
- System stability (no crashes)

### Don't Track These
- Confidence scores
- Keyword match rates
- Intent detection accuracy
- System performance metrics

---

## The Governance Review Cycle

### Weekly Review (Every Friday)
```
1. How many rules added this week?
2. Do they all have evidence?
3. Are they improving fallback rate?
4. Any unintended side effects?
5. What patterns emerged?
```

### Monthly Review (Every 4 weeks)
```
1. Total rules added (should be < 20)
2. System stability (any crashes?)
3. User satisfaction (from feedback)
4. Ready for next phase?
```

---

## What Breaks Governance

### Red Flags 🚨
- Adding rules without log evidence
- Adding 20+ rules in one week
- Changing thresholds randomly
- Adding new intents
- Modifying core routing logic

### Yellow Flags ⚠️
- Adding rules with only 2-3 occurrences
- Not documenting why rules exist
- Forgetting to test rule impact
- Ignoring user struggle patterns

---

## The Constitution

### Article 1: Evidence-Based
All rules must have log evidence.

### Article 2: Limited Growth
Maximum 20 rules total.

### Article 3: Documented
Every rule must explain why it exists.

### Article 4: Tested
Every rule must improve a metric.

### Article 5: Locked
Once Phase 4 begins, no new rules.

---

## Final Governance Statement

**This system is not built to be smart.**

**This system is built to be controlled.**

Control is achieved through:
1. Strict governance
2. Evidence-based decisions
3. Limited rule growth
4. Continuous monitoring
5. Documented changes

---

## Your Responsibility

You are now the **Governance Officer** of this system.

Your job is NOT to make it smarter.

Your job is to:
1. Prevent rule explosion
2. Ensure evidence-based changes
3. Monitor for drift
4. Keep system stable
5. Document everything

---

## The Oath

**I will not add rules without log evidence.**

**I will not exceed 20 total rules.**

**I will document every change.**

**I will prioritize stability over features.**

**I will let data guide decisions, not assumptions.**

---

## Status

✅ Governance model defined  
✅ Criteria established  
✅ Hierarchy clear  
✅ Ready to deploy with discipline  

**Next**: Deploy. Observe. Analyze with governance. Add only evidence-based rules.

You are now a controlled system. 🎯
