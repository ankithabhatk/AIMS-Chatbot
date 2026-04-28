#!/usr/bin/env python3
"""
STEP 4: DATA CLEANING
Transform raw CSV → clean JSON according to schema
"""

import pandas as pd
import json
import re
from typing import Dict, List, Any

print("=" * 80)
print("STEP 4: DATA CLEANING")
print("=" * 80)

# ═══════════════════════════════════════════════════════════════════════════
# LOAD RAW DATA
# ═══════════════════════════════════════════════════════════════════════════

raw_path = "/Users/maneeth/Desktop/Chat-Bot/data/raw/indian_colleges.csv"
df = pd.read_csv(raw_path)

print(f"\n📥 Loaded: {raw_path}")
print(f"   {len(df)} rows")

# ═══════════════════════════════════════════════════════════════════════════
# CLEANING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def clean_course_name(course: str) -> str:
    """Normalize course names to uppercase without dots"""
    return course.strip().upper().replace(".", "")

def clean_website(website: str) -> str:
    """Remove http:// and https://, keep domain"""
    website = website.strip().lower()
    website = website.replace("https://", "").replace("http://", "").replace("www.", "")
    return website

def clean_phone(phone: Any) -> str:
    """Format phone as +91-XXXXXXXXXX"""
    phone_str = str(phone).strip()
    # Extract digits only
    digits = re.sub(r"[^0-9]", "", phone_str)
    # Take last 10 digits (in case country code is included)
    digits = digits[-10:] if len(digits) >= 10 else digits
    if len(digits) == 10:
        return f"+91-{digits}"
    return phone_str  # Return as-is if invalid

def validate_record(record: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate cleaned record against schema
    Returns: (is_valid, error_messages)
    """
    errors = []
    
    # Required fields
    required_fields = ["college_name", "location", "course_name", "annual_fees_inr", 
                      "placement_percentage", "college_website", "contact_phone"]
    for field in required_fields:
        if not record.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Type checks
    if not isinstance(record.get("duration_years"), int):
        errors.append("duration_years must be integer")
    if not isinstance(record.get("annual_fees_inr"), int):
        errors.append("annual_fees_inr must be integer")
    if not isinstance(record.get("placement_percentage"), int):
        errors.append("placement_percentage must be integer")
    
    # Range checks
    if record.get("duration_years"):
        if not (2 <= record["duration_years"] <= 4):
            errors.append(f"duration_years out of range: {record['duration_years']}")
    
    if record.get("annual_fees_inr"):
        if record["annual_fees_inr"] < 0:
            errors.append(f"annual_fees_inr negative: {record['annual_fees_inr']}")
    
    if record.get("placement_percentage"):
        if not (0 <= record["placement_percentage"] <= 100):
            errors.append(f"placement_percentage out of range: {record['placement_percentage']}")
    
    # Enum checks
    valid_courses = ["BCA", "BBA", "MBA", "MCA", "BCOM", "MCOM"]
    if record.get("course_name") not in valid_courses:
        errors.append(f"Invalid course_name: {record.get('course_name')} (allowed: {valid_courses})")
    
    valid_types = ["PRIVATE", "GOVERNMENT", "DEEMED", "AUTONOMOUS"]
    if record.get("college_type", "").upper() not in valid_types:
        errors.append(f"Invalid college_type: {record.get('college_type')}")
    
    # Format checks
    if record.get("contact_phone"):
        if not re.match(r"^\+91-[0-9]{10}$", record["contact_phone"]):
            errors.append(f"Invalid phone format: {record['contact_phone']}")
    
    return len(errors) == 0, errors

# ═══════════════════════════════════════════════════════════════════════════
# TRANSFORM RAW → CLEAN
# ═══════════════════════════════════════════════════════════════════════════

print("\n🔄 Cleaning data...")
cleaned_records = []
errors_by_row = {}

for idx, row in df.iterrows():
    record = {
        "college_name": row["Name"].strip(),
        "location": row["Place"].strip(),
        "college_type": row["Type"].strip().upper(),
        "course_name": clean_course_name(row["Course"]),
        "duration_years": int(row["Duration_Years"]),
        "annual_fees_inr": int(row["Fees_Annual_INR"]),
        "placement_percentage": int(row["Placement_Percentage"]),
        "college_website": clean_website(row["Website"]),
        "college_affiliation": row["Affiliation"].strip(),
        "contact_phone": clean_phone(row["Contact"]),
    }
    
    is_valid, errors = validate_record(record)
    
    if is_valid:
        cleaned_records.append(record)
    else:
        errors_by_row[idx] = (record, errors)

# ═══════════════════════════════════════════════════════════════════════════
# REPORT
# ═══════════════════════════════════════════════════════════════════════════

print(f"\n✅ Valid records: {len(cleaned_records)}")
print(f"❌ Invalid records: {len(errors_by_row)}")

if errors_by_row:
    print("\n⚠️  Invalid records details:")
    for idx, (record, errors) in errors_by_row.items():
        print(f"\n  Row {idx}: {record.get('college_name')} - {record.get('course_name')}")
        for error in errors:
            print(f"    • {error}")

# ═══════════════════════════════════════════════════════════════════════════
# SAVE CLEANED DATA
# ═══════════════════════════════════════════════════════════════════════════

output_path = "/Users/maneeth/Desktop/Chat-Bot/data/processed/courses_clean.json"

with open(output_path, "w") as f:
    json.dump(cleaned_records, f, indent=2)

print(f"\n✅ Cleaned data saved: {output_path}")
print(f"   Total records: {len(cleaned_records)}")

# ═══════════════════════════════════════════════════════════════════════════
# STATISTICS
# ═══════════════════════════════════════════════════════════════════════════

print("\n📊 CLEANED DATA STATISTICS")
print("─" * 80)

# By course
print("\nRecords by course:")
course_counts = {}
for rec in cleaned_records:
    course = rec["course_name"]
    course_counts[course] = course_counts.get(course, 0) + 1

for course, count in sorted(course_counts.items()):
    print(f"  • {course}: {count}")

# By college type
print("\nRecords by college type:")
type_counts = {}
for rec in cleaned_records:
    ctype = rec["college_type"]
    type_counts[ctype] = type_counts.get(ctype, 0) + 1

for ctype, count in sorted(type_counts.items()):
    print(f"  • {ctype}: {count}")

# Fee ranges
print("\nFee distribution (Annual):")
fees = [r["annual_fees_inr"] for r in cleaned_records]
print(f"  • Min: ₹{min(fees):,}")
print(f"  • Max: ₹{max(fees):,}")
print(f"  • Avg: ₹{sum(fees) // len(fees):,}")

# Placement
print("\nPlacement distribution:")
placements = [r["placement_percentage"] for r in cleaned_records]
print(f"  • Min: {min(placements)}%")
print(f"  • Max: {max(placements)}%")
print(f"  • Avg: {sum(placements) // len(placements)}%")

print("\n" + "=" * 80)
print("READY FOR STEP 5: VALIDATION")
print("=" * 80)
