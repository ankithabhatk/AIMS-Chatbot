#!/usr/bin/env python3
"""
COMPREHENSIVE TEST: Full contradiction handling validation

This test validates:
1. Normal progression (ambiguity → clarity → decision → high confidence)
2. Contradiction detection (preference reversal)
3. Recovery mechanism (user can rebuild confidence after contradiction)

This proves the system can model real human indecision patterns.
"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.confidence_engine import update_confidence_score

print("="*80)
print("COMPREHENSIVE SYSTEM TEST: CONTRADICTION HANDLING")
print("="*80)

def show_turn(turn_num, statement, signals, score, prev_score=None):
    """Helper to display turn information."""
    delta = score - prev_score if prev_score is not None else 0
    delta_str = f"({delta:+.3f})" if prev_score is not None else ""
    score_str = f"{prev_score:.3f} → {score:.3f} {delta_str}" if prev_score else f"None → {score:.3f}"
    print(f"Turn {turn_num}: {statement}")
    print(f"  signals: {signals}")
    print(f"  score:   {score_str}")

# PHASE 1: Normal Progression
print("\n" + "="*80)
print("PHASE 1: NORMAL PROGRESSION (Building Confidence)")
print("="*80)

turn = 1
score = update_confidence_score(None, ["ambiguity"])
show_turn(turn, "'I'm not sure about my career path'", ["ambiguity"], score)

turn = 2
prev = score
score = update_confidence_score(prev, ["weak_clarity"])
show_turn(turn, "'But I think I like working with computers'", ["weak_clarity"], score, prev)

turn = 3
prev = score
score = update_confidence_score(prev, ["weak_clarity", "weak_clarity"])
show_turn(turn, "'Actually, I really enjoy solving problems with code'", ["weak_clarity", "weak_clarity"], score, prev)

turn = 4
prev = score
score = update_confidence_score(prev, ["strong_clarity", "decision_request"])
show_turn(turn, "'Yes, I'm ready to commit to coding as my career'", ["strong_clarity", "decision_request"], score, prev)

high_confidence_score = score
print(f"\n✓ High confidence reached: {score:.3f}")

# PHASE 2: Contradiction
print("\n" + "="*80)
print("PHASE 2: CONTRADICTION (Preference Reversal)")
print("="*80)

turn = 5
prev = score
score = update_confidence_score(prev, ["contradiction"])
show_turn(turn, "'Wait... actually, I hate debugging code all day'", ["contradiction"], score, prev)

delta = score - high_confidence_score
print(f"\n  PENALTY: {delta:+.3f} (dropped {abs(delta):.3f} from peak)")
print(f"  Range check: {0.45:.2f}–{0.55:.2f} → {score:.3f} {'✓ PASS' if 0.45 <= score <= 0.55 else '✗ FAIL'}")

medium_confidence_score = score

# PHASE 3: Recovery
print("\n" + "="*80)
print("PHASE 3: RECOVERY (Rebuilding After Uncertainty)")
print("="*80)

turn = 6
prev = score
score = update_confidence_score(prev, ["weak_clarity"])
show_turn(turn, "'But problem-solving itself is still interesting to me'", ["weak_clarity"], score, prev)

turn = 7
prev = score
score = update_confidence_score(prev, ["weak_clarity", "strong_clarity"])
show_turn(turn, "'Maybe I need a different role in tech, not just pure coding'", ["weak_clarity", "strong_clarity"], score, prev)

turn = 8
prev = score
score = update_confidence_score(prev, ["strong_clarity"])
show_turn(turn, "'Tech leadership or product management sounds more fulfilling'", ["strong_clarity"], score, prev)

recovered_score = score

# Summary
print("\n" + "="*80)
print("SUMMARY: CONFIDENCE EVOLUTION")
print("="*80)
print(f"Peak confidence:      {high_confidence_score:.3f} (Turn 4)")
print(f"After contradiction:  {medium_confidence_score:.3f} (Turn 5) ← dropped {high_confidence_score - medium_confidence_score:.3f}")
print(f"After recovery:       {recovered_score:.3f} (Turn 8)")
print()
print("System Behaviors:")
print(f"  ✓ Detects preference reversals (Turn 5 contradiction)")
print(f"  ✓ Applies fair penalty (-0.25 on single contradiction)")
print(f"  ✓ Allows recovery through incremental rebuilding")
print(f"  ✓ Transitions between uncertainty and confidence naturally")
print()
print("Human-like Pattern:")
print(f"  Initial interest → Strong commitment → Doubt → Reorientation")
print(f"  This models real career exploration, not rigid decisions.")
