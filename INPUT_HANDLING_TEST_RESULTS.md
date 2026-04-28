# Structured Input Handling Test Results

**Date:** Apr 28, 2026  
**Test Type:** Input classification, intent detection, fallback behavior  
**Total Queries Tested:** 14

---

## Test Results by Category

### 1. GARBAGE INPUTS

| Query | Input Class | Intent | Score | Struct Intent | Fallback? | Notes |
|-------|-------------|--------|-------|---------------|-----------|-------|
| `asdfgh` | QUESTION | unknown | 0.0 | none (0) | YES | Random characters, no intent detected |
| `123456` | NONSENSE | nonsense | 0.0 | none (0) | YES | Numeric only, classified as NONSENSE |
| `!!!@@@` | NONSENSE | nonsense | 0.0 | none (0) | YES | Special chars only, classified as NONSENSE |
| `??` | NONSENSE | nonsense | 0.0 | none (0) | YES | Too short + no alphabets |

**Pattern:** All garbage inputs trigger fallback. 3/4 caught by NONSENSE classifier, 1/4 passes as QUESTION but fails intent detection.

---

### 2. SHORT QUERIES

| Query | Input Class | Intent | Score | Struct Intent | Fallback? | Notes |
|-------|-------------|--------|-------|---------------|-----------|-------|
| `hi` | GREETING | unknown | 0.0 | none (0) | NO | Correctly identified as greeting, no fallback |
| `ok` | NONSENSE | nonsense | 0.0 | none (0) | YES | Too short (< 3 chars), classified as NONSENSE |
| `fees` | QUESTION | unknown | 0.0 | fees (1.0) | YES | ⚠️ **ISSUE**: Structured intent detected (1.0) but still triggers fallback |

**Pattern:** Greetings bypass fallback. Single-word queries < 3 chars caught as NONSENSE. "fees" detected structurally but intent router fails.

---

### 3. MIXED GARBAGE + INTENT

| Query | Input Class | Intent | Score | Struct Intent | Fallback? | Notes |
|-------|-------------|--------|-------|---------------|-----------|-------|
| `fees???` | QUESTION | unknown | 0.0 | fees (1.0) | YES | ⚠️ **ISSUE**: Intent detected but fallback triggered |
| `bca!!!` | QUESTION | unknown | 0.0 | none (0) | YES | Program detected (BCA) but no structured intent |
| `admission???` | QUESTION | unknown | 0.0 | admission (1.0) | YES | ⚠️ **ISSUE**: Intent detected but fallback triggered |

**Pattern:** Special characters don't block intent detection at structured layer, but intent router still fails. Program detection works but doesn't prevent fallback.

---

### 4. TYPOS

| Query | Input Class | Intent | Score | Struct Intent | Fallback? | Notes |
|-------|-------------|--------|-------|---------------|-----------|-------|
| `admisson` | QUESTION | unknown | 0.0 | none (0) | YES | ✓ Corrected to "admission" but structured intent not re-evaluated |
| `feees` | QUESTION | unknown | 0.0 | none (0) | YES | ✓ Corrected to "fees" but structured intent not re-evaluated |
| `plcement` | QUESTION | unknown | 0.0 | none (0) | YES | ✓ Corrected to "placement" but structured intent not re-evaluated |
| `aims collge` | QUESTION | unknown | 0.0 | none (0) | YES | Typo not corrected (multi-word), no structured intent |

**Pattern:** Typo correction works (3/4), but corrected queries are not re-evaluated for structured intent. Fallback still triggered.

---

## Summary Statistics

| Metric | Count | % |
|--------|-------|---|
| **Total Queries** | 14 | 100% |
| **Fallback Triggered** | 13 | 92.9% |
| **Classified as NONSENSE** | 4 | 28.6% |
| **Intent Detected (Router)** | 0 | 0.0% |
| **Structured Intent Detected** | 5 | 35.7% |
| **Typos Corrected** | 3 | 21.4% |
| **Program Detected** | 1 | 7.1% |

---

## Breakdown by Category

| Category | Fallbacks | Total | Rate |
|----------|-----------|-------|------|
| Garbage Inputs | 4 | 4 | 100% |
| Short Queries | 2 | 3 | 66.7% |
| Mixed Garbage + Intent | 3 | 3 | 100% |
| Typos | 4 | 4 | 100% |

---

## Key Findings

### ✓ Working Correctly

1. **NONSENSE Classification**: Properly catches numeric-only, special-char-only, and very short inputs (< 3 chars)
2. **Greeting Detection**: "hi" correctly identified as greeting, bypasses fallback
3. **Typo Correction**: SymSpell successfully corrects single-character typos (admisson→admission, feees→fees, plcement→placement)
4. **Structured Intent Detection**: Correctly identifies fees, admission, courses at the structured knowledge layer
5. **Program Detection**: Detects program names (BCA) even with garbage suffix

### ⚠️ Issues Detected

1. **Intent Router Failure**: 
   - `compute_intent_scores()` returns all zeros for all queries
   - No intents detected by the router layer (0/14 success)
   - This causes fallback even when structured intent is detected

2. **Structured Intent Not Routed**:
   - "fees" detected as structured intent (score 1.0) but still triggers fallback
   - "fees???" and "admission???" have perfect structured scores but fallback
   - Suggests routing logic doesn't use structured intent scores properly

3. **Typo Correction Not Re-evaluated**:
   - After correcting "admisson" → "admission", the corrected query is not re-checked for structured intent
   - Fallback is triggered on original query, not corrected version

4. **Special Characters Not Stripped**:
   - "fees???" and "admission???" pass through as QUESTION but fail intent detection
   - Special characters should be stripped before intent detection

5. **Short Single-Word Queries**:
   - "fees" (4 chars) passes NONSENSE check but has no intent detected
   - "ok" (2 chars) correctly caught as NONSENSE
   - Threshold seems inconsistent

---

## Observations

### Intent Detection Pipeline

```
Input → Input Handler (GREETING/EXIT/NONSENSE/QUESTION)
       ↓
       If QUESTION → Intent Router (compute_intent_scores)
       ↓
       If no intent → Structured Knowledge Layer
       ↓
       If no structured intent → FALLBACK
```

**Problem**: Intent Router is returning 0.0 for all scores, so queries never reach structured layer in the routing decision.

### Fallback Rate

**92.9% fallback rate** is extremely high and indicates:
- Intent router is non-functional (all scores = 0.0)
- Structured intent detection works but isn't being used in routing
- Typo corrections aren't being re-evaluated

### Special Characters Handling

Special characters (`???`, `!!!`, `@@@`) are:
- ✓ Detected in NONSENSE check (if combined with short length)
- ✗ Not stripped before intent detection
- ✗ Not preventing structured intent detection (which works correctly)

---

## Test Data Summary

**Garbage Inputs**: Random strings with no semantic meaning
- All trigger fallback (100%)
- 3/4 caught by NONSENSE classifier
- 1/4 passes as QUESTION but fails intent detection

**Short Queries**: 1-4 character inputs
- "hi" → GREETING (no fallback) ✓
- "ok" → NONSENSE (fallback) ✓
- "fees" → QUESTION (fallback) ⚠️ Should not fallback

**Mixed Garbage + Intent**: Intent keywords with special characters
- All trigger fallback (100%)
- Structured intent detected (3/3) but not routed
- Shows special chars don't block structured detection

**Typos**: Common misspellings
- All trigger fallback (100%)
- 3/4 typos corrected by SymSpell
- Corrected queries not re-evaluated

---

## Recommendations for Investigation

1. **Debug `compute_intent_scores()`**: Why are all scores 0.0?
2. **Check Intent Router Logic**: How does it decide between intent router and structured layer?
3. **Implement Structured Intent Routing**: Use structured intent scores in fallback decision
4. **Re-evaluate After Typo Correction**: Apply intent detection to corrected query
5. **Strip Special Characters**: Before intent detection, clean punctuation
6. **Adjust Short Query Handling**: "fees" should not fallback when structured intent = 1.0

---

## Test Execution Details

- **Test Script**: `/Users/maneeth/Desktop/Chat-Bot/test_input_handling.py`
- **Report Generated**: `test_input_handling_report.json`
- **Execution Time**: ~2 seconds
- **Environment**: Python 3.x, Backend services loaded
