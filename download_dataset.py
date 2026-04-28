#!/usr/bin/env python3
"""
STEP 1: CONTROLLED DATA PIPELINE
Download Indian Colleges Dataset from Kaggle
"""

import os
import subprocess
import sys

print("=" * 70)
print("STEP 1: DATASET DOWNLOAD")
print("=" * 70)

# Ensure Kaggle API is installed
try:
    import kaggle
except ImportError:
    print("❌ Kaggle API not installed")
    print("Install with: pip install kaggle")
    sys.exit(1)

# Check Kaggle credentials
kaggle_config = os.path.expanduser("~/.kaggle/kaggle.json")
if not os.path.exists(kaggle_config):
    print("❌ Kaggle API credentials not found at ~/.kaggle/kaggle.json")
    print("\nTo set up:")
    print("1. Go to https://www.kaggle.com/account/settings/api")
    print("2. Click 'Create New API Token'")
    print("3. Save to ~/.kaggle/kaggle.json")
    print("4. chmod 600 ~/.kaggle/kaggle.json")
    sys.exit(1)

# Dataset details
DATASET = "krishakbhatnagar/indian-colleges-data"
OUTPUT_DIR = "/Users/maneeth/Desktop/Chat-Bot/data/raw"

print(f"\n📥 Downloading: {DATASET}")
print(f"📁 Destination: {OUTPUT_DIR}\n")

try:
    # Download dataset
    os.system(f"kaggle datasets download -d {DATASET} -p {OUTPUT_DIR} --unzip")
    
    print("\n✅ Download complete")
    print(f"📁 Check files in: {OUTPUT_DIR}")
    
    # List files
    print("\n📋 Files downloaded:")
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            fpath = os.path.join(OUTPUT_DIR, f)
            size = os.path.getsize(fpath) / 1024  # KB
            print(f"  - {f} ({size:.1f} KB)")
    
except Exception as e:
    print(f"❌ Download failed: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("READY FOR STEP 2: DATA INSPECTION")
print("=" * 70)
