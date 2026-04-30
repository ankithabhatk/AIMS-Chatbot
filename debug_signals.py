#!/usr/bin/env python3
"""Debug signal extraction"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.conversation_memory import extract_confidence_signals

test_queries = [
    "I like coding",
    "I really want to do this",
    "Yes, I'm decided",
    "confusing vs confused",
]

for q in test_queries:
    signals = extract_confidence_signals(q)
    print(f"'{q}' → {signals}")
