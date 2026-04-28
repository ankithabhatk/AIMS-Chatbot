#!/usr/bin/env python3
"""
Minimal debug script to trace ONE query through the pipeline
Query: "I want to do BCA"
"""

import sys
import json
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.counselor.entity_extractor import extract_entities
from app.services.counselor.stage_controller import detect_stage
from app.services.orchestration.engine import run_counselor_pipeline
from app.services.counselor.memory import get_student_profile, SESSION_MEMORY

# Setup
session_id = "debug_session_001"
query = "I want to do BCA"
context = {}

print("=" * 80)
print("DEBUG: Single Query Pipeline Trace")
print("=" * 80)
print(f"\n🔍 QUERY: {query}")
print(f"🔍 SESSION: {session_id}\n")

# STAGE 1: Entity Extraction
print("─" * 80)
print("STAGE 1: ENTITY EXTRACTION")
print("─" * 80)
try:
    entities = extract_entities(query)
    print(f"✓ Entities extracted: {json.dumps(entities, indent=2)}")
except Exception as e:
    print(f"✗ ERROR in extract_entities: {e}")
    entities = {}

# STAGE 2: Stage Controller
print("\n" + "─" * 80)
print("STAGE 2: STAGE CONTROLLER (direct call)")
print("─" * 80)
try:
    # Stage controller needs context with entities
    test_context = {
        "entities": entities,
        "query": query
    }
    stage_result = detect_stage(query, test_context)
    print(f"✓ Stage detected (raw): {stage_result}")
    print(f"  Type: {type(stage_result)}")
except Exception as e:
    print(f"✗ ERROR in detect_stage: {e}")
    import traceback
    traceback.print_exc()
    stage_result = None

# STAGE 3: Run Full Pipeline
print("\n" + "─" * 80)
print("STAGE 3: FULL PIPELINE (run_counselor_pipeline)")
print("─" * 80)
try:
    result = run_counselor_pipeline(query, session_id=session_id, context=context)
    print(f"✓ Pipeline result: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"✗ ERROR in run_counselor_pipeline: {e}")
    import traceback
    traceback.print_exc()
    result = {}

# STAGE 4: Check Memory State
print("\n" + "─" * 80)
print("STAGE 4: MEMORY STATE AFTER QUERY")
print("─" * 80)
try:
    profile = get_student_profile(session_id)
    print(f"✓ Memory profile: {json.dumps(profile, indent=2)}")
except Exception as e:
    print(f"✗ ERROR in get_student_profile: {e}")
    import traceback
    traceback.print_exc()

# SUMMARY
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\n1️⃣  Entities extracted? {bool(entities and entities.get('courses'))}")
if entities:
    print(f"   → courses: {entities.get('courses', [])}")

print(f"\n2️⃣  Stage detected (direct call)? {stage_result is not None}")
if stage_result:
    if isinstance(stage_result, str):
        print(f"   → stage (string): {stage_result}")
    elif isinstance(stage_result, dict):
        print(f"   → stage: {stage_result.get('stage')}")
        print(f"   → should_lock: {stage_result.get('should_lock')}")

print(f"\n3️⃣  Pipeline executed? {bool(result)}")
if result:
    print(f"   → mode: {result.get('mode')}")
    print(f"   → response: {result.get('response', 'N/A')[:100]}...")

print(f"\n4️⃣  Memory persisted? {bool(profile)}")
if profile:
    print(f"   → locked_course: {profile.get('locked_course')}")
    print(f"   → courses: {profile.get('courses', [])}")

print("\n" + "=" * 80)
print("END DEBUG")
print("=" * 80)
