# Multi-Intent Query Testing Results

**Date**: April 28, 2026  
**Status**: Observation only (DO NOT FIX)  
**Purpose**: Understand current behavior before real user testing

---

## Test Summary

| Test | Query | Course | All Answered? | Order Correct? | Issues |
|------|-------|--------|---------------|----------------|--------|
| 1 | "What is AIMS and fees for BCA" | BCA | ❌ NO | ✅ YES | Missing about_aims intent |
| 2 | "Tell me about AIMS, placement for MBA, and hostel facilities" | MBA | ✅ YES | ✅ YES | None |
| 3 | "BCA fees and admission process" | BCA | ❌ NO | ✅ YES | Missing fees intent |
| 4 | "Why AIMS and what courses are available" | None | ✅ YES | ❌ NO | Wrong order (too many intents) |
| 5 | "Fees, placements, and scholarships" | BCA | ✅ YES | ❌ NO | Wrong order (extra intents) |

---

## Statistics

- **Total tests**: 5
- **All intents answered**: 3/5 (60%)
- **Order correct**: 3/5 (60%)
- **No issues**: 1/5 (20%)

---

## Detailed Findings

### Test 1: "What is AIMS and fees for BCA" (BCA context)

**Expected intents**: about_aims, fees  
**Detected intents**: fees, admission  
**Status**: ❌ Missing about_aims

**Observation**:
- System detected fees correctly
- System detected admission (not expected)
- System did NOT detect about_aims
- Order is correct (fees appears first in query)

**Why this happened**:
- Query starts with "What is AIMS" but system didn't recognize it as about_aims intent
- System detected "admission" from "fees" keyword matching

---

### Test 2: "Tell me about AIMS, placement for MBA, and hostel facilities" (MBA context)

**Expected intents**: about_aims, placements, aims_features  
**Detected intents**: about_aims, placements, aims_features, courses  
**Status**: ✅ All answered (with extra)

**Observation**:
- System detected all expected intents
- System also detected courses (not expected)
- Order is correct
- Response includes all information

**Why this happened**:
- Multi-intent detection working well
- Query order preservation working
- Extra intent (courses) detected but not harmful

---

### Test 3: "BCA fees and admission process" (BCA context)

**Expected intents**: fees, admission  
**Detected intents**: admission  
**Status**: ❌ Missing fees

**Observation**:
- System detected admission correctly
- System did NOT detect fees
- Order is correct (admission appears first in response)
- System went into "apply" mode instead of structured mode

**Why this happened**:
- Stage controller detected "apply" intent (from "admission process")
- System switched to apply mode, bypassing structured layer
- Fees intent was not detected in apply mode

---

### Test 4: "Why AIMS and what courses are available" (No course context)

**Expected intents**: why_aims, courses  
**Detected intents**: about_aims, fees, placements, aims_features, why_aims, courses, scholarship  
**Status**: ✅ All answered (but wrong order)

**Observation**:
- System detected all expected intents
- System detected many extra intents
- Order is WRONG (detected about_aims first, but query asks why_aims first)
- Response includes too much information

**Why this happened**:
- Multi-intent detection is too aggressive
- Query order preservation not working correctly
- System is returning all possible intents instead of just the ones asked

---

### Test 5: "Fees, placements, and scholarships" (BCA context)

**Expected intents**: fees, placements, scholarship  
**Detected intents**: fees, placements, admission, courses, scholarship  
**Status**: ✅ All answered (but wrong order)

**Observation**:
- System detected all expected intents
- System detected extra intents (admission, courses)
- Order is WRONG (detected admission and courses, not in query)
- Response includes extra information

**Why this happened**:
- Multi-intent detection is too aggressive
- Query order preservation not working correctly
- System is returning extra intents

---

## Key Observations (DO NOT FIX)

### Observation 1: Missing Intent Detection (Tests 1, 3)

**Pattern**: Some intents are not detected even when keywords are present

**Examples**:
- "What is AIMS" → about_aims not detected
- "fees" → fees not detected in apply mode

**Why this matters**: Real users will ask questions that don't match current keywords

**What to do**: Collect real user data to see actual patterns

---

### Observation 2: Wrong Order (Tests 4, 5)

**Pattern**: Multi-intent detection returns intents in wrong order

**Examples**:
- Query: "Why AIMS and what courses"
- Expected order: why_aims, courses
- Actual order: about_aims, fees, placements, aims_features, why_aims, courses, scholarship

**Why this matters**: Response doesn't match user's question order

**What to do**: Collect real user data to see if this is a real problem

---

### Observation 3: Extra Intents (Tests 2, 4, 5)

**Pattern**: System detects intents that weren't asked for

**Examples**:
- Query: "Tell me about AIMS, placement for MBA, and hostel facilities"
- Detected: about_aims, placements, aims_features, **courses** (not asked)

**Why this matters**: Response includes information user didn't ask for

**What to do**: Collect real user data to see if users find this helpful or annoying

---

### Observation 4: Apply Mode Bypass (Test 3)

**Pattern**: Stage controller detects "apply" intent and bypasses structured layer

**Example**:
- Query: "BCA fees and admission process"
- System goes into "apply" mode
- Fees intent is not answered

**Why this matters**: User asked for fees but got apply guidance instead

**What to do**: Collect real user data to see if this is a real problem

---

## Course Context Handling

### With Course Context (BCA)
- ✅ Course data is correct (BCA fees shown, not other courses)
- ✅ No wrong course data appears
- ⚠️ Some intents not detected

### Without Course Context
- ✅ System handles it gracefully
- ⚠️ Too many intents detected
- ⚠️ Wrong order

---

## What This Means

### Engineering Perspective
- System is working (no crashes)
- Multi-intent detection is functional
- Course context is preserved correctly

### User Perspective
- 60% of queries answered completely
- 60% of queries in correct order
- 40% of queries have issues

### Real User Testing Perspective
- These are predicted problems
- Real users might have different problems
- Real users might not care about these issues
- Real users might find other issues

---

## What NOT To Do

❌ Fix the missing intents  
❌ Fix the wrong order  
❌ Fix the extra intents  
❌ Fix the apply mode bypass  

**Why?** These are based on 5 test queries. Real users will show different patterns.

---

## What TO Do

✅ Deploy to real users  
✅ Collect 100 real queries  
✅ Analyze real failure patterns  
✅ Fix based on real data  

---

## Next Steps

1. **Deploy to users** (this week)
2. **Collect 100 queries** (real, messy, imperfect)
3. **Analyze logs** (next week)
4. **Identify real patterns** (not predicted problems)
5. **Fix systematically** (based on data)

---

## Reminder

**These are observations, not problems to fix.**

Real user testing will show what actually matters.

Deploy and collect data.

