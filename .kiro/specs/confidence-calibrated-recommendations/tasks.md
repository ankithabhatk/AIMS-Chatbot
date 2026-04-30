# Implementation Plan: Confidence-Calibrated Recommendations

## Overview

This feature adds a **thin, surgical tone layer** to career counseling recommendations. The core principle is **separation of concerns**: tone is applied AFTER decision logic completes, not intertwined with it.

**Architecture Constraint**: This is a pure transformation layer — tone is injected as post-processing, not built into decision logic.

**Success Criteria**:
```
DONE WHEN:
✓ Tone varies across low/medium/high confidence
✓ Decision logic remains unchanged
✓ apply_confidence_tone is the ONLY place handling tone
✓ Integration tests still pass (100%)
✓ No duplicate phrasing or broken structure
```

## Tasks

### Phase 1: Core Tone Layer (3 tasks)

- [x] 1. Create ToneProfile data structure
  - Add `ToneProfile` dataclass to `backend/app/services/conversation_memory.py`
  - Fields: `prefix: str`, `judgment_phrase: str`, `confidence_strength: str`
  - Add `__post_init__` validation for `confidence_strength` (must be "exploratory", "balanced", or "decisive")
  - _Requirements: 2.4_

- [x] 2. Implement get_tone_profile() mapping function
  - Create `get_tone_profile(confidence: str) -> ToneProfile` function
  - Map "low" → exploratory tone (prefix: "It's okay to feel unsure — but here's one way to approach this.", judgment: "Consider")
  - Map "medium" → balanced tone (prefix: "Based on what you've told me, here's a practical path:", judgment: "I'd recommend")
  - Map "high" → decisive tone (prefix: "Based on your clear goals, here's what I'd strongly suggest:", judgment: "I'd strongly recommend")
  - Default to "medium" for invalid/missing confidence
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 3. Implement apply_confidence_tone() transformation function
  - Create `apply_confidence_tone(base_recommendation: str, confidence: str, force: bool = False) -> str` function
  - Handle edge case: empty recommendation → return empty string
  - Handle edge case: force=True + low confidence → use soft decision tone (balanced prefix + "I'd recommend")
  - Implement `_inject_tone_prefix(recommendation: str, prefix: str) -> str` helper
    - Find opening patterns ("Based on what you've told me:", "Here's the honest path:", "Based on your")
    - Inject prefix before opening line with blank line for readability
    - If no pattern found, prepend prefix to start
  - Implement `_adjust_judgment_strength(recommendation: str, judgment_phrase: str) -> str` helper
    - Replace "My recommendation" with judgment_phrase
    - Replace "I'd recommend" with judgment_phrase
    - Replace "I recommend" with judgment_phrase
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.3_

### Phase 2: Integration (1 task)

- [x] 4. Integrate tone layer into build_final_recommendation()
  - Modify `build_final_recommendation()` in `backend/app/services/conversation_memory.py`
  - Extract existing recommendation logic into `_build_base_recommendation(profile: UserProfile, query: str, force: bool) -> Optional[str]` helper
  - Call `apply_confidence_tone()` as final step before return
  - Pass `profile.confidence_level` and `force` parameter to tone layer
  - Preserve all existing decision logic (no changes to recommendation building)
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 4.1, 4.2, 4.4_

### Phase 3: Validation (4 tasks)

- [x]* 5. Write unit tests for tone profiles
  - Test `ToneProfile` creation with valid confidence_strength values
  - Test `ToneProfile` validation rejects invalid confidence_strength
  - Test `get_tone_profile()` returns correct profiles for "low", "medium", "high"
  - Test `get_tone_profile()` defaults to "medium" for invalid/None confidence
  - _Requirements: 2.4_

- [x]* 6. Write unit tests for tone transformation
  - Test `apply_confidence_tone()` with empty recommendation returns empty string
  - Test low confidence applies exploratory prefix and "Consider" judgment
  - Test medium confidence applies balanced prefix and "I'd recommend" judgment
  - Test high confidence applies decisive prefix and "I'd strongly recommend" judgment
  - Test force=True + low confidence applies soft decision tone
  - Test `_inject_tone_prefix()` finds and replaces opening patterns
  - Test `_inject_tone_prefix()` prepends when no pattern found
  - Test `_adjust_judgment_strength()` replaces all judgment phrases
  - _Requirements: 3.2, 3.3, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 7. Write property-based tests for correctness properties
  - **Property 1: ToneProfile Completeness**
    - Generator: Valid confidence levels ("low", "medium", "high")
    - Assert all fields (prefix, judgment_phrase, confidence_strength) are non-empty
    - Tag: `Feature: confidence-calibrated-recommendations, Property 1: ToneProfile Completeness`
    - **Validates: Requirements 2.4**
  - **Property 2: Prefix Injection Preservation**
    - Generator: Random recommendation strings + all tone profiles
    - Assert output contains the ToneProfile's prefix phrase
    - Tag: `Feature: confidence-calibrated-recommendations, Property 2: Prefix Injection Preservation`
    - **Validates: Requirements 3.2**
  - **Property 3: Judgment Phrase Replacement**
    - Generator: Recommendations with judgment phrases + all tone profiles
    - Assert original phrases replaced with tone-appropriate phrases
    - Tag: `Feature: confidence-calibrated-recommendations, Property 3: Judgment Phrase Replacement`
    - **Validates: Requirements 3.3**
  - Use `hypothesis` library with minimum 100 iterations per property
  - _Requirements: 3.2, 3.3, 2.4_

- [ ]* 8. Write integration tests for end-to-end tone application
  - Test low confidence user gets exploratory tone in final recommendation
  - Test medium confidence user gets balanced tone in final recommendation
  - Test high confidence user gets decisive tone in final recommendation
  - Test force=True + low confidence gets soft decision tone
  - Test recommendation structure preservation (bullet points, reasoning unchanged)
  - Test missing confidence defaults to medium tone
  - Test existing integration tests still pass (regression check)
  - _Requirements: 5.1, 5.2, 5.3, 4.3, 6.2, 6.3, 6.4_

## Notes

- **Tasks marked with `*` are optional** and can be skipped for faster MVP
- **Separation principle**: Only `apply_confidence_tone()` handles tone — no changes to decision logic, routing, or memory
- **Pure function architecture**: Tone layer is stateless with no side effects
- **Surgical modification**: Only opening phrases and judgment strength are modified, not content structure
- **Edge case handling**: Force + low confidence uses "soft decision" tone (gentle acknowledgment + clear recommendation)
- Each task references specific requirements for traceability
