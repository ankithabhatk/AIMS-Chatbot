#!/usr/bin/env python3
"""Test Q8 routing"""

query = "I like coding but I also want good salary and I'm not great at studies"
q = query.lower()

# Constraint signals from counselor_handler.py
constraint_signals = [
    "weak in", "not good at", "bad at", "struggle with",
    "poor at", "not great at", "difficulty with",
    "but i", "however i", "although i",
    "confused", "not sure", "don't know",
]

print(f"Query: {query}")
print(f"Lowercase: {q}")
print()

for signal in constraint_signals:
    if signal in q:
        print(f"✅ MATCH: '{signal}' found in query")
        print(f"   Position: {q.index(signal)}")
        break
else:
    print("❌ NO MATCH: No constraint signal found")

# Also check exploratory signals
exploratory_signals = [
    "i like", "i love", "i enjoy", "i'm interested in",
    "i want to", "i'm good at", "my passion",
    "help me choose",
    "what should i", "which is better for me", "recommend",
    "best for me", "suitable for me", "right for me",
    "career", "future", "job opportunities",
]

print()
for signal in exploratory_signals:
    if signal in q:
        print(f"✅ EXPLORATORY MATCH: '{signal}' found in query")
        break
