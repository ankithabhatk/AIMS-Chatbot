#!/usr/bin/env python3
"""
Full pipeline debug for B.Com fees
"""

import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.orchestration.engine import execute_orchestration, extract_entities, parse_query
from app.services.structured_knowledge import get_structured_response

query = "bcom fees"

print("\n" + "="*80)
print("🔍 FULL DEBUG TRACE - B.Com Fees Query")
print("="*80 + "\n")

# Step 1: Parse
parsed = parse_query(query)
print(f"1. PARSE:")
print(f"   Query: '{query}'")
print(f"   Intents: {parsed.intents}")
print(f"   Entities: {parsed.entities}\n")

# Step 2: Structured knowledge check
structured = get_structured_response(query)
print(f"2. STRUCTURED KNOWLEDGE:")
if structured:
    print(f"   Found! Intent: {structured.get('intent')}")
    print(f"   Answer: {structured.get('answer', '')[:100]}...")
else:
    print(f"   Not found (returns None)\n")

# Step 3: Full orchestration
print(f"\n3. ORCHESTRATION:")
result = execute_orchestration(query)
print(f"   Mode: {result.mode}")
print(f"   Confidence: {result.confidence}")
print(f"   Fallback: {result.fallback}")
print(f"   Answer: {result.answer[:150]}...\n")

print("="*80)
