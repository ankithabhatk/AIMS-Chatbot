"""
Heavy Task Integration - Contradiction Engine + Signal Extraction

This module shows how the contradiction detection and robust signal extraction
work together in a real orchestration pipeline.

Workflow:
    1. User input arrives
    2. Extract signals using ROBUST signal extractor (handles messy input)
    3. Compare new signals against profile history
    4. Detect contradictions using contradiction engine
    5. Apply confidence penalties
    6. Update profile with new signals
    7. Generate response that acknowledges stability/instability

Production Integration Points:
    - In orchestration engine: run_orchestration()
    - In counselor router: detect_intents()
    - In memory layer: update_student_profile()
    - In tone layer: apply_hybrid_behavior()
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

from app.services.orchestration.contradiction_engine import (
    detect_contradictions,
    apply_contradiction_penalty,
    update_confidence_with_contradictions,
    Contradiction,
)
from app.services.orchestration.signal_extractor import (
    extract_robust_signals,
    RobustSignalResult,
    Signal,
    SignalType,
    ClarityLevel,
    filter_high_confidence_signals,
    aggregate_signals_by_type,
    diagnose_extraction,
)

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# INTEGRATED SIGNAL & CONFIDENCE UPDATE FUNCTION
# ════════════════════════════════════════════════════════════════════════════

def process_user_input_with_contradiction_detection(
    query: str,
    student_profile: Dict[str, Any],
    profile_history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Main integration function: Extract signals, detect contradictions, update confidence.
    
    This is the HEAVYWEIGHT processing that runs on every message in production.
    
    Args:
        query: User input (messy, informal, etc.)
        student_profile: Current student profile state
        profile_history: List of past profile states
    
    Returns:
        {
            "signals": RobustSignalResult,
            "contradictions": List[Contradiction],
            "confidence_update": {
                "old_confidence": float,
                "new_confidence": float,
                "penalty": float,
                "is_stable": bool,
            },
            "profile_update": Dict,  # New profile state
            "system_notes": List[str],  # Internal notes for tone layer
        }
    
    Example:
        Input: user_query = "idk bro maybe coding but like I suck at math lol"
        
        Output:
            {
                "signals": {
                    "signals": [
                        Signal(type=interest, value=coding, confidence=0.82),
                        Signal(type=constraint, value=weak_math, confidence=0.88),
                        Signal(type=clarity, value=weak),
                    ]
                },
                "contradictions": [
                    Contradiction(type=goal_conflict, severity=0.75)
                ],
                "confidence_update": {
                    "old_confidence": 0.85,
                    "new_confidence": 0.70,  # penalty applied
                    "penalty": 0.15,
                    "is_stable": False,
                },
                "profile_update": {
                    "interests": "coding",
                    "math_ability": "weak",
                    "clarity": "weak",
                },
                "system_notes": [
                    "User's interest signal is weak (idk, maybe)",
                    "Contradiction detected: goal shifted",
                ],
            }
    """
    
    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 1: ROBUST SIGNAL EXTRACTION
    # ─────────────────────────────────────────────────────────────────────────
    
    logger.info(f"[INTEGRATION] Processing: {query[:60]}...")
    
    # Extract all signals from messy input
    extraction_result = extract_robust_signals(query)
    
    logger.debug(f"[EXTRACTION] {diagnose_extraction(extraction_result)}")
    
    # Group signals by type
    signals_by_type = aggregate_signals_by_type(extraction_result.signals)
    
    # Convert to profile-compatible format
    new_signals = _signals_to_profile_format(extraction_result, signals_by_type)
    
    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 2: CONTRADICTION DETECTION
    # ─────────────────────────────────────────────────────────────────────────
    
    contradictions = detect_contradictions(profile_history, new_signals)
    
    if contradictions:
        logger.warning(
            f"[CONTRADICTION] Detected {len(contradictions)} contradiction(s): "
            f"{[c.type.value for c in contradictions]}"
        )
        for contradiction in contradictions:
            logger.info(f"  → {contradiction.description}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 3: CONFIDENCE UPDATE
    # ─────────────────────────────────────────────────────────────────────────
    
    current_confidence = student_profile.get("confidence", 0.5)
    
    # Apply contradiction penalties
    new_confidence, penalty = apply_contradiction_penalty(
        current_confidence,
        contradictions,
        max_penalty=0.30
    )
    
    confidence_update = {
        "old_confidence": current_confidence,
        "new_confidence": new_confidence,
        "penalty": penalty,
        "is_stable": penalty <= 0.10,
    }
    
    logger.info(
        f"[CONFIDENCE] {current_confidence:.2f} → {new_confidence:.2f} "
        f"(penalty: -{penalty:.3f})"
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 4: PROFILE UPDATE
    # ─────────────────────────────────────────────────────────────────────────
    
    # Merge new signals into profile
    updated_profile = _merge_signals_into_profile(student_profile, new_signals)
    updated_profile["confidence"] = new_confidence
    updated_profile["last_updated"] = datetime.now().isoformat()
    
    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 5: SYSTEM NOTES (for tone layer)
    # ─────────────────────────────────────────────────────────────────────────
    
    system_notes = _generate_system_notes(
        extraction_result,
        contradictions,
        confidence_update
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # RETURN INTEGRATED RESULT
    # ─────────────────────────────────────────────────────────────────────────
    
    return {
        "signals": extraction_result.to_dict(),
        "contradictions": [c.to_dict() for c in contradictions],
        "confidence_update": confidence_update,
        "profile_update": updated_profile,
        "system_notes": system_notes,
        "timestamp": datetime.now().isoformat(),
    }


# ════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def _signals_to_profile_format(
    extraction_result: RobustSignalResult,
    signals_by_type: Dict
) -> Dict[str, Any]:
    """
    Convert extracted signals to profile-compatible format.
    
    Maps Signal objects to profile keys.
    """
    profile_signals = {}
    
    # Extract primary interest
    if SignalType.INTEREST in signals_by_type:
        interests = signals_by_type[SignalType.INTEREST]
        if interests:
            # Combine interests with their confidence
            best_interest = max(interests, key=lambda s: s.confidence)
            profile_signals["interests"] = best_interest.value
            profile_signals["interest_confidence"] = best_interest.confidence
    
    # Extract constraint
    if SignalType.CONSTRAINT in signals_by_type:
        constraints = signals_by_type[SignalType.CONSTRAINT]
        if constraints:
            best_constraint = max(constraints, key=lambda s: s.confidence)
            # Map constraint type to profile key
            if "weak_math" in best_constraint.value:
                profile_signals["math_ability"] = "weak"
            profile_signals["constraint"] = best_constraint.value
            profile_signals["constraint_confidence"] = best_constraint.confidence
    
    # Extract goal
    if SignalType.GOAL in signals_by_type:
        goals = signals_by_type[SignalType.GOAL]
        if goals:
            best_goal = max(goals, key=lambda s: s.confidence)
            profile_signals["goal"] = best_goal.value
            profile_signals["goal_confidence"] = best_goal.confidence
    
    # Extract clarity
    if SignalType.CLARITY in signals_by_type:
        clarity = signals_by_type[SignalType.CLARITY]
        if clarity:
            clarity_level = clarity[0].clarity_level
            profile_signals["clarity_level"] = clarity_level.name.lower()
    
    # Add overall messiness indicator
    profile_signals["input_quality"] = "messy" if extraction_result.is_messy else "clean"
    profile_signals["ambiguity_score"] = extraction_result.ambiguity_score
    
    return profile_signals


def _merge_signals_into_profile(
    student_profile: Dict[str, Any],
    new_signals: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge new extracted signals into existing profile.
    
    Overwrites old values with new ones, but preserves unrelated fields.
    """
    updated = student_profile.copy()
    
    # Merge signal fields
    for key, value in new_signals.items():
        if value is not None:  # Don't overwrite with None
            updated[key] = value
    
    return updated


def _generate_system_notes(
    extraction_result: RobustSignalResult,
    contradictions: List[Contradiction],
    confidence_update: Dict[str, Any]
) -> List[str]:
    """
    Generate internal notes for the tone layer.
    
    These notes help the tone layer adjust response appropriately.
    """
    notes = []
    
    # Input quality notes
    if extraction_result.is_messy:
        notes.append("INPUT: User message is informal/messy (slang, typos)")
    
    if extraction_result.ambiguity_score > 0.6:
        notes.append("AMBIGUITY: User is unclear or uncertain about preferences")
    
    # Signal extraction notes
    content_signals = [s for s in extraction_result.signals if s.type != SignalType.CLARITY]
    
    if not content_signals:
        notes.append("SIGNALS: No clear signals extracted")
    else:
        high_conf = [s for s in content_signals if s.confidence >= 0.80]
        if high_conf:
            types = [s.type.value for s in high_conf]
            notes.append(f"SIGNALS: Strong confidence in {', '.join(types)}")
        
        low_conf = [s for s in content_signals if s.confidence < 0.60]
        if low_conf:
            notes.append("SIGNALS: Some signals are weak")
    
    # Contradiction notes
    if contradictions:
        severe = [c for c in contradictions if c.severity > 0.80]
        moderate = [c for c in contradictions if 0.60 < c.severity <= 0.80]
        
        if severe:
            notes.append(f"CONTRADICTION: {len(severe)} severe (address explicitly)")
        
        if moderate:
            notes.append(f"CONTRADICTION: {len(moderate)} moderate (may mention)")
    
    # Confidence notes
    if not confidence_update["is_stable"]:
        notes.append(f"CONFIDENCE: Dropped by {confidence_update['penalty']:.1%} (show concern)")
    else:
        notes.append("CONFIDENCE: Stable (user is consistent)")
    
    return notes


# ════════════════════════════════════════════════════════════════════════════
# INTEGRATION POINTS: HOW TO USE IN ORCHESTRATION ENGINE
# ════════════════════════════════════════════════════════════════════════════

def example_orchestration_integration():
    """
    Example: How to integrate into orchestration engine.
    
    In: backend/app/services/orchestration/engine.py
    
    Add to run_orchestration() function:
    
        # HEAVY TASK INTEGRATION: Contradiction detection + robust signal extraction
        from app.services.orchestration.signal_extractor import extract_robust_signals
        from app.services.orchestration.contradiction_engine import detect_contradictions
        
        # Extract signals from messy user input
        signals_result = extract_robust_signals(query)
        
        # Get student profile history
        student_id = context.get("student_id")
        profile_history = get_student_profile_history(student_id)  # From memory service
        
        # Integrate: detect contradictions
        integration_result = process_user_input_with_contradiction_detection(
            query=query,
            student_profile=current_profile,
            profile_history=profile_history
        )
        
        # Use results downstream
        new_confidence = integration_result["confidence_update"]["new_confidence"]
        new_signals = integration_result["signals"]
        contradictions = integration_result["contradictions"]
        system_notes = integration_result["system_notes"]
        
        # Update profile
        updated_profile = integration_result["profile_update"]
        save_student_profile(student_id, updated_profile)
        
        # Pass notes to tone layer
        context["system_notes"] = system_notes
        context["contradictions"] = contradictions
        context["ambiguity_score"] = new_signals["ambiguity_score"]
        
        # Continue with rest of orchestration...
        response = run_counselor_pipeline(query, context)
    """
    pass


def example_tone_layer_integration():
    """
    Example: How to use in tone/behavior layer.
    
    In: backend/app/services/counselor/persona.py
    
    Modify: apply_hybrid_behavior()
    
    Add:
        # Check for contradictions
        contradictions = context.get("contradictions", [])
        
        # Adjust tone based on stability
        if contradictions:
            confidence_update = context.get("confidence_update", {})
            if not confidence_update.get("is_stable"):
                # User is unstable → acknowledge gently
                response = add_acknowledgment(response, contradictions)
                # Use more questioning tone
                tone = "supportive_questioning"
            else:
                # User is stable → continue normally
                tone = "confident_guiding"
        
        # Generate contradiction acknowledgment
        from app.services.orchestration.contradiction_engine import generate_contradiction_response
        
        if contradictions and should_address_contradiction(contradictions):
            strongest_contradiction = contradictions[0]  # Most severe
            ack = generate_contradiction_response(strongest_contradiction)
            response = f"{ack}\n\n{response}"
    """
    pass


# ════════════════════════════════════════════════════════════════════════════
# TESTING & VALIDATION
# ════════════════════════════════════════════════════════════════════════════

def test_integration_example():
    """
    Test the full integration with example inputs.
    """
    # Example 1: Messy input with signal extraction
    print("\n" + "="*80)
    print("TEST 1: Messy Input with Strong Contradiction Detection")
    print("="*80)
    
    query_1 = "idk bro maybe coding but like I suck at math lol"
    
    profile = {
        "interests": "coding",
        "goal": "job",
        "confidence": 0.85,
    }
    
    history = [
        {
            "interests": "coding",
            "goal": "job",
            "turn": 1,
        }
    ]
    
    result = process_user_input_with_contradiction_detection(query_1, profile, history)
    
    print(f"\nQuery: {query_1}")
    print(f"\nExtracted Signals:")
    for signal in result["signals"]["signals"][:3]:
        print(f"  - {signal['value']} ({signal['type']}, confidence: {signal['confidence']:.2f})")
    
    print(f"\nConfidence Update:")
    print(f"  {result['confidence_update']['old_confidence']:.2f} → "
          f"{result['confidence_update']['new_confidence']:.2f} "
          f"(penalty: {result['confidence_update']['penalty']:.3f})")
    
    print(f"\nSystem Notes:")
    for note in result["system_notes"]:
        print(f"  - {note}")
    
    # Example 2: Direct contradiction
    print("\n" + "="*80)
    print("TEST 2: Clear Contradiction Detection")
    print("="*80)
    
    query_2 = "Actually, I hate coding. I want to do business instead."
    
    profile = {
        "interests": "coding",
        "goal": "tech_job",
        "confidence": 0.90,
    }
    
    history = [
        {
            "interests": "coding",
            "goal": "tech_job",
            "turn": 1,
        }
    ]
    
    result = process_user_input_with_contradiction_detection(query_2, profile, history)
    
    print(f"\nQuery: {query_2}")
    print(f"\nContradictions Detected:")
    for contradiction in result["contradictions"]:
        print(f"  - {contradiction['type']}: '{contradiction['previous']}' → '{contradiction['current']}'")
        print(f"    Severity: {contradiction['severity']:.2f}")
    
    print(f"\nConfidence Penalty: {result['confidence_update']['penalty']:.3f}")
    print(f"New Confidence: {result['confidence_update']['new_confidence']:.2f}")


if __name__ == "__main__":
    test_integration_example()
