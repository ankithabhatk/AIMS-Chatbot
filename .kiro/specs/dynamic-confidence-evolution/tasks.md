# Implementation Plan: Dynamic Confidence Evolution

## Overview

This feature transforms confidence handling from **static per-turn extraction** to **dynamic stateful evolution** across conversation turns. The core principle is **accumulation, not overwriting** — confidence builds gradually based on signals across multiple turns.

**Architecture Constraint**: This is a separate engine layer that sits between profile extraction and decision engine. It maintains confidence as a continuous score (0.0-1.0) that evolves monotonically.

**Success Criteria**:
```
DONE WHEN:
✓ Confidence evolves gradually across turns (not jumps)
✓ Scores are monotonic (generally increase, not bounce)
✓ Ambiguity slows growth but doesn't reset confidence
✓ Decision override still works regardless of score
✓ Clean separation from decision/tone logic
✓ Backward compatibility with tone layer
```

## 🔒 Critical Constraints (MANDATORY)

These constraints prevent long-term instability and must be enforced strictly:

### 1. Single Source of Truth
**ONLY `update_confidence_score(prev_score, signals)` can modify the confidence score.**

- ❌ No other function modifies score
- ❌ No inline adjustments anywhere else
- ❌ No direct score mutations in profile updates

**Why**: Without this, you get hidden score mutations and impossible debugging.

### 2. Deterministic Behavior
**Confidence evolution MUST be deterministic and stateless given `(previous_score, signals)`.**

- Same inputs + same history → same confidence score
- No randomness, no timestamps affecting score
- Pure function: `f(prev_score, signals) → new_score`

**Why**: Without this, tone feels inconsistent and users lose trust subconsciously.

### 3. Bounded Delta
**Confidence score change per turn SHALL be bounded: `delta ∈ [-0.3, +0.3]`**

- Maximum increase per turn: +0.3
- Maximum decrease per turn: -0.3
- Prevents sudden jumps (0.2 → 0.8 in one turn)

**Why**: Without this, you get tone whiplash and unstable UX.

## Tasks

### Phase 1: Core Confidence Engine (4 tasks)

- [x] 1. Create ConfidenceScore data structure
  - Add `ConfidenceScore` class to `backend/app/services/confidence_engine.py`
  - Fields: `score: float` (0.0-1.0), `signals_collected: int`, `last_updated: datetime`
  - Methods: `increment(amount: float)`, `decrement(amount: float)`, `cap()`
  - Validation: Score stays within 0.0-1.0 bounds
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Implement signal extraction functions
  - Create `extract_ambiguity_signals(query: str) -> List[Dict]` function
    - Detect "idk", "maybe", "not sure", "confused", "unsure", "wondering"
    - Assign weights: strong ambiguity (-0.1), weak ambiguity (-0.05)
  - Create `extract_clarity_signals(query: str) -> List[Dict]` function
    - Detect "I want", "I decided", "I like", "I need", "I'm sure"
    - Assign weights: strong clarity (+0.15), weak clarity (+0.08)
  - Create `extract_consistency_signals(query: str, previous_queries: List[str]) -> List[Dict]` function
    - Compare interests/goals across turns
    - Assign weights: consistent (+0.1), inconsistent (-0.05)
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. Implement score evolution algorithm (CORE FUNCTION - CRITICAL)
  - Create `update_confidence_score(current_score: float, signals: List[Dict]) -> float` function
  - **CONSTRAINT 1**: This is the ONLY function that modifies confidence score
  - **CONSTRAINT 2**: Must be deterministic (same inputs → same output, no randomness)
  - **CONSTRAINT 3**: Bounded delta per turn: `delta ∈ [-0.3, +0.3]`
  - Implementation requirements:
    - Calculate raw signal impact: `sum(signal_weights)`
    - Clamp delta to bounds: `delta = max(-0.3, min(0.3, raw_impact))`
    - Apply smoothing/momentum to prevent jumps
    - Apply monotonic growth: `new_score = max(current_score, current_score + delta)` (for clarity signals)
    - Cap final score at 0.0-1.0 bounds
  - **TEST IN ISOLATION FIRST** before any integration
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 5.1, 5.2, 5.3, 5.4_

- [x] 4. Implement category mapping
  - Create `map_score_to_category(score: float) -> str` function
  - 0.0-0.3 → "low" (exploratory tone)
  - 0.3-0.7 → "medium" (balanced tone)
  - 0.7-1.0 → "high" (decisive tone)
  - Handle boundary cases consistently (e.g., 0.3 → "medium")
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 4.1. Implement debug utility (CRITICAL FOR TUNING)
  - Create `get_confidence_debug(profile: UserProfile) -> Dict` function
  - Returns: `{"score": float, "delta": float, "signals": List, "category": str, "history": List}`
  - Shows last N score changes with signals that caused them
  - **Why**: Without this, tuning becomes guesswork and debugging becomes painful
  - _Requirements: 14.1, 14.2, 14.3_

### Phase 2: Integration Layer (3 tasks)

- [x] 5. Integrate confidence engine into UserProfile
  - Modify `UserProfile` in `backend/app/services/conversation_memory.py`
  - Replace `confidence_level: str` with `confidence_score: float`
  - Add `confidence_signals: List[Dict]` to track signal history
  - Add `update_confidence(query: str)` method that calls confidence engine
  - Maintain backward compatibility: add `confidence_category` property that maps score → category
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6. Update profile extraction to use confidence engine
  - Modify `extract_user_profile()` in `backend/app/services/conversation_memory.py`
  - Remove direct `confidence_level` extraction
  - Instead: extract signals and pass to confidence engine
  - Update `update_profile()` to call confidence engine with new signals
  - Preserve existing ambiguity signal detection for backward compatibility
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 7. Update tone layer integration point
  - Modify `build_final_recommendation()` in `backend/app/services/conversation_memory.py`
  - Change from `profile.confidence_level` to `profile.confidence_category`
  - Ensure tone layer receives same categorical values (low/medium/high)
  - No changes to `apply_confidence_tone()` function (separation maintained)
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

### Phase 3: Evolution Scenarios & Edge Cases (3 tasks)

- [ ] 8. Implement example evolution scenarios
  - Create test case: "idk what to do" → score ≈ 0.2
  - Create test case: "maybe coding" → score ≈ 0.35
  - Create test case: "I like coding and want good salary" → score ≈ 0.6
  - Create test case: "what should I do?" → score ≈ 0.75
  - Verify monotonic growth across sequence
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 9. Handle edge cases and error conditions
  - Empty query → maintain current score
  - Conflicting signals (clarity + ambiguity) → weighted net effect
  - Score would exceed 1.0 → cap at 1.0
  - Score would go below 0.0 → cap at 0.0
  - Malformed query → graceful degradation
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 10. Implement persistence and state management
  - Store confidence score in UserProfile serialization
  - Persist across conversation sessions via memory store
  - Handle new users (initialize score = 0.0)
  - Provide reset method for testing/debugging
  - Ensure thread safety for concurrent conversations
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

### Phase 4: Validation (4 tasks)

- [ ]* 11. Write unit tests for signal extraction
  - Test `extract_ambiguity_signals()` detects all ambiguity patterns
  - Test `extract_clarity_signals()` detects all clarity patterns
  - Test `extract_consistency_signals()` compares across turns
  - Test signal weighting (strong vs weak signals)
  - Test edge cases: empty query, malformed query
  - _Requirements: 13.1_

- [ ]* 12. Write unit tests for score evolution
  - Test `update_confidence_score()` with various signal combinations
  - Test monotonic growth property (score never decreases with clarity)
  - Test ambiguity slows growth but doesn't decrease score
  - Test consistency accelerates growth
  - Test bounds enforcement (0.0-1.0)
  - _Requirements: 13.1_

- [ ]* 13. Write property-based tests
  - **Property 1: Monotonic Growth**
    - Generator: Sequence of queries with mixed signals
    - Assert: Confidence score never decreases when clarity signals present
    - Tag: `Feature: dynamic-confidence-evolution, Property 1: Monotonic Growth`
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
  - **Property 2: Bounds Enforcement**
    - Generator: Random signal combinations
    - Assert: Score always within 0.0-1.0 range
    - Tag: `Feature: dynamic-confidence-evolution, Property 2: Bounds Enforcement`
    - **Validates: Requirements 1.4, 11.3, 11.4**
  - **Property 3: Category Mapping Consistency**
    - Generator: Random scores 0.0-1.0
    - Assert: Mapping follows 0.0-0.3→low, 0.3-0.7→medium, 0.7-1.0→high
    - Tag: `Feature: dynamic-confidence-evolution, Property 3: Category Mapping Consistency`
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
  - Use `hypothesis` library with minimum 100 iterations per property
  - _Requirements: 13.2_

- [ ]* 14. Write integration tests
  - Test end-to-end: query → signals → score update → category → tone
  - Test example evolution scenarios from requirements
  - Test backward compatibility with tone layer
  - Test decision override still works
  - Test existing integration tests still pass (regression check)
  - _Requirements: 13.3, 13.4_

## Notes

- **Tasks marked with `*` are optional** and can be skipped for faster MVP
- **Separation principle**: Confidence engine is separate from decision/tone logic
- **Monotonic growth**: Confidence generally increases, not bounces
- **Accumulation, not overwriting**: Signals accumulate across turns
- **Backward compatibility**: Tone layer receives same categories (low/medium/high)
- **Edge case handling**: Ambiguity slows but doesn't reset confidence
- Each task references specific requirements for traceability

## Example Evolution Sequence

```
Turn 1: "idk what to do"
  → Ambiguity signal (-0.1)
  → Score: 0.2 (low)

Turn 2: "maybe coding"
  → Weak ambiguity (-0.05) + weak clarity (+0.08)
  → Net: +0.03
  → Score: 0.35 (low/medium boundary)

Turn 3: "I like coding and want good salary"
  → Strong clarity (+0.15) + consistency (+0.1)
  → Net: +0.25
  → Score: 0.6 (medium)

Turn 4: "what should I do?"
  → Decision query signal (+0.15)
  → Score: 0.75 (high)
  → Tone: decisive ("Based on your clear goals...")
```

## Key Design Decisions

1. **Continuous score (0.0-1.0)** instead of categorical labels
2. **Weighted signals** with configurable strengths
3. **Monotonic growth** with minimum threshold
4. **Diminishing returns** for repeated signals
5. **Separate engine** with clean interfaces
6. **Backward compatibility** via category mapping
7. **Persistence** across conversation sessions

## Migration Strategy

1. Deploy confidence engine alongside existing system
2. Run in parallel: extract both static confidence and dynamic score
3. Compare outputs for consistency
4. Switch tone layer to use dynamic categories
5. Remove static confidence extraction
6. Monitor for regressions