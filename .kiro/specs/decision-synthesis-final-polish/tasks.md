# Implementation Plan: Decision Synthesis Final Polish

## Overview

This implementation completes the Decision Synthesis Layer by implementing three critical production-readiness improvements:

1. **System-Level Counselor Lock**: Ensures deterministic routing across all layers
2. **Progressive Response Builder**: Eliminates generic mid-flow responses
3. **Human Judgment Layer**: Adds micro-judgment phrases to recommendations

**Target**: Production-ready system with 10/10 GOOD rating on harsh audit.

---

## 🧩 PHASE 1 — Core Infrastructure (Must be deterministic)

- [x] 1.1 Create Counselor Lock Module
  - Create file: `backend/app/services/counselor_lock.py`
  - Implement `should_lock_counselor(profile) -> bool` function
  - Logic: Return True if profile has interests OR constraints OR goals
  - Add logging for debugging routing decisions
  - _Requirements: 1.1, 1.3_

- [x] 1.2 Apply Lock Across Routing
  - Modify `backend/app/services/structured_knowledge.py`:
    - Add `session_id` parameter to `get_structured_response()`
    - Check counselor lock before returning structured responses
    - Return None if lock is active
  - Modify `backend/app/services/structured_knowledge.py`:
    - Update `get_multi_intent_response()` to use centralized lock function
  - Modify `backend/app/api/chat.py`:
    - Pass `session_id` to `get_structured_response()` call
  - Rule: If `should_lock_counselor(profile)` returns True, return None
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

---

## 🧠 PHASE 2 — Kill Generic Responses

- [x] 2.1 Build Progressive Response Function
  - Create function in `backend/app/services/counselor_handler.py`:
    - `build_progressive_response(profile: UserProfile, query: str) -> str`
  - Logic:
    - If profile has interests: Acknowledge them ("You've mentioned: {interests}")
    - If profile has constraints: Acknowledge them ("You're dealing with: {constraints}")
    - If profile has goals: Acknowledge them ("You want: {goals}")
    - Always add forward step: "So let's narrow this down..."
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_

- [x] 2.2 Replace Generic Responses in _handle_general_exploration
  - Modify `_handle_general_exploration()` in `backend/app/services/counselor_handler.py`
  - Remove: Generic "I'm here to help you find the right path" response
  - Add: Check if profile exists (interests OR constraints OR goals)
  - If profile exists: Call `build_progressive_response(profile, query)`
  - If no profile: Use generic response (only for first turn)
  - _Requirements: 2.5, 2.6_

---

## 🧬 PHASE 3 — Decision Humanization

- [x] 3.1 Add Human Judgment Layer to build_final_recommendation
  - Modify `build_final_recommendation()` in `backend/app/services/conversation_memory.py`
  - Add human judgment phrase before final recommendation:
    - "If I were in your position, I'd start with BCA and keep MCA open."
  - Insert this phrase before the final recommendation section
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 3.2 Add Risk Framing to Recommendations
  - Modify `build_final_recommendation()` in `backend/app/services/conversation_memory.py`
  - Add risk awareness phrase:
    - "The risk with rushing into a decision is you might lock yourself into something that doesn't fit long-term."
  - Add this in the trade-off section
  - _Requirements: 3.4_

- [x] 3.3 Implement Decision Override Logic (CRITICAL)
  - **Problem**: Currently, if confidence_level = "low", system stays exploratory even when user asks "what should I do?"
  - **Required Behavior**: IF user explicitly asks for decision → MUST provide recommendation (even with low confidence)
  - Create function in `backend/app/services/counselor_handler.py`:
    - `should_force_decision(query: str) -> bool`
    - Decision signals: ["what should i do", "what do you recommend", "suggest", "final advice", "what should i choose"]
    - Return True if any signal detected in query.lower()
  - Modify decision routing logic:
    - Check: `if is_decision_query(query) or should_force_decision(query):`
    - Call: `build_final_recommendation(profile, query, force=True)`
  - Modify `build_final_recommendation()` signature:
    - Add parameter: `force: bool = False`
    - Logic: `if profile.confidence_level == "low" and not force: return build_exploratory_response(profile)`
    - If force=True: Provide recommendation with gentle but decisive tone
  - Expected output for low confidence + force:
    - Acknowledge uncertainty: "It's okay to feel unsure — but based on what you've told me..."
    - Include human judgment phrases: "If I were in your position..."
    - Provide clear recommendation despite uncertainty
  - _Requirements: 4.3, 4.4, 4.5, 5.1, 5.2, 5.3_

---

## 🤔 PHASE 4 — Uncertainty Handling

- [x] 4.1 Detect Low Confidence Signals
  - Verify `extract_user_profile()` in `backend/app/services/conversation_memory.py` extracts ambiguity signals
  - Signals: "idk", "maybe", "not sure", "confused", "don't know"
  - Sets `confidence_level = "low"` when detected
  - _Requirements: 4.1_

- [x] 4.2 Add Tone Adjustment Function
  - Create function in `backend/app/services/counselor_handler.py`:
    - `adjust_tone(profile: UserProfile) -> str`
  - Logic:
    - If `profile.confidence_level == "low"`: return "supportive"
    - Else: return "normal"
  - _Requirements: 4.2_

- [x] 4.3 Adjust Behavior for Low Confidence
  - Modify counselor response generation to check confidence level
  - If low confidence:
    - Avoid strong recommendations
    - Add reassuring language: "It's okay to be unsure — we can figure this step by step."
    - Ask more clarifying questions
  - _Requirements: 4.3, 4.4, 4.5_

---

## 🧪 PHASE 5 — Stability + Property Tests

- [x] 5.1 Write property test for counselor lock activation
  - **Property 1: Counselor Lock Activation**
  - **Validates: Requirements 1.1, 1.3**
  - Test: For any profile with signals (interests OR constraints OR goals), counselor lock is active
  - File: `tests/property/test_decision_synthesis_properties.py`

- [x] 5.2 Write property test for counselor lock respect
  - **Property 2-3: Structured/Multi-Intent Handler Respects Lock**
  - **Validates: Requirements 1.1, 1.2, 1.3**
  - Test: For any session with active lock, handlers return None
  - File: `tests/property/test_decision_synthesis_properties.py`

- [x] 5.3 Write property test for profile acknowledgment
  - **Property 4: Profile Acknowledgment in Responses**
  - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
  - Test: For any profile with signals, response references those signals
  - File: `tests/property/test_decision_synthesis_properties.py`

- [x] 5.4 Write property test for no generic responses
  - **Property 5: No Generic Responses with Profile**
  - **Validates: Requirements 2.5**
  - Test: For any non-empty profile, no generic greeting phrases
  - File: `tests/property/test_decision_synthesis_properties.py`

- [x] 5.5 Write property test for human judgment phrases
  - **Property 6: Human Judgment Phrases Present**
  - **Validates: Requirements 3.1, 3.2, 3.3**
  - Test: Final recommendations contain human judgment phrases
  - File: `tests/property/test_decision_synthesis_properties.py`

- [x] 5.6 Write property test for session memory round-trip
  - **Property 12: Session Memory Round-Trip**
  - **Validates: Requirements 6.1**
  - Test: Storing then retrieving profile produces equivalent profile
  - File: `tests/property/test_decision_synthesis_properties.py`

- [x] 5.7 Write property test for counselor lock idempotence
  - **Property 13: Counselor Lock Idempotence**
  - **Validates: Requirements 7.1, 7.4**
  - Test: Calling `should_lock_counselor()` multiple times returns same result
  - File: `tests/property/test_decision_synthesis_properties.py`

- [x] 5.8 Write property test for profile accumulation monotonicity
  - **Property 15: Profile Accumulation Monotonicity**
  - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
  - Test: Adding signals never removes existing signals
  - File: `tests/property/test_decision_synthesis_properties.py`

---

## 🔥 FINAL TEST (MANDATORY)

- [x] 6. Run 5-turn conflict conversation test
  - Test conversation:
    - User: "idk"
    - User: "I like coding maybe"
    - User: "I'm not good at studies"
    - User: "I want money fast"
    - User: "what should I do?"
  - Expected output:
    - Calm tone (no aggressive recommendations)
    - Acknowledges uncertainty
    - Suggests flexible path
    - No generic reset
    - No routing bugs (stays in counselor mode)
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  - **STATUS**: ✅ PASSED - Decision override logic working correctly

---

## 🎯 What "DONE" Actually Means

You are **NOT** done when:
- ✗ Code compiles
- ✗ Tests pass

You **ARE** done when:
- ✓ The system feels like a thinking human advisor under uncertainty
- ✓ No mid-conversation routing failures
- ✓ No generic "I'm here to help" responses after turn 1
- ✓ Recommendations include human judgment phrases
- ✓ 5-turn conflict test passes all checks
- ✓ System achieves 10/10 GOOD rating on harsh audit

**Current state**: 85% logic, 15% human feel  
**Target state**: 70% logic, 30% human feel → this is what users trust

---

## Notes

- Tasks marked with `*` are optional property-based tests (can be skipped for faster MVP)
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness guarantees
- Unit tests validate specific examples and edge cases
