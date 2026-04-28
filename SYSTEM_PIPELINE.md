# AIMS Assistant System Pipeline

## Request Flow (Simplified)

```
User Query
    ↓
[1] INPUT VALIDATION ← NEW (Phase 1)
    ├─ Empty? → Reject
    ├─ Too short? → Reject
    ├─ Pure garbage? → Reject
    └─ Valid → Continue
    ↓
[2] SPELL CORRECTION ← NEW (Phase 1)
    ├─ Word-level SymSpell
    ├─ Correct typos (edit distance = 1)
    └─ Preserve sentence structure
    ↓
[3] INTENT DETECTION
    ├─ Single intent → Route to handler
    └─ Multiple intents ← NEW (Phase 1) → Handle each separately
    ↓
[4] ROUTING DECISION
    ├─ Tool Intent? (location, contact)
    │   └─ → Tool Layer
    ├─ Structured Intent? (fees, admission, about_aims, etc.)
    │   └─ → Structured Layer
    └─ Other?
        └─ → Counselor Layer
    ↓
[5] RESPONSE GENERATION
    ├─ Structured: Return from knowledge base
    ├─ Tool: Return from tool responses
    └─ Counselor: Run counselor pipeline
    ↓
[6] LOGGING ← NEW (Phase 1)
    └─ Log all decisions for analysis
    ↓
Response to User
```

---

## Layer Details

### Layer 1: Input Validation (NEW - Phase 1)
**Purpose**: Prevent garbage input from wasting resources

**Checks**:
- Not empty
- Length >= 3 characters
- Contains at least one alphanumeric character

**Output**: Valid query or rejection message

---

### Layer 2: Spell Correction (NEW - Phase 1)
**Purpose**: Handle typos automatically

**Method**: Word-level SymSpell
- Split query into words
- Correct each word independently
- Only correct if edit distance = 1
- Preserve original sentence structure

**Example**:
```
Input:  "feees for bca"
Output: "fees for bca"
```

---

### Layer 3: Intent Detection
**Purpose**: Understand what user is asking

**Single Intent** (existing):
- Detect top intent
- Route to appropriate layer

**Multiple Intents** (NEW - Phase 1):
- Detect ALL intents with score >= 0.4
- Handle each separately
- Combine responses

**Example**:
```
Input:  "What is AIMS and fees for BCA"
Intent 1: about_aims (score: 0.95)
Intent 2: fees (score: 0.9)
Output: Both answers combined
```

---

### Layer 4: Routing Decision
**Purpose**: Choose which layer handles the query

**Decision Tree**:
```
if intent in ["location", "contact"]:
    → Tool Layer (conversational responses)
elif intent in ["fees", "admission", "courses", "about_aims", "why_aims", "aims_features"]:
    → Structured Layer (knowledge base)
else:
    → Counselor Layer (guidance, reasoning)
```

---

### Layer 5: Response Generation

#### Structured Layer
- Looks up answer in knowledge base
- Returns deterministic response
- No hallucination risk
- Fast (< 10ms)

**Intents**:
- `fees` - Fee structure
- `admission` - Admission process
- `courses` - Course information
- `placements` - Placement statistics
- `about_aims` - Institution information
- `why_aims` - Why choose AIMS
- `aims_features` - Campus facilities

#### Tool Layer
- Returns conversational responses
- Handles location, contact queries
- Provides CTAs (call-to-action)

**Intents**:
- `location` - Campus location
- `contact` - Contact information

#### Counselor Layer
- Runs guidance engine
- Handles comparisons
- Provides career advice
- Falls back to generic response if needed

---

### Layer 6: Logging (NEW - Phase 1)
**Purpose**: Visibility into system decisions

**Log Levels**:
```
[VALIDATION]           - Input validation decisions
[TYPO_CORRECTIONS]     - Spell corrections applied
[TYPO_WORD]            - Individual word corrections
[MULTI_INTENT]         - Multiple intents detected
[MULTI_INTENT_HANDLER] - Multi-intent processing
[ROUTING]              - Routing decisions
[STRUCTURED]           - Structured layer processing
```

---

## Data Flow Example

### Example 1: Simple Query
```
User: "fees for bca"
    ↓
[1] Validation: ✅ Valid
[2] Spell Correction: No typos
[3] Intent Detection: fees (score: 0.9)
[4] Routing: Structured Layer
[5] Response: "BCA fee structure: ₹30,000 - ₹60,000"
[6] Logging: [ROUTING] structured wins
```

### Example 2: Typo Query
```
User: "feees for bca"
    ↓
[1] Validation: ✅ Valid
[2] Spell Correction: "feees" → "fees"
[3] Intent Detection: fees (score: 0.9)
[4] Routing: Structured Layer
[5] Response: "BCA fee structure: ₹30,000 - ₹60,000"
[6] Logging: [TYPO_CORRECTIONS] 'feees' → 'fees'
```

### Example 3: Multi-Intent Query
```
User: "What is AIMS and fees for BCA"
    ↓
[1] Validation: ✅ Valid
[2] Spell Correction: No typos
[3] Intent Detection: 
    - about_aims (score: 0.95)
    - fees (score: 0.9)
[4] Routing: Structured Layer (multiple intents)
[5] Response: 
    **ABOUT_AIMS:** About AIMS Institutes...
    **FEES:** BCA fee structure...
[6] Logging: [MULTI_INTENT] Detected 2 intents
```

### Example 4: Invalid Query
```
User: "!!!???"
    ↓
[1] Validation: ❌ Invalid (no alphanumeric)
[2] Response: "I didn't understand that..."
[6] Logging: [VALIDATION] Query rejected
```

---

## Performance Characteristics

| Layer | Time | Notes |
|-------|------|-------|
| Input Validation | < 1ms | String checks only |
| Spell Correction | 50-100ms | SymSpell lookup per word |
| Intent Detection | < 5ms | Scoring already done |
| Routing | < 1ms | Simple if/else |
| Structured Response | < 10ms | Dictionary lookup |
| Tool Response | < 5ms | Predefined responses |
| Counselor Layer | 100-500ms | May call LLM |
| **Total** | **100-600ms** | Acceptable for production |

---

## Scalability Notes

### Current System (Phase 1)
- ✅ Handles known questions well
- ✅ Handles typos
- ✅ Handles multiple questions
- ⚠️ Rigid keyword matching
- ⚠️ No semantic understanding

### Future Improvements (Phase 2+)
- Add semantic intent detection (embeddings)
- Add context memory (multi-turn)
- Add reasoning layer
- Add user feedback loop

### When to Add Complexity
Only add when:
1. You have logs showing failures
2. You understand the failure pattern
3. You have a specific solution
4. You've tested it doesn't break existing functionality

---

## Key Design Principles

1. **Deterministic** - Same input → Same output
2. **Observable** - Full logging of decisions
3. **Predictable** - No AI guessing
4. **Safe** - Graceful degradation
5. **Fast** - < 1 second response time
6. **Maintainable** - Clear layer separation

---

## Debugging Guide

### Query not being understood?
1. Check `[VALIDATION]` logs - Is it being rejected?
2. Check `[TYPO_CORRECTIONS]` logs - Was it corrected?
3. Check `[ROUTING]` logs - Which layer handled it?
4. Check layer-specific logs - What went wrong?

### Wrong answer?
1. Check `[ROUTING]` logs - Was it routed to correct layer?
2. Check intent detection - Was intent correct?
3. Check knowledge base - Is answer correct?

### Slow response?
1. Check `[TYPO_CORRECTIONS]` - Is SymSpell slow?
2. Check layer logs - Which layer is slow?
3. Consider caching if pattern repeats

---

## Next Steps

### Phase 2 (After collecting logs)
- Analyze real user queries
- Identify failure patterns
- Design targeted improvements
- Implement incrementally

### Phase 3 (When needed)
- Add semantic understanding
- Add context memory
- Add reasoning layer
- Hybrid rule + AI system

---

## Summary

The AIMS Assistant is built as a **layered pipeline**:
1. Validate input
2. Correct typos
3. Detect intents (single or multiple)
4. Route to appropriate layer
5. Generate response
6. Log everything

This design is **robust, observable, and maintainable** — exactly what production systems need.
