# Task 4.3 Completion Summary: Adjust Behavior for Low Confidence

## Task Overview

**Task**: 4.3 Adjust Behavior for Low Confidence  
**Spec**: decision-synthesis-final-polish  
**Requirements**: 4.3, 4.4, 4.5

## Implementation Details

### Changes Made

#### 1. Modified `build_progressive_response()` in `backend/app/services/counselor_handler.py`

**Purpose**: Adjust counselor responses based on user confidence level

**Key Changes**:
- Added tone detection using `adjust_tone(profile)` function
- Added reassuring language for low confidence users: "It's okay to be unsure — we can figure this out step by step. 💭"
- Changed heading from "So let's narrow this down" to "Let's explore this together" for low confidence
- Softened recommendations:
  - Low confidence: "could be a good option to consider" / "might be worth exploring"
  - Normal confidence: "makes sense" / "is better"
- Added more clarifying questions for low confidence users (3+ questions vs 1 question)
- Questions focus on helping user understand their priorities and concerns

**Example Low Confidence Response**:
```
It's okay to be unsure — we can figure this out step by step. 💭

You've mentioned: coding.
You want: quick job.

**Let's explore this together:**

For coding, you have 2 main paths:
• BCA (3 years) → Quick job entry
• BCA + MCA (5 years) → Higher salary

Since you want a job quickly, BCA (3 years) could be a good option to consider.

**To help you decide, let me ask:**
• How do you feel about studying for 3 years vs 5 years?
• What matters more to you right now — getting started quickly or building deeper skills?
• Is there anything else that's making you uncertain?
```

**Example Normal Confidence Response**:
```
You've mentioned: coding.
You want: quick job.

**So let's narrow this down:**

For coding, you have 2 main paths:
• BCA (3 years) → Quick job entry
• BCA + MCA (5 years) → Higher salary

Since you want a job quickly → BCA (3 years) makes sense

**What else would help me give you a clear recommendation?**
```

#### 2. Modified `build_final_recommendation()` in `backend/app/services/conversation_memory.py`

**Purpose**: Avoid strong recommendations when confidence is low

**Key Changes**:
- Added confidence level check at the beginning of the function
- Returns `None` when `profile.confidence_level == "low"`
- This prevents final recommendations from being generated for uncertain users
- Instead, the progressive response builder handles low confidence cases with more questions

**Rationale**: 
- Requirement 4.3: "THE Counselor_Handler SHALL NOT provide final recommendations when the user has high ambiguity signals"
- Requirement 4.4: "WHEN uncertainty is detected, THE Counselor_Handler SHALL ask clarifying questions before providing recommendations"

## Requirements Validation

### Requirement 4.3 ✓
**"THE Counselor_Handler SHALL NOT provide final recommendations when the user has high ambiguity signals"**

- `build_final_recommendation()` returns `None` when confidence is low
- Progressive response uses softened language ("could be", "might be") instead of strong recommendations ("makes sense", "is better")

### Requirement 4.4 ✓
**"WHEN uncertainty is detected, THE Counselor_Handler SHALL ask clarifying questions before providing recommendations"**

- Low confidence responses include 3+ clarifying questions
- Questions help user understand their priorities:
  - "How do you feel about studying for 3 years vs 5 years?"
  - "What matters more to you right now — getting started quickly or building deeper skills?"
  - "Is there anything else that's making you uncertain?"

### Requirement 4.5 ✓
**"THE Counselor_Handler SHALL use reassuring language like 'It's okay to be unsure' OR 'Let's explore this together'"**

- Added: "It's okay to be unsure — we can figure this out step by step. 💭"
- Changed heading to: "Let's explore this together:"
- Uses supportive, non-pressuring language throughout

## Test Results

### Unit Tests (10/10 passed)

Created `tests/unit/test_task_4_3_low_confidence.py`:

1. ✓ `test_adjust_tone_returns_supportive_for_low_confidence` - Verifies tone detection
2. ✓ `test_adjust_tone_returns_normal_for_medium_confidence` - Verifies normal tone
3. ✓ `test_adjust_tone_returns_normal_for_high_confidence` - Verifies high confidence handling
4. ✓ `test_build_final_recommendation_returns_none_for_low_confidence` - Verifies no strong recommendations
5. ✓ `test_build_final_recommendation_works_for_normal_confidence` - Verifies normal flow still works
6. ✓ `test_progressive_response_includes_reassuring_language_for_low_confidence` - Validates Req 4.5
7. ✓ `test_progressive_response_asks_more_questions_for_low_confidence` - Validates Req 4.4
8. ✓ `test_progressive_response_softens_recommendations_for_low_confidence` - Validates Req 4.3
9. ✓ `test_progressive_response_uses_exploratory_language_for_low_confidence` - Validates Req 4.5
10. ✓ `test_progressive_response_normal_for_high_confidence` - Verifies normal behavior unchanged

### Integration Tests (10/10 passed)

Existing uncertainty flow tests still pass:
- `test_uncertainty_stored_in_session_profile`
- `test_uncertainty_persists_across_turns`
- `test_multiple_uncertainty_signals_accumulate`
- `test_confidence_level_updates_to_low`
- `test_profile_retrieval_preserves_uncertainty`
- `test_uncertainty_with_interests_and_constraints`
- `test_profile_to_dict_includes_uncertainty`
- `test_profile_from_dict_restores_uncertainty`
- `test_clear_session_removes_uncertainty`
- `test_all_required_keywords_detected`

### Regression Tests (72/72 passed)

All existing unit tests pass:
- Human judgment tests (7/7)
- Risk framing tests (6/6)
- Progressive response tests (14/14)
- Uncertainty detection tests (25/25)
- Adjust tone tests (5/5)
- Progressive response integration tests (3/3)
- Task 4.3 tests (10/10)
- Other unit tests (2/2)

## Manual Testing

Created `tests/manual_test_task_4_3.py` to demonstrate behavior:

### Test 1: Low Confidence User
- Profile: coding interest, weak in math, wants high salary, confidence=low
- Result: Reassuring language, exploratory tone, 3+ questions, softened recommendations
- Final recommendation: Returns None (as expected)

### Test 2: Normal Confidence User
- Profile: coding interest, weak in math, wants high salary, confidence=medium
- Result: Normal guidance, clear recommendations, 1 question
- Final recommendation: Full recommendation provided (as expected)

### Test 3: Side-by-Side Comparison
- Verified key differences:
  - ✓ Reassuring language in low confidence: True
  - ✓ Exploratory language in low confidence: True
  - ✓ Softened recommendations in low confidence: True
  - ✓ Strong recommendations in normal confidence: True
  - ✓ More questions for low confidence: 3 vs 1

## Behavior Changes

### Before Task 4.3
- All users received the same tone regardless of confidence level
- Final recommendations were provided even for uncertain users
- Limited clarifying questions

### After Task 4.3
- **Low confidence users** (uncertain, confused, "idk"):
  - Get reassuring language: "It's okay to be unsure"
  - Get exploratory framing: "Let's explore this together"
  - Get softened recommendations: "could be", "might be"
  - Get 3+ clarifying questions to help them understand their priorities
  - Do NOT get final recommendations (returns None)
  
- **Normal/High confidence users**:
  - Get balanced guidance: "So let's narrow this down"
  - Get clear recommendations: "makes sense", "is better"
  - Get 1 clarifying question
  - Get final recommendations when ready

## Files Modified

1. `backend/app/services/counselor_handler.py`
   - Modified `build_progressive_response()` function
   - Added tone detection and conditional behavior

2. `backend/app/services/conversation_memory.py`
   - Modified `build_final_recommendation()` function
   - Added confidence level check to avoid strong recommendations

## Files Created

1. `tests/unit/test_task_4_3_low_confidence.py` - Unit tests for Task 4.3
2. `tests/manual_test_task_4_3.py` - Manual demonstration of behavior
3. `tests/TASK_4.3_COMPLETION_SUMMARY.md` - This summary document

## Files Fixed

1. `tests/unit/test_adjust_tone.py` - Added sys.path fix
2. `tests/unit/test_progressive_response.py` - Added sys.path fix
3. `tests/unit/test_progressive_response_integration.py` - Added sys.path fix

## Verification

✅ All requirements (4.3, 4.4, 4.5) validated  
✅ All unit tests pass (72/72)  
✅ All integration tests pass (10/10)  
✅ No regressions introduced  
✅ Manual testing confirms expected behavior  
✅ Code follows existing patterns and conventions  

## Next Steps

Task 4.3 is complete. The counselor handler now appropriately adjusts behavior for low confidence users by:
- Avoiding strong recommendations
- Adding reassuring language
- Asking more clarifying questions
- Using exploratory, supportive tone

The implementation is ready for integration testing with the full 5-turn conflict conversation test (Task 6 in the spec).
