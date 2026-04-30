# Beta Log Analysis Sheet

**Purpose**: Extract patterns from real user queries  
**When**: After every 10-15 queries  
**Time**: 5 minutes per analysis  
**Output**: Actionable improvements

---

## What You're Looking For (NOT Bugs)

❌ **Don't look for**:
- System crashes
- Wrong answers
- Code errors

✅ **DO look for**:
- Language variations (how users phrase things)
- Missed intents (what we didn't detect)
- Confusion loops (user rephrases multiple times)
- Patterns (same intent phrased 5 different ways)

---

## Template: After Every 10 Queries

### Step 1: Extract Fallbacks (2 min)

```
Fallback queries from last 10:
1. "how much does it cost" → fallback (reason: low_confidence)
2. "what's the price" → fallback (reason: no_intent)
3. "can i get scholarship" → fallback (reason: routing_gap)
```

### Step 2: Cluster by Intent (2 min)

```
What the user probably meant:

FEES (3 queries):
- "how much does it cost"
- "what's the price"
- "fees??"

ADMISSION (2 queries):
- "can i get scholarship"
- "how to apply"

COURSES (1 query):
- "what can i do with bca"
```

### Step 3: Note Language Variations (1 min)

```
New language patterns discovered:

FEES variations:
- "cost" (not "fees")
- "price" (not "fees")
- "charges" (not "fees")

ADMISSION variations:
- "how to apply" (not "admission")
- "can i get in" (not "eligibility")
```

---

## Template: After 50 Queries

### Analysis 1: Top Missed Intents

```
Intent: FEES
- Total queries: 15
- Detected: 5
- Missed: 10
- Detection rate: 33%

Language variations found:
- "cost" (7 queries)
- "price" (3 queries)
- "charges" (2 queries)
- "fees" (3 queries)

Action: Add keywords ["cost", "price", "charges"] to fees intent
```

### Analysis 2: Confusion Loops

```
Pattern: User asks → rephrases → rephrases again

Example:
1. "what are fees" → fallback
2. "how much does it cost" → fallback
3. "is it expensive" → fallback

Root cause: Keywords don't match "cost" or "expensive"
Action: Add these keywords to fees intent
```

### Analysis 3: New Intents Discovered

```
Queries that don't fit existing intents:

1. "is bca worth it" (5 queries)
   → Not courses, not fees, not admission
   → Probably "career_value" or "program_comparison"

2. "what's the placement rate" (3 queries)
   → Not placements (which is salary/jobs)
   → Probably "placement_stats"

Action: Consider adding 1-2 new intents based on frequency
```

---

## Real Example: What to Extract

### Raw Logs (First 10 Queries)

```
1. "what are the fees for mba" → detected: fees ✓
2. "how much does it cost" → fallback ✗
3. "tell me about bca" → detected: courses ✓
4. "can i get scholarship" → fallback ✗
5. "hi" → detected: greeting ✓
6. "what's the price" → fallback ✗
7. "admission process" → detected: admission ✓
8. "how to apply" → fallback ✗
9. "python course" → fallback ✗
10. "bye" → detected: exit ✓
```

### Analysis (What You Extract)

```
FEES Intent (3 queries, 33% detection):
- "what are the fees for mba" ✓ (keyword: "fees")
- "how much does it cost" ✗ (keyword: "cost" - NOT in system)
- "what's the price" ✗ (keyword: "price" - NOT in system)

ACTION: Add ["cost", "price"] to fees keywords

ADMISSION Intent (2 queries, 50% detection):
- "admission process" ✓ (keyword: "admission")
- "how to apply" ✗ (keyword: "apply" - exists but not matching)

ACTION: Debug why "apply" isn't matching

COURSES Intent (1 query, 0% detection):
- "python course" ✗ (keyword: "course" exists, but "python" confuses it)

ACTION: Check if "python" is being caught as nonsense
```

---

## Weekly Review Checklist

After 50 queries (roughly 1 week):

- [ ] Extract all fallback queries
- [ ] Cluster by likely intent
- [ ] Note language variations
- [ ] Identify top 3 missed intents
- [ ] Identify top 3 language variations
- [ ] List confusion loops (if any)
- [ ] Identify new intents (if any)

---

## Data You Need from Logs

Each query must have:

```json
{
  "query": "how much does it cost",
  "detected_intents": [],
  "final_intent": "unknown",
  "fallback": true,
  "fallback_reason": "no_intent",
  "confidence": 0.0,
  "mode": "fallback",
  "response": "I didn't quite understand..."
}
```

If any field is missing, logging is incomplete.

---

## Red Flags During Analysis

🚨 **If you see**:
- Same intent missed 5+ times → language gap
- Same query asked 3+ ways → language variation
- User rephrases 3+ times → confusion loop

👉 **Action**: Add keywords, don't add rules

---

## What NOT to Do

❌ **Don't**:
- Add new intents after 1-2 queries
- Change thresholds based on single failures
- Add complex rules
- Optimize for edge cases

✅ **Do**:
- Wait for patterns (5+ same type)
- Add simple keywords
- Keep logic simple
- Focus on common cases

---

## Example: Real Improvement Cycle

### Week 1: Observe
```
50 queries collected
Analysis shows:
- "cost" missed 7 times
- "price" missed 3 times
- "how to apply" missed 2 times
```

### Week 2: Improve (Minimal)
```
Add to fees keywords: ["cost", "price"]
Add to admission keywords: ["how to apply"]
Deploy
```

### Week 3: Verify
```
Next 20 queries
- "cost" now detected: 6/7 ✓
- "price" now detected: 3/3 ✓
- "how to apply" now detected: 2/2 ✓
```

---

## Template: Copy This Weekly

```markdown
## Week X Analysis

**Queries analyzed**: 50
**Fallback rate**: X%
**Detection rate**: Y%

### Top Missed Intents
1. [Intent]: X queries, Y% detection
2. [Intent]: X queries, Y% detection
3. [Intent]: X queries, Y% detection

### Language Variations Found
- [Intent]: ["word1", "word2", "word3"]
- [Intent]: ["word1", "word2"]

### Confusion Loops
1. User asks → rephrases → rephrases
   Root cause: [keyword missing]

### New Intents Discovered
1. [Intent name]: X queries
   Examples: [query1], [query2]

### Actions for Next Week
1. Add keywords: [list]
2. Debug: [issue]
3. Monitor: [pattern]
```

---

## Key Principle

**Every query teaches you something.**

Not about bugs, but about:
- How users think
- How users speak
- What they care about
- What confuses them

This is your Phase 2 curriculum.

---

## Success Metrics (Real Ones)

After 50 queries:
- [ ] Identified top 3 language variations
- [ ] Identified top 3 missed intents
- [ ] Have 5+ examples of each
- [ ] Know what keywords to add
- [ ] Know what NOT to change

---

## When to Stop Analyzing

Stop when:
- New queries match existing patterns
- No new language variations appear
- Fallback reasons are clear
- Improvement path is obvious

Then: Make 1-2 targeted changes and re-deploy.

---

## Final Note

This sheet is your lifeline during beta.

Without it:
- You'll forget patterns
- You'll fix wrong things
- You'll guess instead of learn

With it:
- You'll see exactly what to improve
- You'll improve fast
- You'll avoid rule explosion

Use it religiously.
