#!/usr/bin/env python3
"""
STRICT DATA VALIDATION (TRACE MODE)
Find REAL issues, not assumptions
"""

import json
import random
from typing import Dict, List, Tuple

print("=" * 90)
print("STRICT DATA VALIDATION (TRACE MODE)")
print("=" * 90)

# Load data
with open("/Users/maneeth/Desktop/Chat-Bot/data/processed/courses_clean.json", "r") as f:
    data = json.load(f)

print(f"\n📊 Dataset: {len(data)} records loaded\n")

# ═══════════════════════════════════════════════════════════════════════════
# CHECK 1: SHOW 10 RANDOM RECORDS
# ═══════════════════════════════════════════════════════════════════════════

print("1️⃣  SHOW 10 RANDOM RECORDS (for manual inspection)")
print("─" * 90)

random_indices = random.sample(range(len(data)), min(10, len(data)))
sample_records = [data[i] for i in random_indices]

for i, record in enumerate(sample_records, 1):
    print(f"\n  Record {i}:")
    for key, value in record.items():
        print(f"    {key:<25} {str(value):<40}")

# ═══════════════════════════════════════════════════════════════════════════
# CHECK 2: COURSE NAME CONSISTENCY
# ═══════════════════════════════════════════════════════════════════════════

print("\n\n2️⃣  COURSE NAME CONSISTENCY CHECK")
print("─" * 90)

course_variations = {}
for record in data:
    course = record.get("course_name", "")
    if course not in course_variations:
        course_variations[course] = 0
    course_variations[course] += 1

print("\nUnique course_name values found:")
for course, count in sorted(course_variations.items()):
    print(f"  • '{course}': {count} records")

# Check for variations like "BCA" vs "B.C.A" vs "bca"
issues_course = []
expected_courses = {"BCA", "BBA", "MBA", "MCA", "BCOM", "MCOM"}

for course in course_variations.keys():
    if course not in expected_courses:
        issues_course.append(f"❌ Unexpected course name: '{course}'")
    
    # Check for case variations
    if course != course.upper():
        issues_course.append(f"⚠️  Course name not uppercase: '{course}'")
    
    # Check for punctuation
    if "." in course:
        issues_course.append(f"⚠️  Course name contains dots: '{course}'")

if issues_course:
    print("\n⚠️  COURSE NAME ISSUES FOUND:")
    for issue in issues_course:
        print(f"  {issue}")
else:
    print("\n✅ All course names are standardized")

# ═══════════════════════════════════════════════════════════════════════════
# CHECK 3: MISSING CRITICAL FIELDS
# ═══════════════════════════════════════════════════════════════════════════

print("\n\n3️⃣  MISSING FIELD CHECK (for critical fields)")
print("─" * 90)

critical_fields = ["college_name", "course_name", "annual_fees_inr", "placement_percentage"]
missing_records = {}

for idx, record in enumerate(data):
    for field in critical_fields:
        if field not in record or record[field] == "" or record[field] is None:
            if idx not in missing_records:
                missing_records[idx] = []
            missing_records[idx].append(field)

if missing_records:
    print(f"\n❌ FOUND {len(missing_records)} records with missing critical fields:")
    for idx, missing_fields in missing_records.items():
        print(f"\n  Record {idx}:")
        print(f"    Missing: {', '.join(missing_fields)}")
        print(f"    Data: {data[idx]}")
else:
    print("\n✅ All critical fields present in all records")

# ═══════════════════════════════════════════════════════════════════════════
# CHECK 4: SUSPICIOUS DUPLICATIONS
# ═══════════════════════════════════════════════════════════════════════════

print("\n\n4️⃣  DUPLICATION CHECK (same college + same course)")
print("─" * 90)

seen_combinations = {}
duplicates = []

for idx, record in enumerate(data):
    key = (record.get("college_name", ""), record.get("course_name", ""))
    if key in seen_combinations:
        duplicates.append({
            "first_idx": seen_combinations[key],
            "second_idx": idx,
            "combination": key,
            "first_record": data[seen_combinations[key]],
            "second_record": record
        })
    else:
        seen_combinations[key] = idx

if duplicates:
    print(f"\n❌ FOUND {len(duplicates)} duplicate combinations:")
    for dup in duplicates:
        print(f"\n  Same college-course pair at indices {dup['first_idx']} and {dup['second_idx']}")
        print(f"    College: {dup['combination'][0]}")
        print(f"    Course: {dup['combination'][1]}")
        
        # Show differences
        rec1 = dup["first_record"]
        rec2 = dup["second_record"]
        diffs = []
        for field in rec1.keys():
            if rec1.get(field) != rec2.get(field):
                diffs.append(f"{field}: '{rec1.get(field)}' vs '{rec2.get(field)}'")
        
        if diffs:
            print(f"    Differences: {', '.join(diffs)}")
        else:
            print(f"    ⚠️  EXACT DUPLICATE - same data")
else:
    print("\n✅ No duplicate college-course combinations found")

# ═══════════════════════════════════════════════════════════════════════════
# CHECK 5: USABILITY TEST
# ═══════════════════════════════════════════════════════════════════════════

print("\n\n5️⃣  USABILITY TEST (Can each record answer a real user question?)")
print("─" * 90)

usability_issues = []

for idx, record in enumerate(data):
    # Test: Can we answer "What are the fees for BCA at X?"
    if not record.get("college_name"):
        usability_issues.append(f"Record {idx}: Cannot identify college (missing college_name)")
    if not record.get("course_name"):
        usability_issues.append(f"Record {idx}: Cannot identify course (missing course_name)")
    if record.get("annual_fees_inr") is None or record.get("annual_fees_inr") == "":
        usability_issues.append(f"Record {idx}: Cannot answer fees question ({record.get('college_name')} {record.get('course_name')})")
    
    # Test: Can we answer "What's the placement percentage?"
    if record.get("placement_percentage") is None or record.get("placement_percentage") == "":
        usability_issues.append(f"Record {idx}: Cannot answer placement question ({record.get('college_name')} {record.get('course_name')})")
    
    # Test: Can we answer "How long is BCA?"
    if record.get("duration_years") is None or record.get("duration_years") == "":
        usability_issues.append(f"Record {idx}: Cannot answer duration question ({record.get('college_name')} {record.get('course_name')})")
    
    # Test: Fee range validation
    fees = record.get("annual_fees_inr")
    if isinstance(fees, int) and (fees < 1000 or fees > 5000000):
        usability_issues.append(f"Record {idx}: Suspicious fee value ₹{fees} ({record.get('college_name')} {record.get('course_name')})")

if usability_issues:
    print(f"\n❌ USABILITY ISSUES FOUND ({len(usability_issues)}):")
    for issue in usability_issues[:20]:  # Show first 20
        print(f"  • {issue}")
    if len(usability_issues) > 20:
        print(f"  ... and {len(usability_issues) - 20} more")
else:
    print("\n✅ All records can answer user questions")

# ═══════════════════════════════════════════════════════════════════════════
# CHECK 6: DATA TYPE CONSISTENCY
# ═══════════════════════════════════════════════════════════════════════════

print("\n\n6️⃣  DATA TYPE CONSISTENCY CHECK")
print("─" * 90)

type_issues = []

for idx, record in enumerate(data):
    # Fees should be int
    if not isinstance(record.get("annual_fees_inr"), int):
        type_issues.append(f"Record {idx}: annual_fees_inr is {type(record.get('annual_fees_inr')).__name__}, expected int")
    
    # Placement should be int
    if not isinstance(record.get("placement_percentage"), int):
        type_issues.append(f"Record {idx}: placement_percentage is {type(record.get('placement_percentage')).__name__}, expected int")
    
    # Duration should be int
    if not isinstance(record.get("duration_years"), int):
        type_issues.append(f"Record {idx}: duration_years is {type(record.get('duration_years')).__name__}, expected int")
    
    # Course name should be string
    if not isinstance(record.get("course_name"), str):
        type_issues.append(f"Record {idx}: course_name is {type(record.get('course_name')).__name__}, expected str")

if type_issues:
    print(f"\n❌ TYPE ISSUES FOUND ({len(type_issues)}):")
    for issue in type_issues[:10]:
        print(f"  • {issue}")
    if len(type_issues) > 10:
        print(f"  ... and {len(type_issues) - 10} more")
else:
    print("\n✅ All field types are correct")

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

print("\n\n" + "=" * 90)
print("VALIDATION SUMMARY")
print("=" * 90)

total_issues = len(issues_course) + len(missing_records) + len(duplicates) + len(usability_issues) + len(type_issues)

print(f"\nIssues found:")
print(f"  • Course name variations: {len(issues_course)}")
print(f"  • Missing critical fields: {len(missing_records)}")
print(f"  • Duplicate combinations: {len(duplicates)}")
print(f"  • Usability issues: {len(usability_issues)}")
print(f"  • Type inconsistencies: {len(type_issues)}")
print(f"  ─────────────────────────")
print(f"  • TOTAL ISSUES: {total_issues}")

if total_issues == 0:
    confidence = "HIGH (95%+)"
    status = "✅ READY FOR INTEGRATION"
elif total_issues <= 3:
    confidence = "MEDIUM (70%)"
    status = "⚠️  MINOR ISSUES - REVIEW BEFORE INTEGRATION"
else:
    confidence = "LOW (40%)"
    status = "❌ FIX DATA ISSUES BEFORE INTEGRATION"

print(f"\nConfidence level: {confidence}")
print(f"Status: {status}")

print("\n" + "=" * 90)
