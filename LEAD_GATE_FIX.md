# Lead-Gate Hijacking Fix

## Problem Identified

**Critical UX Bug**: System was hijacking information queries and forcing lead capture forms.

### Before Fix ❌
- User asks: "What are the BCA fees?"
- System responds: "Please provide your Name, Email, Phone..."
- **Result**: User is BLOCKED from getting information

### Root Cause
In `backend/app/api/chat.py`, the `_derive_status()` function was activating a "lead gate" after 2 queries:

```python
def _derive_status(session: Dict[str, Any], intent: str) -> str:
    if intent not in {"greeting", "exit"} and session["query_count"] >= 2 and not session["has_lead"]:
        session["gate_active"] = True  # ❌ This hijacks the flow
        return "lock"
    return "unlock"
```

When `gate_active = True`, the chat endpoint would:
1. Intercept ALL queries
2. Force lead capture flow
3. Block information retrieval
4. Return form request instead of answers

## Solution Applied

**Disabled the automatic lead-gate activation** in `_derive_status()`:

```python
def _derive_status(session: Dict[str, Any], intent: str) -> str:
    # DISABLED: Lead-gate was hijacking information queries
    # Users asking "fees", "scholarship", "hostel" should get ANSWERS, not forms
    # Lead capture should only trigger on explicit application intent
    return "unlock"
```

## After Fix ✅

### Test Results (4/4 Passed)

| Query | Status | Intent | Response Type |
|-------|--------|--------|---------------|
| "What are the BCA fees?" | unlock | factual | ✅ Fees information |
| "Tell me about scholarships" | unlock | fallback | ✅ Scholarship info |
| "What about hostel facilities?" | unlock | follow_up | ✅ Hostel details |
| "How do I apply?" | unlock | factual | ✅ Admission process |

### User Experience Now
- User asks: "What are the BCA fees?"
- System responds: "BBA / BCA / B.Com: Undergraduate programs follow BCU fee norms..."
- **Result**: User gets INFORMATION immediately ✅

## Impact

### Fixed
✅ Information queries return actual information  
✅ No forced form submissions  
✅ Users can ask multiple questions freely  
✅ Natural conversation flow restored  

### Preserved
✅ Lead capture infrastructure still exists (for future use)  
✅ Can be re-enabled with explicit application intent detection  
✅ All logging and tracking still functional  

## Future Lead Capture Strategy

Lead capture should ONLY trigger when user shows **explicit application intent**:

### Trigger Phrases (Future Implementation)
- "I want to apply"
- "I want to join"
- "Contact me"
- "I'm interested in admission"
- "How do I enroll?"

### Do NOT Trigger On
- "What are the fees?"
- "Tell me about scholarships"
- "What about hostel?"
- "How is placement?"
- Any information-seeking query

## Files Modified

- `backend/app/api/chat.py` - Disabled `_derive_status()` lead-gate logic
- `test_lead_gate_fix.py` - Created verification test (4/4 passing)

## Verification

Run the test:
```bash
python test_lead_gate_fix.py
```

Expected output:
```
✅ Lead-gate hijacking is FIXED!
Users now get INFORMATION for info queries, not forms.
```

## Commit Message

```
fix: Remove lead-gate hijacking of information queries

PROBLEM:
- System was forcing lead capture forms for information queries
- Users asking "fees", "scholarship", "hostel" got blocked
- Critical UX bug preventing natural conversation

SOLUTION:
- Disabled automatic lead-gate activation in _derive_status()
- Information queries now return actual information
- Lead capture infrastructure preserved for future use

IMPACT:
- 4/4 test cases now pass
- Users get answers, not forms
- Natural conversation flow restored

Files changed:
- backend/app/api/chat.py (disabled lead-gate logic)
- test_lead_gate_fix.py (verification test)
```

---

**Status**: ✅ FIXED  
**Verified**: 2026-04-28  
**Test Coverage**: 4/4 passing
