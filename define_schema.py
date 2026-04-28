#!/usr/bin/env python3
"""
STEP 3: DEFINE CLEAN SCHEMA
Target structure for chatbot-ready course data
"""

import json

print("=" * 80)
print("STEP 3: DEFINE CLEAN SCHEMA")
print("=" * 80)

# ═══════════════════════════════════════════════════════════════════════════
# TARGET SCHEMA
# ═══════════════════════════════════════════════════════════════════════════

target_schema = {
    "college_name": "str - exact name from dataset",
    "location": "str - city/place where college is located",
    "college_type": "str - Government | Private | Deemed | Autonomous",
    "course_name": "str - standardized course name (BCA, BBA, MBA, M.Com, MCA, B.Com)",
    "duration_years": "int - course duration in years",
    "annual_fees_inr": "int - annual fees in Indian Rupees (single year)",
    "placement_percentage": "int - percentage of placed students (0-100)",
    "college_website": "str - college website URL (without http://)",
    "college_affiliation": "str - affiliation type (Central University, State University, Deemed, Autonomous, Affiliated)",
    "contact_phone": "str - contact phone number formatted as +91-XXXXXXXXXX"
}

print("\n📋 TARGET SCHEMA (for cleaned JSON output)")
print("─" * 80)
for field, description in target_schema.items():
    print(f"\n  {field}:")
    print(f"    {description}")

# ═══════════════════════════════════════════════════════════════════════════
# MAPPING: RAW → CLEAN
# ═══════════════════════════════════════════════════════════════════════════

print("\n\n🔄 FIELD MAPPING (Raw Dataset → Cleaned Schema)")
print("─" * 80)

mapping = {
    "college_name": {
        "source": "Name",
        "rule": "Keep as-is",
        "example": "AIMS College → AIMS College"
    },
    "location": {
        "source": "Place",
        "rule": "Keep as-is",
        "example": "Bangalore → Bangalore"
    },
    "college_type": {
        "source": "Type",
        "rule": "Map: Government|Private → Private; Government",
        "example": "Private → Private"
    },
    "course_name": {
        "source": "Course",
        "rule": "Normalize: standardize course names (all uppercase, no extra spaces)",
        "example": "BCA → BCA; B.Com → B.COM"
    },
    "duration_years": {
        "source": "Duration_Years",
        "rule": "Cast to int",
        "example": "3 → 3"
    },
    "annual_fees_inr": {
        "source": "Fees_Annual_INR",
        "rule": "Cast to int, remove any currency symbols or commas",
        "example": "50000 → 50000"
    },
    "placement_percentage": {
        "source": "Placement_Percentage",
        "rule": "Cast to int, ensure 0-100 range",
        "example": "85 → 85"
    },
    "college_website": {
        "source": "Website",
        "rule": "Remove http:// and https://, keep domain only",
        "example": "www.aimsbanglore.edu → aimsbanglore.edu"
    },
    "college_affiliation": {
        "source": "Affiliation",
        "rule": "Keep as-is",
        "example": "Autonomous → Autonomous"
    },
    "contact_phone": {
        "source": "Contact",
        "rule": "Format as +91-XXXXXXXXXX (10 digits after country code)",
        "example": "9876543210 → +91-9876543210"
    }
}

for field, mapping_info in mapping.items():
    print(f"\n  {field}:")
    print(f"    Source:   {mapping_info['source']}")
    print(f"    Rule:     {mapping_info['rule']}")
    print(f"    Example:  {mapping_info['example']}")

# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION RULES
# ═══════════════════════════════════════════════════════════════════════════

print("\n\n✅ VALIDATION RULES (after cleaning)")
print("─" * 80)

validations = [
    ("college_name", "Non-empty string", "len > 0"),
    ("location", "Non-empty string", "len > 0"),
    ("college_type", "One of: Private | Government | Deemed | Autonomous", "in allowed list"),
    ("course_name", "One of: BCA | BBA | MBA | MCA | B.COM | M.COM", "in allowed list"),
    ("duration_years", "Integer 2-4", "2 <= value <= 4"),
    ("annual_fees_inr", "Integer >= 0", "value >= 0"),
    ("placement_percentage", "Integer 0-100", "0 <= value <= 100"),
    ("college_website", "Valid domain", "regex: ^[a-z0-9]+\\.[a-z0-9]+$"),
    ("college_affiliation", "Non-empty string", "len > 0"),
    ("contact_phone", "Valid Indian phone", "regex: ^\\+91-[0-9]{10}$"),
]

for field, rule, check in validations:
    print(f"\n  {field}:")
    print(f"    Rule:  {rule}")
    print(f"    Check: {check}")

# ═══════════════════════════════════════════════════════════════════════════
# SAMPLE OUTPUT STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════

print("\n\n📦 SAMPLE CLEANED RECORD (JSON)")
print("─" * 80)

sample_record = {
    "college_name": "AIMS College",
    "location": "Bangalore",
    "college_type": "Private",
    "course_name": "BCA",
    "duration_years": 3,
    "annual_fees_inr": 50000,
    "placement_percentage": 85,
    "college_website": "aimsbanglore.edu",
    "college_affiliation": "Autonomous",
    "contact_phone": "+91-9876543210"
}

print(json.dumps(sample_record, indent=2))

# ═══════════════════════════════════════════════════════════════════════════
# OUTPUT FORMAT
# ═══════════════════════════════════════════════════════════════════════════

print("\n\n📄 OUTPUT FORMAT")
print("─" * 80)
print("""
Target file: /data/processed/courses_clean.json

Format: JSON array of objects (one object per college-course combination)

[
  {college_name, location, college_type, ...},
  {college_name, location, college_type, ...},
  ...
]

Total records: Each college-course pair = 1 record
""")

print("\n" + "=" * 80)
print("READY FOR STEP 4: DATA CLEANING")
print("=" * 80)
