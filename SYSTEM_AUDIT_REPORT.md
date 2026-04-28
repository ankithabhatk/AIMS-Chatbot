# System Behavioral Audit Report
**Date:** April 26, 2026  
**Auditor:** Kiro AI  
**System:** AIMS College Chatbot - Decision & Guidance Engine

---

## Executive Summary

This audit examines the chatbot as a **behavioral decision system**, not just code. The focus is on **logic errors** that cause:
- Wrong recommendations (trust-breaking)
- Stage violations (flow breaks)
- Looping/repetition (UX killer)
- Memory leaks (context loss)
- Fallback abuse (intent override)

**Critical Finding:** The system has **6 major behavioral bugs** that directly impact user trust and conversion.

---

## Issue #1: Interest Override Bug (CRITICAL - Trust Breaker)

### Where It Occurs
**File:** `backend/app/services/counselor/guidance_engine.py`  
**Function:** `run_guidance_engine()` → `_score_course()`  
**Lines:** 48-75

### What Happens
When a user explicitly states their interest (e.g., "I'm interested in coding"), the system **ignores it** if their marks are slightly higher for a different course.

**Example Failure:**
```
User: "I got 70% and I'm interested in coding"
Expected: BCA (coding = tech)
Actual: BBA (because marks weight = 0.5, interest weight = 0.55, but marks threshold bonus overrides)
```

### Why It Happens
```python
# Marks scoring
if marks >= strong_marks:
    score += 0.5  # 70% for BBA → +0.5
    
# Interest scoring  
if matched_interest == course:
    score += 0.55  # Interest in BCA → +0.55
```

**The Bug:** When marks are "strong" for BBA (≥65%) but only "moderate" for BCA (≥65%), the marks bonus **stacks with other factors** and overrides the interest signal.

**Root Cause:** The scoring is additive without priority weighting. Interest should be **dominant** when explicitly stated.

### Exact Fix
```python
# In _score_course(), BEFORE marks scoring:
# Priority 1: Explicit interest match
if matched_interest == course:
    score += 0.70  # Increased from 0.55 to 0.70 to dominate
    reasons.append(f"your interest directly aligns with {course}")
    # Early bonus to ensure interest wins
    
# Priority 2: Marks (only if no interest conflict)
if marks is not None:
    if marks >= strong_marks:
        score += 0.40  # Reduced from 0.5 to 0.40
        reasons.append(f"marks ({marks}%) are well above the {min_marks}% requirement")
```

**Impact:** High - This causes **wrong course recommendations** which breaks user trust immediately.

---

## Issue #2: Stage Violation - "How to Apply" Triggers Guidance

### Where It Occurs
**File:** `backend/app/services/orchestration/engine.py`  
**Function:** `_execute_counselor_pipeline()`  
**Lines:** 727-850

### What Happens
When a user asks "how to apply" (clear conversion intent), the system routes them **back to guidance** instead of showing application steps.

**Example Failure:**
```
User: "How do I apply for BBA?"
Expected: Application process steps
Actual: "Based on your profile, BBA is a good fit. Does this direction feel right?"
```

### Why It Happens
```python
# Line 760-770: Intent detection
intents = detect_intents(query)  # Returns [("guidance", 0.8), ("conversion", 0.7)]

# Line 820: Guidance runs FIRST
if intent == "guidance":
    guidance_result = run_guidance(query, context)
    # ... bridge logic runs here
    
# Conversion never reached because guidance consumed the query
```

**Root Cause:** Intent priority is **score-based**, not **stage-based**. "How to apply" matches both guidance keywords ("which course") and conversion keywords ("apply"), but guidance wins on score.

### Exact Fix
```python
# In _execute_counselor_pipeline(), BEFORE intent loop (line ~815):

# STAGE ENFORCEMENT: Conversion intents override guidance
conversion_keywords = ["apply", "admission", "process", "documents", "how to join", "procedure", "steps"]
if any(word in query.lower() for word in conversion_keywords):
    # Force conversion mode, skip guidance
    from app.services.counselor.conversion import run_next_step_info
    top_course = context.get("locked_course") or (context.get("courses", [""])[0] if context.get("courses") else "your chosen course")
    answer = run_next_step_info(query, top_course, context)
    return {"answer": answer, "mode": "conversion", "intents": ["apply"], "confidence": 1.0}
```

**Impact:** High - Users asking "how to apply" get **stuck in guidance loop** instead of progressing to conversion.

---

## Issue #3: Conversion Stage Ignored on "Sounds Good"

### Where It Occurs
**File:** `backend/app/services/counselor/conversion.py`  
**Function:** `run_conversion_flow()`  
**Lines:** 95-145

### What Happens
When a user says "sounds good" after a recommendation, the system **doesn't advance the conversion stage** unless they use exact trigger phrases.

**Example Failure:**
```
Bot: "BBA is the best fit for you. Does this direction feel right?"
User: "Yeah, that works"
Expected: Move to visualization stage
Actual: Repeats guidance or asks another question
```

### Why It Happens
```python
# Line 105: Decision detection
if stage == "none" and detect_decision_signal(query):
    session["conversion_stage"] = "decision_confirmed"
    
# detect_decision_signal() checks:
DECISION_PATTERNS = [
    r"\bi think\b", r"\bi'll go with\b", r"\bseems good\b", r"\blooks good\b"
]

# "that works" is NOT in the list
```

**Root Cause:** Decision patterns are **too narrow**. Common affirmations like "that works", "okay", "sure" don't trigger stage advancement.

### Exact Fix
```python
# In conversion.py, update DECISION_PATTERNS (line ~15):
DECISION_PATTERNS = [
    r"\bi think\b",
    r"\bi'll go with\b",
    r"\bseems good\b",
    r"\blooks good\b",
    r"\bthat works\b",      # ADD
    r"\bthat's good\b",     # ADD
    r"\bokay\b",            # ADD
    r"\bok\b",              # ADD (but check for "ok" in other contexts)
    r"\bsure\b",            # ADD
    r"\byeah\b.*\bgood\b",  # ADD (catches "yeah that's good")
    r"\bsounds right\b",
    r"\bi'll do\b",
]
```

**Impact:** Medium-High - Users who **confirm decisions** don't progress, causing them to repeat themselves or drop off.

---

## Issue #4: Memory Leak - Marks Lost After Guidance

### Where It Occurs
**File:** `backend/app/services/counselor/memory.py`  
**Function:** `update_student_profile()`  
**Lines:** 35-80

### What Happens
When a user provides marks (e.g., "I got 65%"), the system stores it. But if they then ask a guidance question, the marks **disappear** from context.

**Example Failure:**
```
Turn 1: "I got 65%"
Turn 2: "Which course should I choose?"
Expected: Guidance uses 65% marks
Actual: Guidance says "Marks not yet provided"
```

### Why It Happens
```python
# Line 50-60: Marks update
if entities.get("marks"):
    try:
        marks_val = float(entities["marks"])
        if 0 <= marks_val <= 100:
            profile["marks"] = marks_val
        elif profile.get("marks") and profile["marks"] > 100:
            profile.pop("marks")  # BUG: Removes marks if invalid
```

**Root Cause:** The validation logic **removes marks** if a new invalid value is detected, instead of **keeping the old valid value**.

### Exact Fix
```python
# In update_student_profile(), replace lines 50-60:
if entities.get("marks"):
    try:
        marks_val = float(entities["marks"])
        if 0 <= marks_val <= 100:
            profile["marks"] = marks_val
        # REMOVED: Don't delete marks on invalid input
        # Just ignore the invalid value and keep the old one
    except (ValueError, TypeError):
        pass  # Keep existing marks
```

**Impact:** High - Users have to **repeat their marks** multiple times, causing frustration.

---

## Issue #5: Fallback Overrides Real Intent

### Where It Occurs
**File:** `backend/app/services/orchestration/engine.py`  
**Function:** `_execute_counselor_pipeline()`  
**Lines:** 700-750

### What Happens
When a user asks a specific question (e.g., "What's the BBA salary?"), the system triggers **fallback** instead of routing to the career engine.

**Example Failure:**
```
User: "What's the BBA salary?"
Expected: Career engine → salary data
Actual: "I want to make sure I guide you correctly. You can ask me about: Courses, Fees..."
```

### Why It Happens
```python
# Line 730: Intent detection
intents = detect_intents(query)  # Returns [("career", 0.55)]

# Line 735: Threshold check
if top_score < 0.6:
    return {"answer": "I want to guide you correctly...", "mode": "clarification"}
```

**Root Cause:** The threshold (0.6) is **too high**. Queries with clear intent but lower keyword density (e.g., "BBA salary" has only 1 keyword) score below 0.6 and trigger fallback.

### Exact Fix
```python
# In _execute_counselor_pipeline(), line ~735:
# Lower threshold for specific intents
SPECIFIC_INTENTS = ["career", "compare", "constraint"]
threshold = 0.5 if top_intent in SPECIFIC_INTENTS else 0.6

if top_score < threshold:
    return {"answer": "I want to guide you correctly...", "mode": "clarification"}
```

**Impact:** Medium - Users asking **specific questions** get generic fallback instead of answers.

---

## Issue #6: Looping - Same Response Repeated

### Where It Occurs
**File:** `backend/app/services/orchestration/engine.py`  
**Function:** `_execute_counselor_pipeline()`  
**Lines:** 950-1000

### What Happens
When a user asks similar questions in a row, the system **repeats the same response** without detecting the loop.

**Example Failure:**
```
Turn 1: "Which course is better?"
Bot: "Based on your profile, BBA is the best fit..."

Turn 2: "What about BCA?"
Bot: "Based on your profile, BBA is the best fit..."  (SAME RESPONSE)
```

### Why It Happens
```python
# Line 970: Similarity check
similarity = calculate_similarity(final_answer, last_answer)

if similarity > 0.8:
    logger.warning(f"[LOOP RISK] Similarity={similarity:.2f}")
    # BUT NO ACTION TAKEN - just logs the warning
```

**Root Cause:** The system **detects** loops but doesn't **prevent** them. It logs a warning but still returns the same response.

### Exact Fix
```python
# In _execute_counselor_pipeline(), after line 970:
similarity = calculate_similarity(final_answer, last_answer)

if similarity > 0.8:
    logger.warning(f"[LOOP RISK] Similarity={similarity:.2f} | turn={context.get('turn_count')}")
    
    # PREVENT LOOP: Inject variation
    variation_intros = [
        "Let me approach this differently.",
        "To give you a fresh perspective,",
        "Here's another way to look at it:",
        "Let me clarify that better:"
    ]
    import random
    intro = random.choice(variation_intros)
    final_answer = f"{intro}\n\n{final_answer}"
    
    # OR: Trigger clarification if loop persists
    if context.get("loop_count", 0) >= 2:
        final_answer = "I notice we're going in circles. Let me ask: what's the ONE thing you're most unsure about right now?"
        context["loop_count"] = 0
    else:
        context["loop_count"] = context.get("loop_count", 0) + 1
```

**Impact:** High - Looping **kills UX** and makes users feel unheard.

---

## Issue #7: Hardcoding vs Data - BBA/B.Com Fallback

### Where It Occurs
**File:** `backend/app/services/orchestration/engine.py`  
**Function:** `_execute_counselor_pipeline()`  
**Lines:** 727-745

### What Happens
When a user is confused, the system **hardcodes** "BBA or B.Com" as fallback options instead of using the guidance engine.

**Example Failure:**
```
User: "I'm confused, I got 80% and like coding"
Expected: BCA (based on interest + marks)
Actual: "BBA or B.Com seem like your strongest starting points"
```

### Why It Happens
```python
# Line 730-745: Confusion handling
if context.get("confusion_count", 0) >= 2:
    # HARDCODED:
    top_course = "BBA"
    second_course = "B.Com"
    
    return {
        "answer": f"Let's simplify this.\nBased on what you've told me so far, {top_course} or {second_course} seem like your strongest starting points."
    }
```

**Root Cause:** The confusion handler **bypasses the guidance engine** and uses hardcoded defaults.

### Exact Fix
```python
# In _execute_counselor_pipeline(), replace lines 730-745:
if context.get("confusion_count", 0) >= 2 and (is_confusion_query or top_intent == "unknown"):
    # Use actual guidance instead of hardcoded BBA/B.Com
    from app.services.counselor.guidance_engine import run_guidance_engine
    guidance = run_guidance_engine(query, context)
    top_course = guidance.get("top_course", "BBA")
    recommended = guidance.get("recommended_courses", ["BBA", "B.Com"])
    second_course = recommended[1] if len(recommended) > 1 else "B.Com"
    
    return {
        "answer": f"Let's simplify this.\nBased on what you've told me so far, {top_course} or {second_course} seem like your strongest starting points.\n\nWould you like to look at the fees for these, or discuss which one fits your salary goals better?",
        "mode": "guidance", 
        "intents": ["guidance"], 
        "confidence": 1.0
    }
```

**Impact:** Medium - Confused users get **generic recommendations** instead of personalized guidance.

---

## Summary Table

| Issue | File | Impact | Type | Fix Complexity |
|-------|------|--------|------|----------------|
| #1: Interest Override | guidance_engine.py | **CRITICAL** | Decision Correctness | Low |
| #2: Stage Violation | engine.py | **HIGH** | Stage Integrity | Low |
| #3: Conversion Ignored | conversion.py | **HIGH** | Stage Integrity | Low |
| #4: Memory Leak | memory.py | **HIGH** | Memory Consistency | Low |
| #5: Fallback Abuse | engine.py | **MEDIUM** | Fallback Override | Low |
| #6: Looping | engine.py | **HIGH** | Loop Detection | Medium |
| #7: Hardcoding | engine.py | **MEDIUM** | Data vs Hardcode | Low |

---

## Priority Fixes (Do These First)

### 1. Issue #1 - Interest Override (CRITICAL)
**Why:** Breaks trust immediately. User says "I like coding" → gets BBA recommendation.  
**Fix Time:** 5 minutes  
**Impact:** Prevents wrong recommendations

### 2. Issue #4 - Memory Leak (HIGH)
**Why:** Users have to repeat marks multiple times.  
**Fix Time:** 2 minutes  
**Impact:** Reduces frustration

### 3. Issue #2 - Stage Violation (HIGH)
**Why:** Users asking "how to apply" get stuck in guidance loop.  
**Fix Time:** 5 minutes  
**Impact:** Fixes conversion flow

### 4. Issue #6 - Looping (HIGH)
**Why:** Same response repeated kills UX.  
**Fix Time:** 10 minutes  
**Impact:** Prevents user drop-off

### 5. Issue #3 - Conversion Ignored (HIGH)
**Why:** Users confirming decisions don't progress.  
**Fix Time:** 3 minutes  
**Impact:** Improves conversion rate

---

## Testing Recommendations

After applying fixes, test these scenarios:

1. **Interest Override Test:**
   - Input: "I got 70% and I'm interested in coding"
   - Expected: BCA recommended
   
2. **Stage Violation Test:**
   - Input: "How do I apply for BBA?"
   - Expected: Application steps, not guidance
   
3. **Memory Persistence Test:**
   - Turn 1: "I got 65%"
   - Turn 2: "Which course?"
   - Expected: Guidance uses 65%
   
4. **Loop Detection Test:**
   - Turn 1: "Which course?"
   - Turn 2: "What about BCA?"
   - Expected: Different response structure

---

## Architecture Observations

### What's Working Well
1. **Modular Design:** Separation of concerns (router → engines → composer)
2. **Intent Detection:** Keyword-based scoring is fast and mostly accurate
3. **Memory System:** Session-based storage works for demo scale

### What Needs Improvement
1. **Priority System:** No clear hierarchy (interest > marks > salary)
2. **Stage Machine:** Conversion stages exist but aren't enforced
3. **Loop Prevention:** Detection exists but no action taken
4. **Fallback Logic:** Too aggressive, overrides real intents

---

## End of Report
