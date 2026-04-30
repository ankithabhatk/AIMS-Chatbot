# Design Document: Decision Synthesis Final Polish

## Overview

This design completes the Decision Synthesis Layer by implementing three critical production-readiness improvements:

1. **System-Level Counselor Lock**: Ensures deterministic routing across all layers (multi-intent, structured, boundary) so users stay in counselor mode once they have an active profile
2. **Progressive Response Builder**: Eliminates generic mid-flow responses by always building forward from accumulated user context
3. **Human Judgment Layer**: Adds micro-judgment phrases ("If I were in your position...") to make recommendations feel like they come from a human counselor

**Current Architecture**: The system has a 4-layer routing hierarchy:
- **Boundary Handler**: Filters out-of-scope queries (external exams, comparisons)
- **Multi-Intent Handler**: Combines multiple structured intents ("fees and hostel")
- **Counselor Handler**: Provides conversational guidance for exploratory queries
- **Structured Knowledge Handler**: Returns deterministic facts (fees, courses, admission)
- **RAG Handler**: Fallback for unstructured queries

**Problem**: Counselor lock is only partially implemented in multi-intent handler. Structured handler and boundary handler don't check for active counselor sessions, causing mid-conversation routing failures.

**Solution**: Create central `should_lock_counselor(profile)` function and apply it consistently across all routing layers.

## Architecture

### High-Level System Flow

```
User Query
    ↓
[Extract Profile Signals] ← session_id
    ↓
[Check Counselor Lock] ← should_lock_counselor(profile)
    ↓
    ├─ LOCKED → [Counselor Handler]
    │              ↓
    │          [Progressive Response Builder]
    │              ↓
    │          [Human Judgment Layer] (if decision query)
    │
    └─ UNLOCKED → [Standard Routing]
                      ↓
                  [Boundary → Multi-Intent → Structured → RAG]
```

### Key Design Decisions

1. **Centralized Lock Function**: Single source of truth for counselor lock logic prevents inconsistencies
2. **Profile-First Routing**: Check counselor lock BEFORE any other routing logic
3. **Progressive Context Building**: Never reset to generic responses when profile exists
4. **Tone Adaptation**: Adjust language based on confidence level (low → supportive, high → decisive)

## Components and Interfaces

### Component 1: Counselor Lock Module

**Location**: `backend/app/services/counselor_lock.py` (new file)

**Purpose**: Centralized counselor lock logic used by all routing layers

**Interface**:
```python
def should_lock_counselor(profile: UserProfile) -> bool:
    """
    Determine if user should be locked in counselor mode.
    
    Returns True if:
    - User has interests (exploring career options)
    - User has constraints (weak in X, not good at Y)
    - User has goals (want high salary, quick job)
    - User has ambiguity signals (confused, not sure)
    
    Args:
        profile: UserProfile with accumulated signals
        
    Returns:
        bool: True if user should stay in counselor mode
    """
```

**Implementation Strategy**:
- Extract existing logic from `should_force_counselor()` in conversation_memory.py
- Make it more robust by checking ANY signal presence (not just constraints)
- Add logging for debugging routing decisions

### Component 2: Progressive Response Builder

**Location**: `backend/app/services/counselor_handler.py` (modify existing)

**Purpose**: Build responses that always reference accumulated context

**Interface**:
```python
def build_progressive_response(profile: UserProfile, query: str) -> str:
    """
    Build response that builds forward from accumulated profile.
    
    NEVER returns generic greetings when profile exists.
    ALWAYS summarizes known signals.
    ALWAYS adds one step forward.
    
    Args:
        profile: UserProfile with accumulated signals
        query: Current user query
        
    Returns:
        str: Progressive response building on known context
    """
```

**Tone Levels**:
- **Low confidence** (uncertain user): Slower, more questions, reassuring
- **Medium confidence**: Balanced, structured
- **High confidence**: Decisive, action-oriented

### Component 3: Human Judgment Layer

**Location**: `backend/app/services/conversation_memory.py` (modify existing `build_final_recommendation`)

**Purpose**: Add human-feeling micro-judgment phrases to recommendations

**Interface**:
```python
def build_final_recommendation(profile: UserProfile, query: str) -> Optional[str]:
    """
    Build final recommendation with human judgment tone.
    
    Adds 3 elements:
    1. Personal stance: "If I were in your position..."
    2. Trade-off framing: "This path keeps both options open..."
    3. Risk awareness: "The risk is..."
    
    Args:
        profile: UserProfile with interests, constraints, goals
        query: Decision query ("what should I do")
        
    Returns:
        Optional[str]: Human-feeling recommendation or None if insufficient data
    """
```

**Micro-Judgment Phrases**:
- "If I were in your position..."
- "Here's the honest path..."
- "In my experience..."
- "The risk is..."
- "This keeps both options open..."
- "I know this is tough, but..."

### Component 4: Uncertainty Handler

**Location**: `backend/app/services/counselor_handler.py` (modify existing)

**Purpose**: Detect uncertainty and adjust tone appropriately

**Interface**:
```python
def detect_uncertainty(query: str, profile: UserProfile) -> bool:
    """
    Detect if user is uncertain about their choices.
    
    Signals: "idk", "maybe", "not sure", "confused"
    
    Args:
        query: Current user query
        profile: UserProfile (may contain ambiguity_signals)
        
    Returns:
        bool: True if uncertainty detected
    """

def get_uncertainty_adjusted_response(profile: UserProfile, query: str) -> str:
    """
    Generate supportive response for uncertain users.
    
    Behavior:
    - Reduce decisiveness
    - Ask guiding questions
    - Avoid hard recommendations
    - Use reassuring language
    
    Args:
        profile: UserProfile with ambiguity signals
        query: Current user query
        
    Returns:
        str: Supportive, slower-paced response
    """
```

### Component 5: Decision Override Logic

**Location**: `backend/app/services/counselor_handler.py` (modify existing)

**Purpose**: Ensure explicit decision queries override uncertainty mode

**Critical Design Rule**: When a user explicitly asks for a decision, the system MUST provide a recommendation even if confidence_level is "low". This prevents the system from staying in exploratory mode indefinitely.

**Decision Override Rule**:
```
IF user explicitly asks for decision:
    Decision Engine > Uncertainty Handler
ELSE:
    Uncertainty Handler may delay decision
```

**Interface**:
```python
def should_force_decision(query: str) -> bool:
    """
    Detect if user is explicitly requesting a decision.
    
    Decision signals: "what should i do", "what do you recommend", 
                     "suggest", "final advice", "what should i choose"
    
    Args:
        query: Current user query
        
    Returns:
        bool: True if explicit decision request detected
    """

def build_final_recommendation(profile: UserProfile, query: str, force: bool = False) -> Optional[str]:
    """
    Build final recommendation with human judgment tone.
    
    CRITICAL: If force=True, MUST provide recommendation even with low confidence.
    
    Args:
        profile: UserProfile with interests, constraints, goals
        query: Decision query
        force: If True, override uncertainty handling
        
    Returns:
        Optional[str]: Human-feeling recommendation or None if insufficient data
    """
```

**Behavior**:
- **Without force**: If `confidence_level == "low"`, return exploratory response
- **With force**: Provide recommendation with gentle but decisive tone, acknowledging uncertainty but still giving guidance

**Example Output** (force=True, low confidence):
```
It's okay to feel unsure — but based on what you've told me, here's how I'd approach this.

If I were in your position:
• You like coding
• You're not strong in studies  
• You want money quickly

👉 The practical path is: Start with BCA → focus on job-ready skills → aim for placements early

**Why:**
• Faster entry into earning
• Less academic pressure compared to MCA
• You can still grow salary with experience

**Trade-off:**
• Lower starting salary vs MCA path
• But faster income, which matches your priority

👉 My recommendation: Go for BCA with a strong focus on practical skills and placements.
```

## Data Models

### UserProfile (existing, no changes needed)

```python
@dataclass
class UserProfile:
    interests: Set[str]           # coding, business, management, etc.
    constraints: Set[str]          # weak_in_math, not_good_at_studies, etc.
    goals: Set[str]                # high_salary, quick_job, etc.
    education_level: Optional[str] # 12th, bca, graduate, etc.
    ambiguity_signals: Set[str]    # uncertain, confused, etc.
    previous_intents: List[str]    # Last 5 intents
    confidence_level: str          # low, medium, high
```

### CounselorLockResult (new)

```python
@dataclass
class CounselorLockResult:
    """Result of counselor lock check."""
    locked: bool
    reason: str  # For debugging: "has_interests", "has_constraints", etc.
    profile_summary: str  # Human-readable summary of profile
```

## Integration Points

### Integration 1: Multi-Intent Handler

**File**: `backend/app/services/structured_knowledge.py`

**Current Code**:
```python
def get_multi_intent_response(query: str, session_id: Optional[str] = None) -> dict:
    # COUNSELOR LOCK: If user has active counselor profile, don't hijack
    if session_id:
        from app.services.conversation_memory import get_memory_store
        memory = get_memory_store()
        profile = memory.get_profile(session_id)
        
        # If user has interests/constraints/goals, they're in counselor mode
        if profile.interests or profile.constraints or profile.goals:
            logger.info(f"[multi-intent] Skipping - user in active counselor session")
            return None
```

**New Code**:
```python
def get_multi_intent_response(query: str, session_id: Optional[str] = None) -> dict:
    # COUNSELOR LOCK: Check centralized lock function
    if session_id:
        from app.services.counselor_lock import should_lock_counselor
        from app.services.conversation_memory import get_memory_store
        
        memory = get_memory_store()
        profile = memory.get_profile(session_id)
        
        if should_lock_counselor(profile):
            logger.info(f"[multi-intent] Counselor lock active - skipping")
            return None
```

### Integration 2: Structured Knowledge Handler

**File**: `backend/app/services/structured_knowledge.py`

**Current Code**:
```python
def get_structured_response(query: str) -> dict:
    # No counselor lock check - THIS IS THE BUG
    intent, confidence = is_structured_intent(query)
    if confidence < 0.8:
        return None
    # ... return structured response
```

**New Code**:
```python
def get_structured_response(query: str, session_id: Optional[str] = None) -> dict:
    """Get structured response for known intents.
    
    CRITICAL: Check counselor lock FIRST to prevent mid-conversation hijacking.
    """
    # COUNSELOR LOCK: Check before returning structured response
    if session_id:
        from app.services.counselor_lock import should_lock_counselor
        from app.services.conversation_memory import get_memory_store
        
        memory = get_memory_store()
        profile = memory.get_profile(session_id)
        
        if should_lock_counselor(profile):
            logger.info(f"[structured] Counselor lock active - skipping")
            return None
    
    intent, confidence = is_structured_intent(query)
    if confidence < 0.8:
        return None
    # ... return structured response
```

### Integration 3: Chat Routing Layer

**File**: `backend/app/api/chat.py`

**Current Code**:
```python
# CHECK: Single-intent structured knowledge override
structured_result = get_structured_response(query)
if structured_result:
    # ... return structured response
```

**New Code**:
```python
# CHECK: Single-intent structured knowledge override
# IMPORTANT: Pass session_id for counselor lock check
structured_result = get_structured_response(query, session_id=session_id)
if structured_result:
    # ... return structured response
```

### Integration 4: Counselor Handler

**File**: `backend/app/services/counselor_handler.py`

**Current Code** (in `_handle_general_exploration`):
```python
def _handle_general_exploration(query: str, profile: UserProfile, memory_context: str = "") -> Dict:
    # Generic response - THIS IS THE BUG
    answer = (
        "I'm here to help you find the right path! 🎓\n\n"
        "**Let's start with a few questions:**\n\n"
        # ... generic questions
    )
```

**New Code**:
```python
def _handle_general_exploration(query: str, profile: UserProfile, memory_context: str = "") -> Dict:
    # CRITICAL: If profile exists, ALWAYS build forward - never reset to generic
    if profile.interests or profile.constraints or profile.goals:
        return {
            "answer": build_progressive_response(profile, query),
            "intent": "counselor_progressive",
            "confidence": 1.0,
            "mode": "counselor",
            "sources": [{"title": "Career Guidance", "url": "https://www.theaims.ac.in"}],
        }
    
    # Only use generic if NO profile exists
    answer = (
        "I'm here to help you find the right path! 🎓\n\n"
        # ... generic questions
    )
```

## Error Handling

### Error Scenario 1: Profile Retrieval Failure

**Situation**: Session ID provided but profile cannot be retrieved

**Handling**:
```python
try:
    profile = memory.get_profile(session_id)
except Exception as e:
    logger.error(f"Profile retrieval failed: {e}")
    # Fallback: Create empty profile (no lock)
    profile = UserProfile()
```

### Error Scenario 2: Counselor Lock Check Failure

**Situation**: Exception in `should_lock_counselor()` function

**Handling**:
```python
try:
    locked = should_lock_counselor(profile)
except Exception as e:
    logger.error(f"Counselor lock check failed: {e}")
    # Fallback: No lock (allow normal routing)
    locked = False
```

### Error Scenario 3: Progressive Response Builder Failure

**Situation**: Exception in `build_progressive_response()`

**Handling**:
```python
try:
    answer = build_progressive_response(profile, query)
except Exception as e:
    logger.error(f"Progressive response builder failed: {e}")
    # Fallback: Use generic response (better than crash)
    answer = "Let me help you explore your options. What interests you most?"
```

## Testing Strategy

This feature requires both **unit tests** (specific examples, edge cases) and **property-based tests** (universal properties across all inputs).

### Unit Testing

**Test File**: `tests/unit/test_counselor_lock.py`

**Test Cases**:
1. `test_counselor_lock_with_interests()`: Profile with interests → locked
2. `test_counselor_lock_with_constraints()`: Profile with constraints → locked
3. `test_counselor_lock_with_goals()`: Profile with goals → locked
4. `test_counselor_lock_empty_profile()`: Empty profile → not locked
5. `test_multi_intent_respects_lock()`: Multi-intent handler skips when locked
6. `test_structured_respects_lock()`: Structured handler skips when locked
7. `test_progressive_response_references_profile()`: Response mentions known signals
8. `test_no_generic_response_with_profile()`: No "I'm here to help" when profile exists
9. `test_human_judgment_phrases()`: Final recommendation contains micro-judgment phrases
10. `test_uncertainty_detection()`: "idk" query → ambiguity signals extracted
11. `test_uncertainty_adjusted_tone()`: Uncertain user → supportive tone

**Test File**: `tests/integration/test_decision_synthesis_flow.py`

**Test Cases**:
1. `test_5_turn_conflict_conversation()`: Full conversation with conflict resolution
2. `test_counselor_lock_prevents_placement_hijack()`: Turn 3 stays in counselor
3. `test_no_generic_mid_conversation()`: Turns 2-5 build forward from profile
4. `test_final_recommendation_has_human_tone()`: Decision output feels human

### Property-Based Testing

**Why PBT Applies**: The Decision Synthesis Layer has clear universal properties that should hold across all valid inputs:
- Session memory round-trip preservation
- Counselor lock idempotence
- Profile accumulation monotonicity
- Deterministic routing for same profile state

**Test File**: `tests/property/test_decision_synthesis_properties.py`

**Property Test Library**: `hypothesis` (Python PBT library)

**Configuration**: Minimum 100 iterations per property test



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified the following redundancies:

**Redundancy Group 1** (Profile Acknowledgment):
- Properties 2.2, 2.3, 2.4 all test that responses acknowledge specific signal types
- These can be consolidated into a single comprehensive property: "For any profile with signals, response acknowledges those signals"

**Redundancy Group 2** (Human Tone):
- Properties 3.1, 3.2, 3.3, 3.4, 3.5 all test aspects of human-feeling tone
- These can be consolidated into two properties: one for presence of human phrases, one for absence of robotic phrases

**Redundancy Group 3** (Idempotence):
- Properties 7.1 and 7.4 are identical (counselor lock idempotence)
- Properties 7.2 and 7.3 test the same behavior (reads don't modify state) for different functions

**Redundancy Group 4** (Monotonicity):
- Properties 8.2, 8.3, 8.4 all test signal isolation
- Property 8.5 is a specific case of 8.1
- These can be consolidated into two properties: monotonic growth and signal isolation

**Final Property Set**: After consolidation, 15 unique properties remain.

### Property 1: Counselor Lock Activation

*For any* user profile containing at least one signal (interests OR constraints OR goals), the counselor lock SHALL be active.

**Validates: Requirements 1.1, 1.3**

### Property 2: Structured Handler Respects Lock

*For any* session with an active counselor lock, calling `get_structured_response()` with that session_id SHALL return None.

**Validates: Requirements 1.1, 1.2, 1.3**

### Property 3: Multi-Intent Handler Respects Lock

*For any* session with an active counselor lock, calling `get_multi_intent_response()` with that session_id SHALL return None.

**Validates: Requirements 1.1**

### Property 4: Profile Acknowledgment in Responses

*For any* user profile containing signals (interests, constraints, or goals), the counselor response SHALL reference at least one of those signals in the output text.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 5: No Generic Responses with Profile

*For any* non-empty user profile, the counselor response SHALL NOT contain generic greeting phrases like "I'm here to help you find the right path".

**Validates: Requirements 2.5**

### Property 6: Human Judgment Phrases Present

*For any* final recommendation generated by `build_final_recommendation()`, the output SHALL contain at least one human judgment phrase from the set: {"If I were in your position", "In my experience", "Here's what I'd recommend", "Here's the honest path", "Let me break this down"}.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 7: Empathetic Language in Trade-offs

*For any* recommendation involving trade-offs or conflicts, the output SHALL contain at least one empathetic phrase from the set: {"I know this is tough", "This is a common dilemma", "It's okay to", "Let's explore"}.

**Validates: Requirements 3.4**

### Property 8: No Robotic Language

*For any* final recommendation, the output SHALL NOT contain robotic phrases from the set: {"Based on analysis", "The optimal solution is", "According to data", "Algorithmically determined"}.

**Validates: Requirements 3.5**

### Property 9: Uncertainty Signal Extraction

*For any* query containing uncertainty keywords from the set: {"idk", "maybe", "not sure", "confused", "don't know"}, the extracted profile SHALL contain ambiguity signals.

**Validates: Requirements 4.1**

### Property 10: Supportive Tone with Uncertainty

*For any* user profile containing ambiguity signals, the counselor response SHALL use supportive language (contains at least one phrase from: {"It's okay", "Let's explore", "No pressure", "Take your time"}).

**Validates: Requirements 4.2, 4.5**

### Property 11: No Hard Recommendations When Uncertain

*For any* user profile with ambiguity signals, calling `build_final_recommendation()` SHALL either return None OR return a response containing clarifying questions (contains "?").

**Validates: Requirements 4.3, 4.4**

### Property 12: Session Memory Round-Trip

*For any* valid user profile, storing the profile to session memory and then retrieving it SHALL produce an equivalent profile (all signal sets equal, education level equal, confidence level equal).

**Validates: Requirements 6.1**

### Property 13: Counselor Lock Idempotence

*For any* user profile, calling `should_lock_counselor(profile)` multiple times SHALL return the same boolean result on each call.

**Validates: Requirements 7.1, 7.4**

### Property 14: Lock Checks Don't Modify State

*For any* user profile, calling routing functions that check counselor lock (`get_multi_intent_response`, `get_structured_response`) SHALL NOT modify the profile state.

**Validates: Requirements 7.2, 7.3**

### Property 15: Profile Accumulation Monotonicity

*For any* user profile and new signal set, adding signals to the profile SHALL result in a profile where:
- `len(new_profile.interests) >= len(old_profile.interests)`
- `len(new_profile.constraints) >= len(old_profile.constraints)`
- `len(new_profile.goals) >= len(old_profile.goals)`

AND adding signals of one type SHALL NOT remove signals of other types.

**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

### Property 16: Routing Determinism

*For any* user profile and query, calling the routing logic multiple times with the same profile and query SHALL produce the same routing decision (counselor vs structured vs multi-intent).

**Validates: Requirements 5.2**

## Testing Strategy

This feature uses a **dual testing approach** combining unit tests for specific examples and property-based tests for universal correctness guarantees.

### Unit Testing

**Purpose**: Verify specific examples, edge cases, and integration points

**Test Files**:
- `tests/unit/test_counselor_lock.py`: Counselor lock logic
- `tests/unit/test_progressive_responses.py`: Progressive response builder
- `tests/unit/test_human_judgment.py`: Human judgment tone
- `tests/integration/test_decision_synthesis_flow.py`: End-to-end conversation flows

**Key Unit Tests**:
1. **Counselor lock with interests**: Profile with interests → locked
2. **Counselor lock with constraints**: Profile with constraints → locked
3. **Counselor lock empty profile**: Empty profile → not locked
4. **Multi-intent respects lock**: Multi-intent handler skips when locked
5. **Structured respects lock**: Structured handler skips when locked
6. **Progressive response references profile**: Response mentions known signals
7. **No generic with profile**: No "I'm here to help" when profile exists
8. **Human judgment phrases**: Final recommendation contains micro-judgment
9. **Uncertainty detection**: "idk" query → ambiguity signals extracted
10. **5-turn conflict conversation**: Full integration test (from test_real_conversation.py)

### Property-Based Testing

**Purpose**: Verify universal properties across all valid inputs using randomized testing

**Library**: `hypothesis` (Python property-based testing library)

**Configuration**: Minimum 100 iterations per property test

**Test File**: `tests/property/test_decision_synthesis_properties.py`

**Property Test Implementation**:

Each property test will:
1. Use `hypothesis` to generate random valid inputs (profiles, queries, signals)
2. Execute the system function with generated inputs
3. Assert the property holds for all generated inputs
4. Tag each test with a comment referencing the design property

**Example Property Test**:

```python
from hypothesis import given, strategies as st
import pytest

# Feature: decision-synthesis-final-polish, Property 1: Counselor Lock Activation
@given(
    interests=st.sets(st.sampled_from(["coding", "business", "management"]), min_size=1),
    constraints=st.sets(st.sampled_from(["weak_in_math", "not_good_at_studies"]), max_size=2),
    goals=st.sets(st.sampled_from(["high_salary", "quick_job"]), max_size=2),
)
def test_property_counselor_lock_activation(interests, constraints, goals):
    """Property 1: For any profile with signals, counselor lock is active."""
    from app.services.counselor_lock import should_lock_counselor
    from app.services.conversation_memory import UserProfile
    
    # Create profile with at least one signal type
    profile = UserProfile(
        interests=interests if interests else set(),
        constraints=constraints if constraints else set(),
        goals=goals if goals else set(),
    )
    
    # Property: If ANY signal present, lock should be active
    has_signals = bool(profile.interests or profile.constraints or profile.goals)
    assert should_lock_counselor(profile) == has_signals
```

**Property Test Coverage**:

- **Property 1-3**: Counselor lock behavior (100+ random profiles)
- **Property 4-5**: Response content validation (100+ random profiles)
- **Property 6-8**: Human tone validation (100+ random recommendations)
- **Property 9-11**: Uncertainty handling (100+ random uncertain queries)
- **Property 12**: Round-trip preservation (100+ random profiles)
- **Property 13-14**: Idempotence and state isolation (100+ random profiles)
- **Property 15**: Monotonicity (100+ random signal additions)
- **Property 16**: Routing determinism (100+ random profile/query pairs)

### Integration Testing

**Purpose**: Verify end-to-end behavior with realistic conversation flows

**Test File**: `tests/integration/test_decision_synthesis_flow.py`

**Key Integration Tests**:
1. **5-turn conflict conversation**: Tests full flow from interest → constraint → goal1 → goal2 → decision
2. **Counselor lock prevents hijack**: Verifies turn 3 doesn't route to placements
3. **No generic mid-conversation**: Verifies turns 2-5 build forward
4. **Human tone in final output**: Verifies decision feels human

**Existing Test**: `test_real_conversation.py` already implements the 5-turn conflict test with 12 verification checks. This will be integrated into the test suite.

### Test Execution Strategy

**Phase 1: Unit Tests** (fast feedback)
- Run on every commit
- Should complete in < 5 seconds
- Catches basic regressions

**Phase 2: Property Tests** (comprehensive coverage)
- Run on every PR
- Should complete in < 30 seconds (100 iterations × 16 properties)
- Catches edge cases and universal violations

**Phase 3: Integration Tests** (realistic scenarios)
- Run on every PR
- Should complete in < 10 seconds
- Catches end-to-end issues

**Phase 4: Manual Audit** (production readiness)
- Run before release
- 10 test conversations with harsh evaluation
- Target: 10/10 GOOD rating

### Success Criteria

The feature is production-ready when:
1. ✅ All unit tests pass (10/10)
2. ✅ All property tests pass (16/16 properties hold for 100+ iterations each)
3. ✅ All integration tests pass (4/4)
4. ✅ 5-turn conflict test passes all 12 checks
5. ✅ Manual audit achieves 10/10 GOOD rating

## Implementation Notes

### Code Organization

**New Files**:
- `backend/app/services/counselor_lock.py`: Centralized lock logic
- `tests/property/test_decision_synthesis_properties.py`: Property-based tests

**Modified Files**:
- `backend/app/services/structured_knowledge.py`: Add session_id parameter, check lock
- `backend/app/services/counselor_handler.py`: Add progressive response builder
- `backend/app/services/conversation_memory.py`: Enhance human judgment layer
- `backend/app/api/chat.py`: Pass session_id to structured handler

### Implementation Order

1. **Create counselor_lock.py** with `should_lock_counselor()` function
2. **Modify structured_knowledge.py** to check lock before returning responses
3. **Modify chat.py** to pass session_id to structured handler
4. **Modify counselor_handler.py** to add progressive response builder
5. **Enhance conversation_memory.py** with human judgment phrases
6. **Write unit tests** for each component
7. **Write property tests** for universal properties
8. **Run integration tests** to verify end-to-end behavior
9. **Perform manual audit** with 10 test conversations

### Performance Considerations

- **Counselor lock check**: O(1) - just checks if sets are non-empty
- **Profile retrieval**: O(1) - dictionary lookup by session_id
- **Progressive response building**: O(n) where n = number of signals (typically < 10)
- **Property tests**: 100 iterations × 16 properties = 1600 test cases (should complete in < 30s)

### Backward Compatibility

This feature is **backward compatible**:
- Existing sessions without profiles continue to work (empty profile → no lock)
- Existing routing logic unchanged for non-counselor queries
- New session_id parameter is optional (defaults to None → no lock check)

### Deployment Strategy

**Phase 1: Canary Deployment** (10% traffic)
- Monitor counselor lock activation rate
- Monitor routing decision distribution
- Monitor response quality metrics

**Phase 2: Gradual Rollout** (50% traffic)
- Verify no increase in fallback rate
- Verify no increase in user confusion signals
- Verify improvement in conversation continuity

**Phase 3: Full Deployment** (100% traffic)
- Monitor for 48 hours
- Collect user feedback
- Perform post-deployment audit

### Monitoring and Observability

**Key Metrics**:
- `counselor_lock_activation_rate`: % of queries with active lock
- `routing_decision_distribution`: counselor vs structured vs multi-intent vs RAG
- `generic_response_rate`: % of responses containing generic phrases
- `human_tone_score`: % of recommendations with human judgment phrases
- `conversation_continuity_score`: % of multi-turn conversations without routing breaks

**Logging**:
- Log counselor lock decisions with reason (for debugging)
- Log profile state at each turn (for conversation analysis)
- Log routing decisions with profile summary (for audit trail)

### Rollback Plan

If issues are detected:
1. **Immediate**: Feature flag to disable counselor lock (fall back to old routing)
2. **Short-term**: Revert to previous version of structured_knowledge.py and counselor_handler.py
3. **Long-term**: Fix issues, re-test, re-deploy

### Documentation Updates

**User-Facing**:
- Update chatbot behavior documentation
- Add examples of multi-turn conversations
- Explain how the system remembers context

**Developer-Facing**:
- Document counselor lock architecture
- Document progressive response builder
- Document property-based testing approach
- Add architecture diagrams showing routing flow

## Conclusion

This design completes the Decision Synthesis Layer by implementing three critical improvements:

1. **System-Level Counselor Lock**: Ensures deterministic routing across all layers, preventing mid-conversation hijacking
2. **Progressive Response Builder**: Eliminates generic responses by always building forward from accumulated context
3. **Human Judgment Layer**: Makes recommendations feel human through micro-judgment phrases and empathetic language

The design uses property-based testing to verify universal correctness guarantees (round-trip preservation, idempotence, monotonicity, determinism) while maintaining comprehensive unit and integration test coverage.

**Production Readiness**: This feature transforms the Decision Synthesis Layer from "working system" to "trustworthy advisor" by ensuring routing stability, conversation continuity, and human-feeling recommendations.
