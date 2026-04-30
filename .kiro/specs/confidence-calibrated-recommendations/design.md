# Design Document: Confidence-Calibrated Recommendations

## Overview

This feature adds adaptive tone mapping to career counseling recommendations based on user confidence levels. The core architectural principle is **tone injection as post-processing** — tone is applied AFTER decision logic completes, not intertwined with it.

**Key Design Principle**: Separation of concerns between WHAT to say (decision engine) and HOW it feels (tone layer).

The system already extracts confidence levels (`low`, `medium`, `high`) and stores them in `UserProfile.confidence_level`. This design adds a pure transformation layer that takes completed recommendations and adjusts their tone based on confidence, without modifying decision logic, routing, or memory systems.

### Design Goals

1. **Surgical Tone Injection**: Modify only opening phrases and judgment strength, not content structure
2. **Pure Function Architecture**: Tone transformation is stateless and side-effect-free
3. **Preserve Existing Logic**: No changes to decision synthesis, routing, or profile extraction
4. **Natural Language Output**: Avoid robotic or template-like responses
5. **Testable Separation**: Tone layer can be tested independently of decision logic

### Non-Goals

- Modifying decision synthesis logic in `build_final_recommendation`
- Changing counselor routing behavior
- Altering profile extraction or memory accumulation
- Rewriting recommendation structure or bullet points
- Adding new confidence detection logic (already exists)

## Architecture

### Layer Separation

```
User Query
    ↓
Profile Extraction (existing)
    ↓
Decision Engine (build_final_recommendation)
    ↓
    │ Returns base recommendation string
    ↓
Tone Layer (apply_confidence_tone) ← NEW
    ↓
    │ Transforms tone based on confidence
    ↓
Final Output
```

**Critical Constraint**: The tone layer receives a complete recommendation string and returns a modified string. It does NOT:
- Access UserProfile directly
- Build recommendations from scratch
- Modify decision logic
- Change routing behavior

### Component Responsibilities

| Component | Responsibility | What It Does NOT Do |
|-----------|---------------|---------------------|
| **Decision Engine** | Determine WHAT to recommend | Apply tone, access confidence |
| **Tone Layer** | Determine HOW it feels | Make decisions, access profile |
| **Profile Extraction** | Extract signals from queries | Apply tone, make recommendations |
| **Routing Logic** | Direct to counselor/info | Apply tone, make decisions |

## Components and Interfaces

### 1. ToneProfile (Data Structure)

A structured representation of tone parameters for a given confidence level.

```python
@dataclass
class ToneProfile:
    """Tone parameters for a specific confidence level."""
    
    # Opening phrase to inject before recommendation
    prefix: str
    
    # Strength of judgment language ("I'd recommend" vs "Consider")
    judgment_phrase: str
    
    # Confidence strength indicator
    confidence_strength: str  # "exploratory", "balanced", "decisive"
    
    def __post_init__(self):
        """Validate tone profile parameters."""
        valid_strengths = {"exploratory", "balanced", "decisive"}
        if self.confidence_strength not in valid_strengths:
            raise ValueError(f"Invalid confidence_strength: {self.confidence_strength}")
```

**Design Rationale**: Structured data makes tone parameters explicit, testable, and maintainable. Avoids scattering magic strings throughout code.

### 2. get_tone_profile() Function

Maps confidence levels to tone parameters.

```python
def get_tone_profile(confidence: str) -> ToneProfile:
    """
    Map confidence level to tone parameters.
    
    Args:
        confidence: User confidence level ("low", "medium", "high")
        
    Returns:
        ToneProfile with appropriate tone parameters
        
    Raises:
        ValueError: If confidence level is invalid
    """
    tone_map = {
        "low": ToneProfile(
            prefix="It's okay to feel unsure — but here's one way to approach this.",
            judgment_phrase="Consider",
            confidence_strength="exploratory"
        ),
        "medium": ToneProfile(
            prefix="Based on what you've told me, here's a practical path:",
            judgment_phrase="I'd recommend",
            confidence_strength="balanced"
        ),
        "high": ToneProfile(
            prefix="Based on your clear goals, here's what I'd strongly suggest:",
            judgment_phrase="I'd strongly recommend",
            confidence_strength="decisive"
        )
    }
    
    if confidence not in tone_map:
        # Default to medium for invalid/missing confidence
        return tone_map["medium"]
    
    return tone_map[confidence]
```

**Design Rationale**: 
- Centralized tone mapping prevents duplication
- Explicit defaults handle edge cases gracefully
- Pure function with no side effects
- Easy to extend with new confidence levels

### 3. apply_confidence_tone() Function

The core tone injection function — a pure transformation layer.

```python
def apply_confidence_tone(
    base_recommendation: str,
    confidence: str,
    force: bool = False
) -> str:
    """
    Apply confidence-appropriate tone to a base recommendation.
    
    This is a PURE FUNCTION that transforms recommendation tone without
    modifying decision logic or accessing user profile.
    
    Architecture Constraint: This function receives a COMPLETE recommendation
    and returns a MODIFIED recommendation. It does NOT build recommendations.
    
    Args:
        base_recommendation: Complete recommendation string from decision engine
        confidence: User confidence level ("low", "medium", "high")
        force: Whether decision override is active
        
    Returns:
        Recommendation with confidence-appropriate tone applied
        
    Edge Cases:
        - Empty recommendation: Returns empty string
        - Invalid confidence: Defaults to "medium" tone
        - force=True + low confidence: Uses "soft decision" tone
    """
    # Edge case: empty recommendation
    if not base_recommendation or not base_recommendation.strip():
        return ""
    
    # Edge case: force override with low confidence
    # Use gentle but decisive tone (not fully confident, not purely exploratory)
    if force and confidence == "low":
        tone = ToneProfile(
            prefix="It's okay to feel unsure — but based on what you've told me, here's how I'd approach this.",
            judgment_phrase="I'd recommend",
            confidence_strength="balanced"
        )
    else:
        tone = get_tone_profile(confidence)
    
    # Surgical injection: modify only opening and judgment phrases
    modified = _inject_tone_prefix(base_recommendation, tone.prefix)
    modified = _adjust_judgment_strength(modified, tone.judgment_phrase)
    
    return modified


def _inject_tone_prefix(recommendation: str, prefix: str) -> str:
    """
    Inject tone-appropriate prefix into recommendation opening.
    
    Strategy: Replace or prepend to the first line that starts with
    "Based on what you've told me" or similar opening phrases.
    
    Args:
        recommendation: Original recommendation text
        prefix: Tone-appropriate prefix to inject
        
    Returns:
        Recommendation with prefix injected
    """
    lines = recommendation.split("\n")
    
    # Find opening line patterns to replace
    opening_patterns = [
        "Based on what you've told me:",
        "Here's the honest path:",
        "Based on your",
    ]
    
    for i, line in enumerate(lines):
        for pattern in opening_patterns:
            if line.strip().startswith(pattern):
                # Inject prefix before this line
                lines.insert(i, prefix)
                lines.insert(i + 1, "")  # Add blank line for readability
                return "\n".join(lines)
    
    # No opening pattern found — prepend prefix to start
    return f"{prefix}\n\n{recommendation}"


def _adjust_judgment_strength(recommendation: str, judgment_phrase: str) -> str:
    """
    Adjust judgment phrase strength in recommendation.
    
    Strategy: Replace existing judgment phrases with confidence-appropriate ones.
    
    Args:
        recommendation: Recommendation text
        judgment_phrase: Confidence-appropriate judgment phrase
        
    Returns:
        Recommendation with adjusted judgment strength
    """
    # Map of phrases to replace based on judgment strength
    replacements = {
        "My recommendation": f"{judgment_phrase}",
        "I'd recommend": judgment_phrase,
        "I recommend": judgment_phrase,
    }
    
    modified = recommendation
    for old_phrase, new_phrase in replacements.items():
        modified = modified.replace(old_phrase, new_phrase)
    
    return modified
```

**Design Rationale**:
- **Pure function**: No side effects, no state access
- **Surgical modification**: Changes only opening and judgment phrases, not structure
- **Edge case handling**: Explicit handling of force + low confidence
- **Testability**: Can test with simple string inputs/outputs
- **Separation**: Completely independent of decision logic

### 4. Integration Point

The tone layer integrates into `build_final_recommendation` as the final step before return.

```python
# In conversation_memory.py, modify build_final_recommendation:

def build_final_recommendation(
    profile: UserProfile, 
    query: str, 
    force: bool = False
) -> Optional[str]:
    """
    Build a final recommendation based on accumulated profile.
    
    NEW: Applies confidence-calibrated tone as final step.
    """
    # ... existing decision logic (unchanged) ...
    
    # Build base recommendation (all existing logic)
    base_recommendation = _build_base_recommendation(profile, query, force)
    
    if base_recommendation is None:
        return None
    
    # NEW: Apply confidence-appropriate tone
    final_recommendation = apply_confidence_tone(
        base_recommendation=base_recommendation,
        confidence=profile.confidence_level,
        force=force
    )
    
    return final_recommendation
```

**Design Rationale**:
- Minimal change to existing function
- Tone application is the last step (post-processing)
- Decision logic remains unchanged
- Clear separation of concerns

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: ToneProfile Completeness

*For any* valid confidence level ("low", "medium", "high"), the ToneProfile returned by `get_tone_profile()` SHALL have all required fields (prefix, judgment_phrase, confidence_strength) populated with non-empty strings.

**Validates: Requirements 2.4**

**Rationale**: This ensures the tone mapping function always produces complete, usable tone parameters. A ToneProfile with missing fields would cause downstream failures in tone injection.

### Property 2: Prefix Injection Preservation

*For any* base recommendation string and any ToneProfile, applying `apply_confidence_tone()` SHALL result in output that contains the ToneProfile's prefix phrase.

**Validates: Requirements 3.2**

**Rationale**: This verifies that the tone layer successfully injects the confidence-appropriate opening phrase into all recommendations, regardless of recommendation structure or content.

### Property 3: Judgment Phrase Replacement

*For any* base recommendation containing judgment phrases ("My recommendation", "I'd recommend", "I recommend") and any ToneProfile, applying `apply_confidence_tone()` SHALL replace those phrases with the ToneProfile's judgment_phrase.

**Validates: Requirements 3.3**

**Rationale**: This ensures that judgment strength is consistently adjusted based on confidence level. The original judgment phrases should not appear in the output when they've been replaced with confidence-appropriate alternatives.

## Data Models

### ToneProfile

```python
@dataclass
class ToneProfile:
    prefix: str              # Opening phrase
    judgment_phrase: str     # Judgment strength
    confidence_strength: str # "exploratory", "balanced", "decisive"
```

**Fields**:
- `prefix`: Tone-appropriate opening phrase to inject
- `judgment_phrase`: Confidence-appropriate judgment language
- `confidence_strength`: Categorical indicator of tone strength

**Validation**:
- `confidence_strength` must be one of: `"exploratory"`, `"balanced"`, `"decisive"`
- All fields are required (no optional fields)

### UserProfile (Existing - No Changes)

The existing `UserProfile` already contains `confidence_level: str` field. No modifications needed.

## Error Handling

### Invalid Confidence Level

**Scenario**: `confidence_level` is missing, None, or invalid value

**Handling**: Default to `"medium"` confidence

```python
def get_tone_profile(confidence: str) -> ToneProfile:
    if confidence not in tone_map:
        return tone_map["medium"]  # Safe default
```

**Rationale**: Graceful degradation — system continues with balanced tone rather than failing.

### Empty Recommendation

**Scenario**: `base_recommendation` is empty or None

**Handling**: Return empty string immediately

```python
def apply_confidence_tone(base_recommendation: str, ...) -> str:
    if not base_recommendation or not base_recommendation.strip():
        return ""
```

**Rationale**: No tone to apply if there's no recommendation. Fail fast.

### Force + Low Confidence Edge Case

**Scenario**: User has low confidence but explicitly requests decision (`force=True`)

**Handling**: Use "soft decision" tone — gentle acknowledgment + clear recommendation

```python
if force and confidence == "low":
    tone = ToneProfile(
        prefix="It's okay to feel unsure — but based on what you've told me, here's how I'd approach this.",
        judgment_phrase="I'd recommend",
        confidence_strength="balanced"
    )
```

**Rationale**: Respects user's request for decision while acknowledging their uncertainty. Not fully confident tone (would feel dismissive), not purely exploratory (would ignore their request).

### Malformed Recommendation Structure

**Scenario**: Recommendation doesn't contain expected opening patterns

**Handling**: Prepend prefix to start of recommendation

```python
# In _inject_tone_prefix:
# No opening pattern found — prepend prefix to start
return f"{prefix}\n\n{recommendation}"
```

**Rationale**: Ensures tone is always applied, even if recommendation structure changes.

## Testing Strategy

### Dual Testing Approach

This feature requires both **unit tests** (for specific examples and edge cases) and **property-based tests** (for universal properties across all inputs). Together, they provide comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and integration points
- **Property tests**: Verify universal properties hold across randomized inputs

### Property-Based Testing

**Library**: Use `pytest` with `hypothesis` library (Python's standard PBT framework)

**Configuration**: Each property test MUST run minimum 100 iterations to ensure comprehensive input coverage.

**Test Tagging**: Each property test MUST include a comment tag referencing the design property:

```python
# Feature: confidence-calibrated-recommendations, Property 1: ToneProfile Completeness
@given(confidence=st.sampled_from(["low", "medium", "high"]))
def test_tone_profile_completeness(confidence):
    profile = get_tone_profile(confidence)
    assert profile.prefix
    assert profile.judgment_phrase
    assert profile.confidence_strength
```

**Property Tests Required**:

1. **Property 1: ToneProfile Completeness**
   - Generator: Valid confidence levels ("low", "medium", "high")
   - Assertion: All fields non-empty
   - Tag: `Feature: confidence-calibrated-recommendations, Property 1: ToneProfile Completeness`

2. **Property 2: Prefix Injection Preservation**
   - Generator: Random recommendation strings + all tone profiles
   - Assertion: Output contains prefix
   - Tag: `Feature: confidence-calibrated-recommendations, Property 2: Prefix Injection Preservation`

3. **Property 3: Judgment Phrase Replacement**
   - Generator: Recommendations with judgment phrases + all tone profiles
   - Assertion: Original phrases replaced with tone-appropriate phrases
   - Tag: `Feature: confidence-calibrated-recommendations, Property 3: Judgment Phrase Replacement`

### Unit Tests

**Test Coverage**:

1. **ToneProfile Creation**
   - Valid confidence levels create correct profiles
   - Invalid confidence defaults to medium
   - Profile validation catches invalid strength values

2. **get_tone_profile() Function**
   - Low confidence → exploratory tone
   - Medium confidence → balanced tone
   - High confidence → decisive tone
   - Invalid confidence → medium default
   - None confidence → medium default

3. **apply_confidence_tone() Function**
   - Empty recommendation → empty string
   - Low confidence → exploratory prefix
   - Medium confidence → balanced prefix
   - High confidence → decisive prefix
   - Force + low confidence → soft decision tone
   - Judgment phrase replacement works correctly
   - Prefix injection works with various recommendation structures

4. **Tone Injection Helpers**
   - `_inject_tone_prefix()` finds and replaces opening patterns
   - `_inject_tone_prefix()` prepends when no pattern found
   - `_adjust_judgment_strength()` replaces judgment phrases correctly

5. **Integration with build_final_recommendation**
   - Tone layer is called after decision logic
   - Profile confidence level is passed correctly
   - Force parameter is passed correctly
   - None recommendations are handled gracefully

**Example Unit Test**:

```python
def test_apply_confidence_tone_low():
    base = "Based on what you've told me:\n• You like coding\n\nMy recommendation: Start with BCA"
    result = apply_confidence_tone(base, confidence="low", force=False)
    
    assert "It's okay to feel unsure" in result
    assert "Consider" in result
    assert "My recommendation" not in result  # Replaced with "Consider"

def test_apply_confidence_tone_force_low():
    base = "Based on what you've told me:\n• You like coding\n\nMy recommendation: Start with BCA"
    result = apply_confidence_tone(base, confidence="low", force=True)
    
    assert "It's okay to feel unsure" in result
    assert "I'd recommend" in result  # Soft decision, not "Consider"
    assert "based on what you've told me" in result.lower()
```

### Integration Tests

**Test Coverage**:

1. **End-to-End Tone Application**
   - User with low confidence gets exploratory tone
   - User with high confidence gets decisive tone
   - Force override with low confidence gets soft decision tone

2. **Recommendation Structure Preservation**
   - Bullet points remain unchanged
   - Reasoning sections remain unchanged
   - Only opening and judgment phrases are modified

3. **Edge Case Handling**
   - Missing confidence level defaults to medium
   - Empty recommendations return empty
   - Malformed recommendations still get tone applied

**Example Integration Test**:

```python
def test_end_to_end_low_confidence_recommendation():
    profile = UserProfile(
        interests={"coding"},
        confidence_level="low"
    )
    
    recommendation = build_final_recommendation(profile, "what should I do", force=False)
    
    assert recommendation is None  # Low confidence without force returns None
    
def test_end_to_end_force_low_confidence():
    profile = UserProfile(
        interests={"coding"},
        confidence_level="low"
    )
    
    recommendation = build_final_recommendation(profile, "what should I do", force=True)
    
    assert recommendation is not None
    assert "It's okay to feel unsure" in recommendation
    assert "I'd recommend" in recommendation  # Soft decision tone
```

### Manual Testing Scenarios

1. **Low Confidence User**
   - Input: "I'm not sure what to do, I like coding but weak in math"
   - Expected: Exploratory tone with "Consider" language

2. **High Confidence User**
   - Input: "I want to do coding, I'm good at it, what should I do"
   - Expected: Decisive tone with "I'd strongly recommend" language

3. **Force Override**
   - Input: Low confidence user asks "just tell me what to do"
   - Expected: Soft decision tone — gentle but clear

4. **Medium Confidence (Default)**
   - Input: "I like coding, what should I study"
   - Expected: Balanced tone with "I'd recommend" language

## Tone Variation Examples

### Low Confidence (Exploratory)

**Before Tone Layer**:
```
Based on what you've told me:
• You like coding
• You're weak in math

My recommendation: Start with BCA
```

**After Tone Layer**:
```
It's okay to feel unsure — but here's one way to approach this.

Based on what you've told me:
• You like coding
• You're weak in math

Consider: Start with BCA
```

### Medium Confidence (Balanced)

**Before Tone Layer**:
```
Based on what you've told me:
• You like coding

My recommendation: Start with BCA
```

**After Tone Layer**:
```
Based on what you've told me, here's a practical path:

• You like coding

I'd recommend: Start with BCA
```

### High Confidence (Decisive)

**Before Tone Layer**:
```
Based on what you've told me:
• You like coding
• You want high salary

My recommendation: BCA → MCA
```

**After Tone Layer**:
```
Based on your clear goals, here's what I'd strongly suggest:

• You like coding
• You want high salary

I'd strongly recommend: BCA → MCA
```

### Force + Low Confidence (Soft Decision)

**Before Tone Layer**:
```
Based on what you've told me:
• You like coding
• You're weak in math

My recommendation: Start with BCA
```

**After Tone Layer**:
```
It's okay to feel unsure — but based on what you've told me, here's how I'd approach this.

• You like coding
• You're weak in math

I'd recommend: Start with BCA
```

**Note**: This is NOT fully confident tone (would feel dismissive of their uncertainty) and NOT purely exploratory (would ignore their request for decision).

## Implementation Notes

### What Changes

1. **New Functions** (in `conversation_memory.py`):
   - `ToneProfile` dataclass
   - `get_tone_profile()` function
   - `apply_confidence_tone()` function
   - `_inject_tone_prefix()` helper
   - `_adjust_judgment_strength()` helper

2. **Modified Function**:
   - `build_final_recommendation()` — add tone application as final step

### What Does NOT Change

1. **Decision Logic**: All recommendation building logic remains unchanged
2. **Profile Extraction**: `extract_user_profile()` unchanged
3. **Routing Logic**: `should_force_counselor()` unchanged
4. **Memory Store**: `ConversationMemory` class unchanged
5. **Profile Structure**: `UserProfile` dataclass unchanged (already has `confidence_level`)

### Code Organization

```
backend/app/services/conversation_memory.py
├── UserProfile (existing)
├── ConversationMemory (existing)
├── extract_user_profile() (existing)
├── should_force_counselor() (existing)
├── build_memory_context() (existing)
├── is_decision_query() (existing)
├── ToneProfile (NEW)
├── get_tone_profile() (NEW)
├── apply_confidence_tone() (NEW)
├── _inject_tone_prefix() (NEW)
├── _adjust_judgment_strength() (NEW)
└── build_final_recommendation() (MODIFIED - add tone layer call)
```

### Refactoring Strategy

To maintain clean separation, extract base recommendation logic:

```python
def _build_base_recommendation(profile: UserProfile, query: str, force: bool) -> Optional[str]:
    """
    Build base recommendation without tone (existing logic).
    
    This is the existing build_final_recommendation logic extracted
    into a separate function for clarity.
    """
    # All existing recommendation building logic moves here
    # Returns base recommendation string
    pass

def build_final_recommendation(profile: UserProfile, query: str, force: bool = False) -> Optional[str]:
    """
    Build final recommendation with confidence-calibrated tone.
    
    This is the public API that applies tone layer.
    """
    base = _build_base_recommendation(profile, query, force)
    
    if base is None:
        return None
    
    return apply_confidence_tone(base, profile.confidence_level, force)
```

**Rationale**: Clear separation makes testing easier and enforces architectural constraint.

## Performance Considerations

### Computational Cost

- **Tone Profile Lookup**: O(1) dictionary lookup
- **String Replacement**: O(n) where n = recommendation length
- **Overall Impact**: Negligible (< 1ms for typical recommendations)

### Memory Footprint

- **ToneProfile Objects**: 3 instances (low, medium, high) — ~1KB total
- **String Operations**: Temporary strings during replacement — ~10KB max
- **Overall Impact**: Negligible

### Optimization Opportunities

1. **Cache Tone Profiles**: Create once at module load
2. **Regex Compilation**: Pre-compile patterns if using regex
3. **String Builder**: Use list join instead of repeated concatenation

**Current Assessment**: No optimization needed — performance is not a concern for this feature.

## Security Considerations

### Input Validation

- **Confidence Level**: Validated in `get_tone_profile()` with safe default
- **Recommendation String**: No injection risk (pure text transformation)
- **Force Parameter**: Boolean type enforced by Python

### No New Attack Surface

- Pure functions with no external I/O
- No database access
- No network calls
- No user input directly processed (only pre-validated profile data)

**Assessment**: No security concerns introduced by this feature.

## Deployment Considerations

### Rollout Strategy

1. **Phase 1**: Deploy tone layer code (no behavior change yet)
2. **Phase 2**: Enable tone application in `build_final_recommendation`
3. **Phase 3**: Monitor logs for tone distribution (low/medium/high)
4. **Phase 4**: Collect user feedback on tone appropriateness

### Feature Flag

Consider adding feature flag for gradual rollout:

```python
ENABLE_CONFIDENCE_TONE = os.getenv("ENABLE_CONFIDENCE_TONE", "true").lower() == "true"

def build_final_recommendation(...):
    base = _build_base_recommendation(...)
    
    if not ENABLE_CONFIDENCE_TONE:
        return base
    
    return apply_confidence_tone(base, profile.confidence_level, force)
```

### Monitoring

**Metrics to Track**:
- Tone distribution (% low, medium, high)
- Force override frequency with low confidence
- Average recommendation length by tone
- User satisfaction by tone (if feedback available)

### Rollback Plan

If issues arise:
1. Set `ENABLE_CONFIDENCE_TONE=false` environment variable
2. Redeploy (falls back to base recommendations)
3. No data migration needed (stateless feature)

## Future Enhancements

### Potential Extensions (Out of Scope)

1. **Dynamic Tone Profiles**: Learn tone preferences from user feedback
2. **Granular Tone Control**: More than 3 confidence levels
3. **Context-Aware Tone**: Adjust based on query type (career vs. course)
4. **Tone Consistency**: Ensure tone matches across multi-turn conversations
5. **A/B Testing**: Compare tone variations for effectiveness

### Extensibility Points

The design supports future extensions:

- **New Confidence Levels**: Add to `tone_map` in `get_tone_profile()`
- **Custom Tone Profiles**: Pass `ToneProfile` directly to `apply_confidence_tone()`
- **Tone Strategies**: Replace `_inject_tone_prefix()` with different strategies
- **Language Support**: Extend tone profiles for multiple languages

## Conclusion

This design enforces strict separation between decision logic (WHAT to say) and tone application (HOW it feels). The tone layer is a pure, stateless transformation that can be tested independently and deployed with minimal risk.

**Key Architectural Wins**:
1. ✅ Tone is injected, not intertwined
2. ✅ Pure function architecture (no side effects)
3. ✅ Surgical modification (only opening and judgment phrases)
4. ✅ Preserves all existing logic (decision, routing, memory)
5. ✅ Testable in isolation
6. ✅ Handles edge cases explicitly (force + low confidence)

The design is ready for implementation with clear interfaces, comprehensive error handling, and a straightforward testing strategy.
