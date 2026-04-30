#!/usr/bin/env python3
"""
CONSOLE TEST HARNESS: Messy Input Testing

Run real messy inputs through the full pipeline:
1. Extract signals from query
2. Evolve confidence score
3. Show tone response

This is where we find what breaks.
"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.conversation_memory import extract_confidence_signals, extract_user_profile, UserProfile
from app.services.confidence_engine import update_confidence_score, map_score_to_category
from app.services.counselor.persona import apply_persona_layer

# Messy test inputs
MESSY_INPUTS = [
    "idk bro what to do",
    "maybe coding but I suck at math",
    "coding seems okay but I want money fast",
    "actually coding is boring",
    "maybe business idk",
    "I like business but parents want engineering",
    "what should I choose",
    "I'm confused between coding and business",
    "coding is fun but no jobs",
    "I hate studying tbh",
    "tech is cool but also scary",
    "really not sure about this whole thing",
    "okay I'm going to do coding",
    "wait actually I want business instead",
    "both sound interesting to me",
]

print("="*80)
print("CONSOLE TEST HARNESS: MESSY INPUT PIPELINE TEST")
print("="*80)
print()

# Track profile across conversation
profile = UserProfile()
confidence_score = None

for turn, query in enumerate(MESSY_INPUTS, 1):
    print(f"Turn {turn}: {query}")
    
    # Step 1: Extract signals
    signals = extract_confidence_signals(query, profile)
    print(f"  signals:     {signals}")
    
    # Step 2: Update confidence
    prev_score = confidence_score
    confidence_score = update_confidence_score(confidence_score, signals)
    category = map_score_to_category(confidence_score)
    
    # Step 3: Show score movement
    if prev_score is not None:
        delta = confidence_score - prev_score
        delta_str = f"({delta:+.3f})"
        print(f"  confidence:  {prev_score:.3f} → {confidence_score:.3f} {delta_str}")
    else:
        print(f"  confidence:  None → {confidence_score:.3f}")
    
    print(f"  category:    {category}")
    
    # Step 4: Extract user profile for context
    user_signals = extract_user_profile(query, profile)
    
    # Update profile for next turn
    if user_signals.get("interests"):
        profile.interests.update(user_signals["interests"])
    if user_signals.get("goals"):
        profile.goals.update(user_signals["goals"])
    if user_signals.get("constraints"):
        profile.constraints.update(user_signals["constraints"])
    
    # Step 5: Show what we extracted
    if user_signals.get("interests"):
        print(f"  interests:   {user_signals['interests']}")
    if user_signals.get("goals"):
        print(f"  goals:       {user_signals['goals']}")
    if user_signals.get("constraints"):
        print(f"  constraints: {user_signals['constraints']}")
    
    print()

print("="*80)
print("PIPELINE SUMMARY")
print("="*80)
print(f"Total turns: {len(MESSY_INPUTS)}")
print(f"Final confidence: {confidence_score:.3f}")
print(f"Final category: {map_score_to_category(confidence_score)}")
print()
print("Profile state:")
print(f"  Interests collected: {profile.interests}")
print(f"  Goals collected: {profile.goals}")
print(f"  Constraints collected: {profile.constraints}")
print()

print("="*80)
print("KEY OBSERVATIONS")
print("="*80)
print("1. Did confidence move like a human (gradual ups, sharp downs)?")
print("2. Were contradictions detected when user changed preferences?")
print("3. Did uncertainty increase when user expressed doubt?")
print("4. Did profile capture multi-interests correctly?")
print()
print("Check the signals column above for patterns.")
