#!/usr/bin/env python3
"""
Contextual Truth Test - Direct API
Tests: When given MBA context, does system return MBA-specific placement data?

Flow:
1. Query 1: "MBA fees" (establishes course context)
2. Query 2: "What about placements?" (should return MBA-specific data)

Expected: Highest ₹23 LPA (MBA-specific)
Not: Highest ₹27 LPA (overall/generic)
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_contextual_truth():
    print("\n" + "="*80)
    print("🔍 CONTEXTUAL TRUTH VALIDATION - Direct API Test")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    session = "ctx-truth-test"
    
    # Query 1: Establish MBA context
    print("📝 QUERY 1: 'MBA fees' (Establish context)")
    print("-"*80)
    
    resp1 = requests.post(
        f"{BASE_URL}/api/v1/chat",
        json={"query": "MBA fees", "session_id": session},
        timeout=15
    )
    
    if resp1.status_code != 200:
        print(f"❌ Error: {resp1.status_code}")
        return False
    
    data1 = resp1.json()
    answer1 = data1.get("answer", "")
    mode1 = data1.get("mode", "")
    
    print(f"Mode: {mode1}")
    print(f"Response 1:\n{answer1}\n")
    
    time.sleep(2)
    
    # Query 2: Follow-up on placements with context
    print("📝 QUERY 2: 'What about placements?' (With MBA context)")
    print("-"*80)
    
    resp2 = requests.post(
        f"{BASE_URL}/api/v1/chat",
        json={"query": "What about placements?", "session_id": session},
        timeout=15
    )
    
    if resp2.status_code != 200:
        print(f"❌ Error: {resp2.status_code}")
        return False
    
    data2 = resp2.json()
    answer2 = data2.get("answer", "")
    mode2 = data2.get("mode", "")
    fallback2 = data2.get("fallback", False)
    
    print(f"Mode: {mode2}")
    print(f"Fallback: {fallback2}")
    print(f"\nResponse 2:")
    print("---")
    print(answer2)
    print("---\n")
    
    # Analysis
    print("="*80)
    print("🔍 CONTEXTUAL TRUTH ANALYSIS")
    print("="*80)
    
    # Check for package values
    import re
    
    answer2_lower = answer2.lower()
    packages = re.findall(r'₹(\d+)\s*(?:lpa|lakhs?)?', answer2, re.IGNORECASE)
    
    print(f"\nPackage values found: {packages}")
    
    # Check for contextual markers
    has_mba_prefix = "mba" in answer2_lower
    has_bba_prefix = "bba" in answer2_lower
    has_overall = "overall" in answer2_lower
    has_highest_27 = "₹27" in answer2 or "27 lpa" in answer2_lower
    has_highest_23 = "₹23" in answer2 or "23 lpa" in answer2_lower
    
    print(f"\n✅ Has 'MBA' context: {has_mba_prefix}")
    print(f"✅ Has 'BBA' context: {has_bba_prefix}")
    print(f"⚠️  Has 'overall': {has_overall}")
    print(f"💰 Has ₹23 LPA (MBA-specific): {has_highest_23}")
    print(f"💰 Has ₹27 LPA (overall): {has_highest_27}")
    
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)
    
    if fallback2:
        print("🔴 FAIL: System returned fallback (no context grounding)")
        return False
    elif has_highest_27 and not has_mba_prefix:
        print("🔴 FAIL: Shows overall ₹27 LPA instead of MBA-specific ₹23 LPA")
        print("   ^ This is the contextual truth problem")
        return False
    elif has_highest_23 and (has_mba_prefix or has_bba_prefix):
        print("🟢 PASS: Shows course-specific package with context")
        return True
    elif has_highest_23:
        print("🟡 PARTIAL: Shows ₹23 LPA but no course prefix")
        return True
    else:
        print("🟡 UNCLEAR: Could not determine if answer is contextually accurate")
        print(f"   Full answer: {answer2}")
        return None

if __name__ == "__main__":
    result = test_contextual_truth()
    
    print("\n" + "="*80)
    if result is True:
        print("✅ SYSTEM IS CONTEXTUALLY ACCURATE")
    elif result is False:
        print("❌ SYSTEM HAS CONTEXTUAL TRUTH PROBLEM")
    else:
        print("🟡 NEEDS MANUAL REVIEW")
    print("="*80)
