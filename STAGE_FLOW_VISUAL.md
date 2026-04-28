# Stage Controller Flow Diagram

## Stage Priority Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    STAGE PRIORITY                            │
│                                                              │
│  APPLY (100)           ← Highest Priority                   │
│      ↓                                                       │
│  DECISION_LOCKED (90)  ← Course Locked, No Switching        │
│      ↓                                                       │
│  DECISION (80)         ← User Confirms, Lock Course         │
│      ↓                                                       │
│  GUIDANCE (50)         ← User Exploring Options             │
│      ↓                                                       │
│  CONFUSION (30)        ← User Stuck, Simplify               │
│      ↓                                                       │
│  FALLBACK (0)          ← No Signal, Ultimate Fallback       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Complete User Journey

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER JOURNEY                                  │
└──────────────────────────────────────────────────────────────────────┘

User: "I got 75% in 12th"
    ↓
┌─────────────────────┐
│  STAGE: GUIDANCE    │  ← Has signal (marks)
│  ACTION: guidance   │
└─────────────────────┘
    ↓
System: "Based on your 75%, BCA and BBA are strong options..."
    ↓
User: "BCA sounds good"
    ↓
┌─────────────────────┐
│  STAGE: DECISION    │  ← Decision detected
│  ACTION: lock_and_  │
│         guide       │
└─────────────────────┘
    ↓
[COURSE LOCKED: BCA]  ← Decision lock applied
    ↓
System: "Great choice! BCA will give you strong tech skills..."
    ↓
User: "What about fees?"
    ↓
┌─────────────────────┐
│  STAGE: DECISION_   │  ← Course already locked
│         LOCKED      │
│  ACTION: deepening  │
└─────────────────────┘
    ↓
System: "BCA fees are ₹X per year..." (Only talks about BCA)
    ↓
User: "How to apply?"
    ↓
┌─────────────────────┐
│  STAGE: APPLY       │  ← Apply overrides locked
│  ACTION: apply      │  ← (Priority 100 > 90)
└─────────────────────┘
    ↓
System: "Here are the steps to apply for BCA:
         1. Registration...
         2. Form Filling...
         3. Document Upload..."
```

---

## Stage Detection Logic

```
┌──────────────────────────────────────────────────────────────────────┐
│                      STAGE DETECTION                                  │
└──────────────────────────────────────────────────────────────────────┘

Query: "how to apply"
    ↓
Check: Contains apply keywords? → YES
    ↓
STAGE: APPLY (Priority 100)
    ↓
ACTION: apply
    ↓
RESULT: Structured admission steps

─────────────────────────────────────────────────────────────────────

Query: "what about fees" + context.locked_course = "BCA"
    ↓
Check: Course already locked? → YES
    ↓
STAGE: DECISION_LOCKED (Priority 90)
    ↓
ACTION: deepening
    ↓
RESULT: Answer about BCA only, no course switching

─────────────────────────────────────────────────────────────────────

Query: "BCA sounds good"
    ↓
Check: Contains decision keywords? → YES
    ↓
STAGE: DECISION (Priority 80)
    ↓
ACTION: lock_and_guide
    ↓
RESULT: Run guidance, lock top course, return response

─────────────────────────────────────────────────────────────────────

Query: "I got 70%"
    ↓
Check: Has marks/interest/goal signal? → YES
    ↓
STAGE: GUIDANCE (Priority 50)
    ↓
ACTION: guidance
    ↓
RESULT: Run guidance engine, recommend courses

─────────────────────────────────────────────────────────────────────

Query: "I'm confused"
    ↓
Check: Contains confusion keywords? → YES
    ↓
STAGE: CONFUSION (Priority 30)
    ↓
ACTION: simplify
    ↓
RESULT: Simplified guidance, ask for basic info

─────────────────────────────────────────────────────────────────────

Query: "hello"
    ↓
Check: Any signal? → NO
    ↓
STAGE: FALLBACK (Priority 0)
    ↓
ACTION: fallback
    ↓
RESULT: Ultimate fallback message
```

---

## Decision Locking Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                      DECISION LOCKING                                 │
└──────────────────────────────────────────────────────────────────────┘

User: "BCA sounds good"
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 1. STAGE DETECTION                                                   │
│    - Detect: DECISION stage                                          │
│    - Action: lock_and_guide                                          │
│    - should_lock: True                                               │
└─────────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. ENTITY EXTRACTION                                                 │
│    - Extract: courses = ["BCA"]                                      │
│    - Extract: marks = None                                           │
│    - Extract: interests = None                                       │
└─────────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. CONVERSION FLOW                                                   │
│    - Detect: decision_signal = True                                  │
│    - Set: conversion_stage = "decision_confirmed"                    │
│    - Return: conversion response                                     │
└─────────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. DECISION LOCK (CRITICAL)                                          │
│    - Check: conversion_stage == "decision_confirmed"? → YES          │
│    - Check: locked_course exists? → NO                               │
│    - Extract: course_to_lock = "BCA" (from entities)                 │
│    - Execute: lock_decision(context, "BCA")                          │
│    - Store: context["locked_course"] = "BCA"                         │
│    - Persist: update_student_profile(session_id, {"locked_course"})  │
└─────────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 5. LOCKED STATE                                                      │
│    - locked_course: "BCA"                                            │
│    - lock_timestamp: 1234567890                                      │
│    - conversion_stage: "decision_confirmed"                          │
└─────────────────────────────────────────────────────────────────────┘
    ↓
[COURSE LOCKED: BCA] ← Cannot be changed
```

---

## Locked Course Behavior

```
┌──────────────────────────────────────────────────────────────────────┐
│                   LOCKED COURSE BEHAVIOR                              │
└──────────────────────────────────────────────────────────────────────┘

Context: locked_course = "BCA"

User: "I'm interested in business"
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE: DECISION_LOCKED (Priority 90)                                 │
│ - Locked course: BCA                                                 │
│ - New interest: business (would suggest BBA)                         │
│ - Action: deepening (NOT guidance)                                   │
│ - Result: Talk about BCA only, ignore business interest              │
└─────────────────────────────────────────────────────────────────────┘
    ↓
System: "You've chosen BCA. What would you like to know more about?"

─────────────────────────────────────────────────────────────────────

User: "What about fees?"
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE: DECISION_LOCKED (Priority 90)                                 │
│ - Locked course: BCA                                                 │
│ - Query: fees                                                        │
│ - Action: deepening                                                  │
│ - Result: BCA fees only                                              │
└─────────────────────────────────────────────────────────────────────┘
    ↓
System: "BCA fees are ₹X per year..."

─────────────────────────────────────────────────────────────────────

User: "How to apply?"
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE: APPLY (Priority 100) ← Overrides DECISION_LOCKED             │
│ - Locked course: BCA                                                 │
│ - Query: apply                                                       │
│ - Action: apply                                                      │
│ - Result: Structured BCA admission steps                             │
└─────────────────────────────────────────────────────────────────────┘
    ↓
System: "Here are the steps to apply for BCA:
         1. Registration...
         2. Form Filling..."
```

---

## Stage Priority Override Example

```
┌──────────────────────────────────────────────────────────────────────┐
│                   STAGE PRIORITY OVERRIDE                             │
└──────────────────────────────────────────────────────────────────────┘

Scenario: User has locked course but asks to apply

Context:
- locked_course: "BBA"
- conversion_stage: "decision_confirmed"

User: "how to apply"
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE DETECTION (Multiple Stages Detected)                           │
│                                                                       │
│ 1. DECISION_LOCKED (Priority 90) ← Course is locked                  │
│ 2. APPLY (Priority 100)          ← Apply keywords detected           │
│                                                                       │
│ WINNER: APPLY (100 > 90)                                             │
└─────────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ ACTION: apply                                                         │
│ - Use locked course: "BBA"                                           │
│ - Return: Structured admission steps for BBA                         │
└─────────────────────────────────────────────────────────────────────┘
    ↓
System: "Here are the steps to apply for BBA:
         1. Registration: Visit our portal...
         2. Form Filling: Enter your details...
         3. Document Upload: Upload marksheets..."

KEY INSIGHT: Apply intent (Priority 100) overrides locked state (Priority 90)
             but still uses the locked course for the apply flow.
```

---

## Confusion Handling Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                     CONFUSION HANDLING                                │
└──────────────────────────────────────────────────────────────────────┘

User: "I'm confused"
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE: CONFUSION (Priority 30)                                       │
│ - Confusion keywords detected                                        │
│ - Action: simplify                                                   │
└─────────────────────────────────────────────────────────────────────┘
    ↓
System: "Let's simplify this. Tell me:
         1. Your 12th marks (%)
         2. What you're interested in (business/tech/finance/hospitality)"
    ↓
User: "I got 65% and like technology"
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE: GUIDANCE (Priority 50) ← Confusion resolved, has signal      │
│ - marks: 65                                                          │
│ - interests: technology → BCA                                        │
│ - Action: guidance                                                   │
└─────────────────────────────────────────────────────────────────────┘
    ↓
System: "Based on your 65% and interest in technology, BCA is your best fit..."
```

---

## Fallback Trigger Conditions

```
┌──────────────────────────────────────────────────────────────────────┐
│                      FALLBACK TRIGGERS                                │
└──────────────────────────────────────────────────────────────────────┘

FALLBACK ONLY TRIGGERS WHEN:

✅ No apply keywords
✅ No locked course
✅ No decision keywords
✅ No marks in query or context
✅ No interests in query or context
✅ No courses in query or context
✅ No goal signals (salary, job, abroad, etc.)
✅ No confusion keywords

Example Queries That Trigger Fallback:
- "hello"
- "hi"
- "hey"
- "what's up"
- "tell me something"

Example Queries That DON'T Trigger Fallback:
- "I got 70%" → GUIDANCE (has marks)
- "I like coding" → GUIDANCE (has interest)
- "BCA sounds good" → DECISION (has decision keyword)
- "how to apply" → APPLY (has apply keyword)
- "I'm confused" → CONFUSION (has confusion keyword)
```

---

## Summary

The Stage Controller provides:

1. **Clear Priority Hierarchy**: APPLY > DECISION_LOCKED > DECISION > GUIDANCE > CONFUSION > FALLBACK
2. **Decision Locking**: Course locks after user confirms, cannot be switched
3. **Stage Override**: Higher priority stages override lower priority stages
4. **Behavioral Control**: System behaves like decision engine, not chatbot
5. **Deterministic Flow**: Same input → same stage → same action

**Result**: Chatbot → Decision Engine ✅
