#!/usr/bin/env python3
"""
Simple trace: Is profile being passed correctly?
"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.conversation_memory import extract_confidence_signals, UserProfile
from app.services.confidence_engine import update_confidence_score, _is_reinforcing_pivot

# Test directly with manual profile
profile = UserProfile()
profile.interests = ["coding"]

query = "I actually feel coding is right for me"

print(f"Query: {query}")
print(f"Profile: {profile}")
print(f"Profile.interests: {profile.interests}")
print()

# Check pivot logic directly
print("Direct pivot logic check:")
result = _is_reinforcing_pivot(query, profile)
print(f"  _is_reinforcing_pivot(query, profile) = {result}")
print()

# Now test with update_confidence_score
signals = ["pivot", "weak_clarity"]
prev_score = 0.4

print("Calling update_confidence_score:")
print(f"  prev_score={prev_score}")
print(f"  signals={signals}")
print(f"  query={query}")
print(f"  profile={profile}")
print()

new_score = update_confidence_score(prev_score, signals, query=query, profile=profile)

print(f"Result:")
print(f"  New score: {new_score:.3f}")
print(f"  Delta: {new_score - prev_score:+.3f}")
print()

# What SHOULD happen:
# - weak_clarity: +0.20
# - pivot: should be skipped (reinforcing)
# - raw_delta = 0.20
# - After smoothing, maybe ~0.50?

print(f"Expected delta without penalty: +0.200")
print(f"Actual delta: {new_score - prev_score:+.3f}")

if (new_score - prev_score) > 0.15:
    print("✓ Profile IS being used correctly")
else:
    print("❌ Profile might NOT be passed, or pivot penalty still applied")
