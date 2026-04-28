# Input Handling Test Summary - Quick Reference

## All Test Cases (14 queries)

| Query | Intent | Correct? | Fallback? | Notes |
|-------|--------|----------|-----------|-------|
| **GARBAGE INPUTS** |
| asdfgh | unknown | ✗ No | YES | Random chars, no intent detected |
| 123456 | nonsense | ✓ Yes | YES | Numeric only, NONSENSE classifier works |
| !!!@@@ | nonsense | ✓ Yes | YES | Special chars only, NONSENSE classifier works |
| ?? | nonsense | ✓ Yes | YES | Too short, NONSENSE classifier works |
| **SHORT QUERIES** |
| hi | greeting | ✓ Yes | NO | Greeting detected, no fallback ✓ |
| ok | nonsense | ✓ Yes | YES | Too short, NONSENSE classifier works |
| fees | fees (struct) | ✗ No | YES | ⚠️ Structured intent detected but fallback triggered |
| **MIXED GARBAGE + INTENT** |
| fees??? | fees (struct) | ✗ No | YES | ⚠️ Structured intent (1.0) but fallback triggered |
| bca!!! | BCA (program) | ✗ No | YES | Program detected but no structured intent |
| admission??? | admission (struct) | ✗ No | YES | ⚠️ Structured intent (1.0) but fallback triggered |
| **TYPOS** |
| admisson | admission (corrected) | ✗ No | YES | ✓ Typo corrected but not re-evaluated |
| feees | fees (corrected) | ✗ No | YES | ✓ Typo corrected but not re-evaluated |
| plcement | placement (corrected) | ✗ No | YES | ✓ Typo corrected but not re-evaluated |
| aims collge | none | ✗ No | YES | Typo not corrected (multi-word) |

---

## Pattern Analysis

### What Works ✓
- **NONSENSE Detection**: Catches numeric, special-char-only, very short inputs
- **Greeting Detection**: "hi" correctly identified, no fallback
- **Typo Correction**: SymSpell corrects single-char typos (admisson→admission, feees→fees, plcement→placement)
- **Structured Intent Detection**: Correctly identifies fees, admission, courses at knowledge layer
- **Program Detection**: Identifies BCA even with garbage suffix

### What Fails ✗
- **Intent Router**: Returns 0.0 for all queries (0/14 detected)
- **Structured Intent Routing**: Detected but not used in fallback decision
- **Special Character Handling**: Not stripped before intent detection
- **Typo Re-evaluation**: Corrected queries not re-checked for intent
- **Short Single-Word Queries**: "fees" should not fallback when structured intent = 1.0

---

## Statistics

| Metric | Value |
|--------|-------|
| Total Queries | 14 |
| Fallback Rate | 92.9% (13/14) |
| NONSENSE Caught | 28.6% (4/14) |
| Intent Router Success | 0% (0/14) |
| Structured Intent Detected | 35.7% (5/14) |
| Typos Corrected | 21.4% (3/14) |
| Program Detected | 7.1% (1/14) |

---

## Critical Issues

### 🔴 Issue #1: Intent Router Non-Functional
- `compute_intent_scores()` returns all zeros
- No intents detected by router layer
- Causes fallback even when structured intent exists

### 🔴 Issue #2: Structured Intent Not Routed
- "fees" (score 1.0) → fallback triggered
- "fees???" (score 1.0) → fallback triggered  
- "admission???" (score 1.0) → fallback triggered
- Routing logic doesn't use structured scores

### 🟡 Issue #3: Typo Correction Not Re-evaluated
- "admisson" → corrected to "admission"
- But corrected query not re-checked for structured intent
- Fallback triggered on original, not corrected version

### 🟡 Issue #4: Special Characters Not Stripped
- "fees???" and "admission???" pass as QUESTION
- Special chars should be removed before intent detection
- Structured layer handles it correctly, router doesn't

---

## Detailed Findings

### Garbage Inputs (4/4 fallback)
```
asdfgh      → QUESTION, unknown intent, fallback ✗
123456      → NONSENSE, caught ✓
!!!@@@      → NONSENSE, caught ✓
??          → NONSENSE, caught ✓
```
**Issue**: "asdfgh" passes NONSENSE check but has no intent detected

### Short Queries (2/3 fallback)
```
hi          → GREETING, no fallback ✓
ok          → NONSENSE, caught ✓
fees        → QUESTION, unknown intent, fallback ✗
```
**Issue**: "fees" has structured intent (1.0) but still fallback

### Mixed Garbage + Intent (3/3 fallback)
```
fees???     → QUESTION, fees intent (1.0), fallback ✗
bca!!!      → QUESTION, BCA program detected, fallback ✗
admission???→ QUESTION, admission intent (1.0), fallback ✗
```
**Issue**: All have structured intent but fallback triggered

### Typos (4/4 fallback)
```
admisson    → QUESTION, corrected→admission, fallback ✗
feees       → QUESTION, corrected→fees, fallback ✗
plcement    → QUESTION, corrected→placement, fallback ✗
aims collge → QUESTION, no correction, fallback ✗
```
**Issue**: Corrections work but not re-evaluated

---

## Root Cause Summary

The chatbot's input handling has a **routing layer failure**:

1. **Input Handler** works correctly (GREETING/EXIT/NONSENSE/QUESTION)
2. **Structured Knowledge Layer** works correctly (detects fees, admission, courses)
3. **Intent Router** is broken (all scores = 0.0)
4. **Routing Decision** doesn't use structured intent scores

Result: 92.9% fallback rate despite correct intent detection at structured layer.

---

## Execution Log

```
Test Date: Apr 28, 2026
Test Script: test_input_handling.py
Total Queries: 14
Execution Time: ~2 seconds
Report Format: JSON + Markdown
```

See `test_input_handling_report.json` for detailed raw data.
