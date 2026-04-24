
import os
import sys
import asyncio
import logging

# Add the project root to sys.path
sys.path.append(os.getcwd())

# Mock environment variables if needed
os.environ["ENVIRONMENT"] = "production"

from app.services.data_ingestion import ingest_college_data

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print("Starting AIMS Data Ingestion...")
    stats = ingest_college_data()
    print(f"Ingestion complete: {stats}")
