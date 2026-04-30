"""
HEAVY TASK IMPLEMENTATION GUIDE
Contradiction Engine + Signal Extraction Hardening Integration

This file shows EXACTLY where to integrate the two new modules into
the existing orchestration engine.

Files Created:
  1. contradiction_engine.py - Detects contradictions, applies penalties
  2. signal_extractor.py - Robust signal extraction (handles messy input)
  3. integration_heavy_tasks.py - Integration logic
  4. INTEGRATION_GUIDE.md (this file) - Implementation instructions

═══════════════════════════════════════════════════════════════════════════════
PHASE 1: SIGNAL EXTRACTION HARDENING (REPLACES FRAGILE EXTRACTION)
═══════════════════════════════════════════════════════════════════════════════

Currently in engine.py, signal extraction is done by various dispersed functions.
We'll REPLACE fragile extraction with robust extraction.

CHANGE LOCATION 1: In orchestration/engine.py - run_orchestration() function

BEFORE (Current, Fragile):
    # Old way - used scattered functions from counselor modules
    entities = context.get("_entities") or context
    extracted_courses = entities.get("courses", [])
    
    # Limited interest extraction
    from app.services.counselor.entity_extractor import extract_entities
    entities = extract_entities(working_query)

AFTER (New, Hardened):
    # NEW: Import robust signal extractor
    from app.services.orchestration.signal_extractor import (
        extract_robust_signals,
        filter_high_confidence_signals,
        aggregate_signals_by_type,
        SignalType
    )
    
    # NEW: Replace fragile extraction with robust version
    signal_result = extract_robust_signals(working_query)
    
    # NEW: Filter for high confidence only (production-safe)
    high_confidence_signals = filter_high_confidence_signals(
        signal_result.signals,
        min_confidence=0.65  # Only trust signals above this threshold
    )
    
    # NEW: Group by type for easier access
    signals_by_type = aggregate_signals_by_type(high_confidence_signals)
    
    # NEW: Extract entities from robust signals
    extracted_courses = _extract_courses_from_signals(signals_by_type, working_query)
    
    # Store signal quality in context (for tone adjustment)
    context["signal_ambiguity"] = signal_result.ambiguity_score
    context["input_is_messy"] = signal_result.is_messy
    context["extracted_signals"] = signal_result.signals


═══════════════════════════════════════════════════════════════════════════════
PHASE 2: CONTRADICTION DETECTION (NEW LAYER BEFORE CONFIDENCE UPDATE)
═══════════════════════════════════════════════════════════════════════════════

Add this AFTER signal extraction, BEFORE confidence update.

CHANGE LOCATION 2: In orchestration/engine.py - run_orchestration() function

INSERT (after signal extraction, before confidence calculation):

    # ═══════════════════════════════════════════════════════════════════════
    # HEAVY TASK: CONTRADICTION DETECTION & CONFIDENCE PENALTIES
    # ═══════════════════════════════════════════════════════════════════════
    
    from app.services.orchestration.contradiction_engine import (
        detect_contradictions,
        apply_contradiction_penalty,
        should_address_contradiction,
        get_contradiction_summary,
    )
    
    # Get student profile history (from memory service)
    student_id = session_id  # or context.get("student_id")
    if hasattr(context.get("_memory"), "get_profile_history"):
        profile_history = context["_memory"].get_profile_history(student_id)
    else:
        profile_history = []
    
    # Convert robust signals to profile format for contradiction detection
    new_profile_signals = _signals_to_profile_signals(signals_by_type)
    
    # Detect contradictions
    contradictions = detect_contradictions(profile_history, new_profile_signals)
    
    # Store for later use
    context["detected_contradictions"] = contradictions
    context["contradiction_summary"] = get_contradiction_summary(contradictions)
    
    if contradictions:
        logger.warning(f"[CONTRADICTION] {context['contradiction_summary']}")
    
    # Apply penalty to confidence
    current_confidence = context.get("confidence", 0.5)
    new_confidence, penalty_applied = apply_contradiction_penalty(
        current_confidence,
        contradictions,
        max_penalty=0.30  # Bounded delta
    )
    
    # Update context
    context["confidence"] = new_confidence
    context["confidence_penalty"] = penalty_applied
    context["is_stable"] = penalty_applied <= 0.10


═══════════════════════════════════════════════════════════════════════════════
PHASE 3: TONE LAYER INTEGRATION (USE CONTRADICTIONS IN RESPONSE)
═══════════════════════════════════════════════════════════════════════════════

Modify the tone/persona layer to acknowledge contradictions.

CHANGE LOCATION 3: In counselor/persona.py - apply_hybrid_behavior()

INSERT (at beginning of response generation):

    # NEW: Check for contradictions and adjust tone
    from app.services.orchestration.contradiction_engine import (
        should_address_contradiction,
        generate_contradiction_response
    )
    
    contradictions = context.get("detected_contradictions", [])
    
    if contradictions and should_address_contradiction(contradictions):
        # Address the strongest contradiction
        strongest = sorted(contradictions, key=lambda c: c.severity, reverse=True)[0]
        ack = generate_contradiction_response(strongest)
        
        # Prepend acknowledgment to response
        response = f"{ack}\n\n{response}"
        
        # Adjust tone to be more questioning (uncertain)
        tone_params["confidence_level"] = "questioning"
        tone_params["uncertainty"] = 0.3
    
    # If user is unstable (low confidence), use gentler tone
    is_stable = context.get("is_stable", True)
    if not is_stable:
        tone_params["urgency"] = "low"
        tone_params["pressure"] = "minimal"


═══════════════════════════════════════════════════════════════════════════════
PHASE 4: MEMORY LAYER INTEGRATION (SAVE EXTENDED PROFILE)
═══════════════════════════════════════════════════════════════════════════════

Update profile saving to include new fields.

CHANGE LOCATION 4: In counselor/memory.py - update_student_profile()

MODIFY (to save extended fields):

    def update_student_profile(student_id: str, profile_update: Dict) -> Dict:
        \"\"\"Update student profile with new signals and confidence.\"\"\"
        
        # Get current profile
        current_profile = get_student_profile(student_id) or {}
        
        # Merge updates
        current_profile.update(profile_update)
        
        # NEW: Save extended fields
        current_profile["confidence"] = profile_update.get("confidence", current_profile.get("confidence", 0.5))
        current_profile["clarity_level"] = profile_update.get("clarity_level")
        current_profile["input_quality"] = profile_update.get("input_quality")
        current_profile["ambiguity_score"] = profile_update.get("ambiguity_score")
        current_profile["last_confidence_update"] = datetime.now().isoformat()
        
        # Save to memory
        SESSION_MEMORY[student_id] = current_profile
        
        return current_profile
    
    # NEW: Add method to get profile history
    def get_profile_history(student_id: str, limit: int = 10) -> List[Dict]:
        \"\"\"Get recent profile states for contradiction detection.\"\"\"
        # This might be loaded from a database in production
        # For now, maintain in memory or retrieve from conversation history
        history = getattr(SESSION_MEMORY.get(student_id, {}), "_history", [])
        return history[-limit:]


═══════════════════════════════════════════════════════════════════════════════
PHASE 5: HELPER FUNCTIONS (ADD TO engine.py)
═══════════════════════════════════════════════════════════════════════════════

Add these helper functions to orchestration/engine.py:

def _extract_courses_from_signals(signals_by_type: Dict, query: str) -> List[str]:
    \"\"\"Extract course mentions from robust signals.\"\"\"
    from app.services.orchestration.signal_extractor import SignalType
    
    courses = []
    
    # Method 1: Extract from interest signals
    if SignalType.INTEREST in signals_by_type:
        for signal in signals_by_type[SignalType.INTEREST]:
            # Map interest to course
            course = _map_interest_to_course(signal.value)
            if course:
                courses.append(course)
    
    # Method 2: Direct course mentions in query
    direct = extract_course_mentions(query)  # Use existing function
    courses.extend(direct)
    
    return list(set(courses))  # Deduplicate


def _signals_to_profile_signals(signals_by_type: Dict) -> Dict[str, Any]:
    \"\"\"Convert robust signals to profile format for contradiction detection.\"\"\"
    from app.services.orchestration.signal_extractor import SignalType
    
    profile_signals = {}
    
    if SignalType.INTEREST in signals_by_type:
        best_interest = max(signals_by_type[SignalType.INTEREST], 
                           key=lambda s: s.confidence)
        profile_signals["interests"] = best_interest.value
    
    if SignalType.CONSTRAINT in signals_by_type:
        best_constraint = max(signals_by_type[SignalType.CONSTRAINT],
                             key=lambda s: s.confidence)
        profile_signals["math_ability"] = best_constraint.value
    
    if SignalType.GOAL in signals_by_type:
        best_goal = max(signals_by_type[SignalType.GOAL],
                       key=lambda s: s.confidence)
        profile_signals["goal"] = best_goal.value
    
    if SignalType.CLARITY in signals_by_type:
        clarity = signals_by_type[SignalType.CLARITY][0]
        profile_signals["clarity_level"] = clarity.clarity_level.name.lower()
    
    return profile_signals


═══════════════════════════════════════════════════════════════════════════════
PHASE 6: CONFIGURATION & TUNING
═══════════════════════════════════════════════════════════════════════════════

Key parameters to adjust in production:

1. SIGNAL CONFIDENCE THRESHOLD (in _extract_courses_from_signals):
   min_confidence: 0.65  # Only trust signals above this
   
   - Increase to 0.75+ for stricter filtering (fewer false positives)
   - Decrease to 0.60 for more inclusive extraction (catch weak signals)

2. CONTRADICTION PENALTY (in apply_contradiction_penalty):
   max_penalty: 0.30  # Maximum confidence drop
   base_penalty: 0.15  # Per contradiction
   
   - Increase penalty for stricter stability requirements
   - Decrease for more forgiving behavior

3. AMBIGUITY THRESHOLD (in should_address_contradiction):
   ambiguity_score > 0.60  # When to note user is unclear
   
   - Adjust based on how messy your user input is

4. CLARITY DETECTION (in detect_clarity_from_prefixes):
   Tune the prefix lists based on your user base
   - Add common slang to SLANG_NORMALIZATION
   - Add new uncertainty patterns to WEAK_SIGNAL_PREFIXES


═══════════════════════════════════════════════════════════════════════════════
TESTING INTEGRATION
═══════════════════════════════════════════════════════════════════════════════

Run the integration test:

    python backend/app/services/orchestration/integration_heavy_tasks.py

Expected output:
    
    ════════════════════════════════════════════════════════════════════════════
    TEST 1: Messy Input with Strong Contradiction Detection
    ════════════════════════════════════════════════════════════════════════════
    
    Query: idk bro maybe coding but like I suck at math lol
    
    Extracted Signals:
      - weak_math (constraint, confidence: 0.88)
      - coding (interest, confidence: 0.82)
      - weak (clarity, confidence: 0.55)
    
    Confidence Update:
      0.85 → 0.75 (penalty: 0.10)
    
    System Notes:
      - INPUT: User message is informal/messy (slang, typos)
      - SIGNALS: Strong confidence in constraint
      - CONFIDENCE: Stable (user is consistent)


═══════════════════════════════════════════════════════════════════════════════
PRODUCTION CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

Before deploying to production:

□ Run full test suite with integration test
□ Test with real messy user inputs (screenshots/logs)
□ Validate contradictions are detected correctly
□ Verify confidence penalties don't drop too low
□ Check tone layer modifications work
□ Monitor confidence scores in logs (are they reasonable?)
□ Test with profile history (are contradictions across turns detected?)
□ Verify response tone acknowledges contradictions appropriately
□ Load test: ensure extraction doesn't slow down response time
□ Fallback: what happens if profile history is empty?

Key Validation Points:

1. Signal Extraction Robustness:
   - "idk bro maybe coding" → extracts "coding" with low confidence ✓
   - "coding" + "hate coding" in same convo → detects contradiction ✓
   - Multiple goals → extractall, score by confidence ✓

2. Contradiction Detection:
   - "I like coding" then "I hate coding" → HIGH severity ✓
   - "job goal" then "entrepreneurship goal" → HIGH severity ✓
   - Weak signals from uncertain user → MODERATE severity ✓
   - No false positives → deterministic results ✓

3. Confidence Penalty:
   - Single contradiction → -0.10 to -0.15 ✓
   - Multiple contradictions → capped at -0.30 ✓
   - Stable input → no penalty ✓

4. Tone Adjustment:
   - Contradictions mentioned in response ✓
   - Tone becomes more questioning when unstable ✓
   - User can recover confidence by clarifying ✓


═══════════════════════════════════════════════════════════════════════════════
MONITORING & MAINTENANCE
═══════════════════════════════════════════════════════════════════════════════

After deployment, monitor:

1. Logging metrics:
   - [CONTRADICTION] entries in logs → how often detected?
   - Penalty values → are they reasonable?
   - Signal confidence distribution → are signals strong enough?

2. User behavior:
   - Do users respond to contradiction acknowledgments?
   - Does confidence penalty affect recommendation quality?
   - Are unstable users getting appropriate follow-ups?

3. Performance:
   - Signal extraction time per query (should be <50ms)
   - Contradiction detection time (should be <10ms)
   - Overall orchestration latency increase (should be <100ms)

4. Quality metrics:
   - Contradiction false positive rate
   - Confidence score drift over conversation
   - User satisfaction with recommendations


═══════════════════════════════════════════════════════════════════════════════
ADVANCED CUSTOMIZATION
═══════════════════════════════════════════════════════════════════════════════

Future enhancements (Phase 2):

1. ML-backed fuzzy matching (replace difflib)
2. Domain-specific contradiction detection
3. Multi-language support for signal extraction
4. User preference learning (e.g., "this user always second-guesses")
5. Integration with external knowledge bases
6. A/B testing different penalty strategies
7. Confidence recovery mechanisms (how users rebuild trust)
"""
