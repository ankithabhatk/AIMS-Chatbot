#!/usr/bin/env python3
"""
STEP 2: DATASET INSPECTION
Analyze structure, missing values, duplicates, and identify useful fields
"""

import pandas as pd
import os

print("=" * 80)
print("STEP 2: DATA INSPECTION")
print("=" * 80)

# Load dataset
dataset_path = "/Users/maneeth/Desktop/Chat-Bot/data/raw/indian_colleges.csv"
df = pd.read_csv(dataset_path)

print(f"\n📊 Dataset loaded from: {dataset_path}")
print(f"📈 Shape: {df.shape[0]} rows × {df.shape[1]} columns\n")

# ═══════════════════════════════════════════════════════════════════════════
# 1. COLUMNS
# ═══════════════════════════════════════════════════════════════════════════
print("1️⃣  COLUMNS")
print("─" * 80)
print("\nColumn names and types:")
for col in df.columns:
    dtype = df[col].dtype
    sample = df[col].iloc[0]
    print(f"  • {col:<25} Type: {str(dtype):<10} Sample: {sample}")

# ═══════════════════════════════════════════════════════════════════════════
# 2. MISSING VALUES
# ═══════════════════════════════════════════════════════════════════════════
print("\n\n2️⃣  MISSING VALUES")
print("─" * 80)
missing = df.isnull().sum()
print("\nMissing values per column:")
for col, count in missing.items():
    pct = (count / len(df)) * 100
    status = "✅ OK" if count == 0 else f"⚠️  {count} ({pct:.1f}%)"
    print(f"  • {col:<25} {status}")

# ═══════════════════════════════════════════════════════════════════════════
# 3. DUPLICATES
# ═══════════════════════════════════════════════════════════════════════════
print("\n\n3️⃣  DUPLICATES")
print("─" * 80)
dup_exact = df.duplicated().sum()
dup_by_name_course = df[['Name', 'Course']].duplicated().sum()
print(f"  • Exact duplicates: {dup_exact}")
print(f"  • Same college/course: {dup_by_name_course}")
if dup_exact > 0 or dup_by_name_course > 0:
    print("  ⚠️  Duplicates found")

# ═══════════════════════════════════════════════════════════════════════════
# 4. UNIQUE VALUES PER FIELD
# ═══════════════════════════════════════════════════════════════════════════
print("\n\n4️⃣  UNIQUE VALUES")
print("─" * 80)
for col in ['Name', 'Place', 'Type', 'Course', 'Affiliation']:
    unique_count = df[col].nunique()
    values = df[col].unique()[:5]
    print(f"  • {col:<25} {unique_count} unique values")
    print(f"    Samples: {', '.join(map(str, values))}")

# ═══════════════════════════════════════════════════════════════════════════
# 5. NUMERIC FIELDS STATISTICS
# ═══════════════════════════════════════════════════════════════════════════
print("\n\n5️⃣  NUMERIC STATISTICS")
print("─" * 80)
numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
for col in numeric_cols:
    print(f"\n  {col}:")
    print(f"    Min: {df[col].min()}")
    print(f"    Max: {df[col].max()}")
    print(f"    Mean: {df[col].mean():.2f}")
    print(f"    Missing: {df[col].isnull().sum()}")

# ═══════════════════════════════════════════════════════════════════════════
# 6. FIRST 5 ROWS (PREVIEW)
# ═══════════════════════════════════════════════════════════════════════════
print("\n\n6️⃣  DATA PREVIEW (First 5 rows)")
print("─" * 80)
print(df.head().to_string())

# ═══════════════════════════════════════════════════════════════════════════
# 7. USEFULNESS ASSESSMENT
# ═══════════════════════════════════════════════════════════════════════════
print("\n\n7️⃣  USEFULNESS FOR CHATBOT")
print("─" * 80)

assessment = {
    "Name": "✅ CRITICAL - identify college",
    "Place": "✅ USEFUL - location context",
    "Type": "✅ USEFUL - college category",
    "Course": "✅ CRITICAL - course identification",
    "Duration_Years": "✅ USEFUL - course length",
    "Fees_Annual_INR": "✅ CRITICAL - answer fee queries",
    "Placement_Percentage": "✅ CRITICAL - answer placement queries",
    "Contact": "⚠️  PARTIAL - phone number only, needs formatting",
    "Website": "✅ USEFUL - provide college website",
    "Affiliation": "✅ USEFUL - college authority type",
}

for col, assessment_text in assessment.items():
    print(f"  • {col:<25} {assessment_text}")

# ═══════════════════════════════════════════════════════════════════════════
# 8. FIELDS TO REMOVE
# ═══════════════════════════════════════════════════════════════════════════
print("\n\n8️⃣  DATA CLEANING RECOMMENDATIONS")
print("─" * 80)
print("\n❌ Fields to REMOVE (not chatbot-relevant):")
print("   None - all fields are useful\n")
print("✅ Fields to KEEP:")
print("   Name, Place, Type, Course, Duration_Years, Fees_Annual_INR,")
print("   Placement_Percentage, Contact, Website, Affiliation\n")
print("🔧 Fields to NORMALIZE:")
print("   • Course names (standardize formatting)")
print("   • Fees (handle currency symbols)")
print("   • Contact (clean phone numbers)")

print("\n" + "=" * 80)
print("READY FOR STEP 3: DEFINE CLEAN SCHEMA")
print("=" * 80)
