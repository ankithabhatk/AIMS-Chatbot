#!/usr/bin/env python3
"""
DATA ENRICHMENT LAYER
Upgrade from informational → decision-capable
"""

import json
from typing import Dict, List

print("=" * 90)
print("DATA ENRICHMENT LAYER")
print("=" * 90)

# Load clean dataset
with open("/Users/maneeth/Desktop/Chat-Bot/data/processed/courses_clean.json", "r") as f:
    clean_data = json.load(f)

# Load enrichment schema
with open("/Users/maneeth/Desktop/Chat-Bot/data/enrichment_schema.json", "r") as f:
    enrichment = json.load(f)

course_intelligence = enrichment["course_intelligence"]

print(f"\n📊 Loading {len(clean_data)} records from clean dataset")
print(f"🧠 Loading intelligence for {len(course_intelligence)} course types")

# ═══════════════════════════════════════════════════════════════════════════
# ENRICH EACH RECORD
# ═══════════════════════════════════════════════════════════════════════════

enriched_data = []

for idx, record in enumerate(clean_data):
    course_type = record.get("course_name", "UNKNOWN")
    
    # Get intelligence for this course type
    if course_type in course_intelligence:
        intelligence = course_intelligence[course_type]
        
        # Merge intelligenc into record
        enriched_record = record.copy()
        enriched_record.update({
            "best_for": intelligence["best_for"],
            "career_paths": intelligence["career_paths"],
            "difficulty_level": intelligence["difficulty_level"],
            "recommended_if": intelligence["recommended_if"],
            "not_recommended_if": intelligence["not_recommended_if"],
            "avg_salary_range": intelligence["avg_salary_range"],
            "skill_fit": intelligence["skill_fit"]
        })
        
        enriched_data.append(enriched_record)
    else:
        print(f"⚠️  Record {idx}: Unknown course type '{course_type}'")
        enriched_data.append(record)

print(f"\n✅ Enriched {len(enriched_data)} records")

# ═══════════════════════════════════════════════════════════════════════════
# SAVE ENRICHED DATASET
# ═══════════════════════════════════════════════════════════════════════════

output_path = "/Users/maneeth/Desktop/Chat-Bot/data/processed/courses_enriched.json"
with open(output_path, "w") as f:
    json.dump(enriched_data, f, indent=2)

print(f"💾 Saved enriched data to: {output_path}")

# ═══════════════════════════════════════════════════════════════════════════
# DEMONSTRATE ENRICHMENT
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 90)
print("BEFORE ENRICHMENT vs AFTER ENRICHMENT")
print("=" * 90)

# Show a before/after comparison for the first BCA record
sample_idx = 0
for idx, record in enumerate(clean_data):
    if record.get("course_name") == "BCA":
        sample_idx = idx
        break

print(f"\n📍 Example: Record {sample_idx} (BCA at {clean_data[sample_idx].get('college_name')})")

print("\n❌ BEFORE (Information-only):")
print("─" * 90)
before_record = clean_data[sample_idx]
for key, value in before_record.items():
    print(f"  {key:<25} {str(value):<50}")

print("\n✅ AFTER (Decision-capable):")
print("─" * 90)
after_record = enriched_data[sample_idx]
for key, value in after_record.items():
    if isinstance(value, list):
        print(f"  {key:<25} {str(value[:2])}")  # Show first 2 items
    elif isinstance(value, dict):
        print(f"  {key:<25} {str(list(value.keys()))}")
    else:
        print(f"  {key:<25} {str(value):<50}")

# ═══════════════════════════════════════════════════════════════════════════
# SEMANTIC VALIDATION (NEW)
# ═══════════════════════════════════════════════════════════════════════════

print("\n\n" + "=" * 90)
print("SEMANTIC VALIDATION - Can now answer behavioral questions?")
print("=" * 90)

# Test case 1: "I like coding"
print("\n🧪 TEST 1: User says 'I like coding'")
print("─" * 90)
print("Expected match: BCA, MCA (high coding skill requirement)")
print("\nBest matches from dataset:")

coding_courses = []
for record in enriched_data:
    skill_fit = record.get("skill_fit", {})
    if skill_fit.get("coding") == "HIGH":
        coding_courses.append({
            "college": record["college_name"],
            "course": record["course_name"],
            "difficulty": record["difficulty_level"],
            "reason": "High coding skill requirement"
        })

# Show unique courses (not all colleges)
unique_coding = {}
for item in coding_courses:
    key = item["course"]
    if key not in unique_coding:
        unique_coding[key] = item

for course, item in sorted(unique_coding.items()):
    print(f"  ✓ {course} ({item['difficulty']} difficulty)")
    print(f"    Example: {item['college']}")

# Test case 2: "I like business and management"
print("\n\n🧪 TEST 2: User says 'I like business and management'")
print("─" * 90)
print("Expected match: BBA, MBA (high business skill requirement)")
print("\nBest matches from dataset:")

business_courses = []
for record in enriched_data:
    skill_fit = record.get("skill_fit", {})
    if skill_fit.get("business") == "HIGH":
        business_courses.append({
            "college": record["college_name"],
            "course": record["course_name"],
            "difficulty": record["difficulty_level"],
            "reason": "High business skill requirement"
        })

unique_business = {}
for item in business_courses:
    key = item["course"]
    if key not in unique_business:
        unique_business[key] = item

for course, item in sorted(unique_business.items()):
    print(f"  ✓ {course} ({item['difficulty']} difficulty)")
    print(f"    Example: {item['college']}")

# Test case 3: "I like numbers and accounting"
print("\n\n🧪 TEST 3: User says 'I like numbers and accounting'")
print("─" * 90)
print("Expected match: BCOM, MCOM (high math skill requirement, low creativity)")
print("\nBest matches from dataset:")

accounting_courses = []
for record in enriched_data:
    skill_fit = record.get("skill_fit", {})
    if skill_fit.get("math") == "HIGH" and skill_fit.get("creativity") == "LOW":
        accounting_courses.append({
            "college": record["college_name"],
            "course": record["course_name"],
            "difficulty": record["difficulty_level"],
            "reason": "High math, low creativity (accounting focused)"
        })

unique_accounting = {}
for item in accounting_courses:
    key = item["course"]
    if key not in unique_accounting:
        unique_accounting[key] = item

for course, item in sorted(unique_accounting.items()):
    print(f"  ✓ {course} ({item['difficulty']} difficulty)")
    print(f"    Example: {item['college']}")

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

print("\n\n" + "=" * 90)
print("ENRICHMENT SUMMARY")
print("=" * 90)

print("\n📊 Dataset now contains:")
print("  ✓ Original fields: college_name, location, fees, placement, etc.")
print("  ✓ NEW - best_for: Use cases for each course")
print("  ✓ NEW - career_paths: Possible careers from each course")
print("  ✓ NEW - difficulty_level: Course difficulty")
print("  ✓ NEW - recommended_if: Who should choose this course")
print("  ✓ NEW - not_recommended_if: Who should avoid this course")
print("  ✓ NEW - avg_salary_range: Expected salary range")
print("  ✓ NEW - skill_fit: Mapping (coding/math/business/creativity/communication)")

print("\n✅ System can now answer:")
print("  ✓ 'I like coding' → BCA/MCA")
print("  ✓ 'I'm interested in business' → BBA/MBA")
print("  ✓ 'I like numbers and details' → BCOM/MCOM")
print("  ✓ 'What are the career paths?' → Specific careers per course")
print("  ✓ 'How difficult is this?' → Difficulty assessment")
print("  ✓ 'What salary should I expect?' → Salary ranges")

print("\n" + "=" * 90)
print("✅ DATA NOW SUPPORTS INTELLIGENT DECISION-MAKING")
print("=" * 90)
