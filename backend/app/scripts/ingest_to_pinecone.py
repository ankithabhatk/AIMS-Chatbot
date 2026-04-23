import os
import uuid
import re
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Load env vars
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

# SDK Imports
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

# -----------------------------
# CONFIG
# -----------------------------
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

INDEX_NAME = "aims-index"
DIMENSION = 1536
METRIC = "cosine"
EMBEDDING_MODEL = "text-embedding-3-small"

CHUNK_SIZE = 200  # words
CHUNK_OVERLAP = 40

VALID_COURSES = ["MBA", "BCA", "MCA", "BBA"]

INTENT_KEYWORDS = {
    "fees": ["fee", "fees", "cost", "tuition"],
    "placements": ["placement", "salary", "companies", "package"],
    "admission": ["admission", "apply", "process"],
    "eligibility": ["eligibility", "criteria", "qualification"],
    "hostel": ["hostel", "accommodation"],
}

# -----------------------------
# INIT CLIENTS
# -----------------------------
pc = Pinecone(api_key=PINECONE_API_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

# -----------------------------
# INDEX CREATION
# -----------------------------
def setup_index():
    print(f"Checking index: {INDEX_NAME}")
    if INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating index: {INDEX_NAME}")
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIMENSION,
            metric=METRIC,
            spec=ServerlessSpec(
                cloud='aws', 
                region='us-east-1' # default for free tier
            )
        )
        # Wait for index to be ready
        while not pc.describe_index(INDEX_NAME).status['ready']:
            time.sleep(1)
    
    return pc.Index(INDEX_NAME)

# -----------------------------
# TEXT CLEANING
# -----------------------------
def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# -----------------------------
# CHUNKING
# -----------------------------
def chunk_text(text):
    words = text.split()
    chunks = []
    for i in range(0, len(words), CHUNK_SIZE - CHUNK_OVERLAP):
        chunk = words[i:i + CHUNK_SIZE]
        if chunk:
            chunks.append(" ".join(chunk))
    return chunks

# -----------------------------
# INTENT DETECTION
# -----------------------------
def detect_intent(text):
    text_lower = text.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(k in text_lower for k in keywords):
            return intent
    return "general"

# -----------------------------
# PRIORITY LOGIC
# -----------------------------
def get_priority(intent):
    if intent in ["fees", "placements", "admission"]:
        return "high"
    elif intent in ["eligibility", "hostel"]:
        return "medium"
    return "low"

# -----------------------------
# EMBEDDING
# -----------------------------
def get_embedding(text):
    response = client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

# -----------------------------
# MAIN INGESTION PIPELINE
# -----------------------------
def ingest(data_path):
    print("Setting up index...")
    index = setup_index()
    
    print(f"Loading data from {data_path}...")
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to load data: {e}")
        return

    vectors = []
    total_upserted = 0

    print("Processing and generating embeddings...")
    for doc in data:
        content = clean_text(doc.get("content", ""))
        if not content:
            continue
            
        course = doc.get("course", "GENERAL")
        source = doc.get("source", "unknown")
        title = doc.get("title", "unknown")

        chunks = chunk_text(content)

        for i, chunk in enumerate(chunks):
            intent = detect_intent(chunk)
            priority = get_priority(intent)

            try:
                embedding = get_embedding(chunk)
            except Exception as e:
                print(f"Error generating embedding: {e}")
                continue

            vector = {
                "id": str(uuid.uuid4()),
                "values": embedding,
                "metadata": {
                    "text": chunk,
                    "course": course,
                    "intent": intent,
                    "sub_intent": "none",
                    "source": source,
                    "page": title,
                    "priority": priority,
                    "last_updated": str(datetime.utcnow()),
                    "keywords": [],
                    "chunk_id": f"{course}_{intent}_{i}"
                }
            }
            vectors.append(vector)

            # Batch upsert every 50 vectors
            if len(vectors) >= 50:
                print(f"Upserting batch of {len(vectors)} vectors...")
                index.upsert(vectors=vectors)
                total_upserted += len(vectors)
                vectors = []

    # Final flush
    if vectors:
        print(f"Upserting final batch of {len(vectors)} vectors...")
        index.upsert(vectors=vectors)
        total_upserted += len(vectors)

    print(f"✅ Ingestion complete. Total vectors upserted: {total_upserted}")
    
    # Validate
    stats = index.describe_index_stats()
    print(f"Index stats: {stats}")

if __name__ == "__main__":
    import sys
    # Use official knowledge test payload if available
    target_data = "/Users/maneeth/Desktop/Chat-Bot/backend/scripts/aims_browser_data.json"
    
    # Check if data file exists, if not we will use an alternative or create a dummy one
    if not os.path.exists(target_data):
        print(f"Warning: {target_data} not found. We will create a scraped_data.json placeholder.")
        # Let's write a small sample scraped payload to ingest based on user's sample
        sample_data = [
          {
            "title": "MBA Fees",
            "content": "The total MBA fee is 6 lakhs. The fees cover tuition, library access, and examination fees.",
            "source": "official_website",
            "course": "MBA"
          },
          {
             "title": "MCA Placements",
             "content": "The MCA placements are very strong. The highest salary package was 12 LPA, and the average was 6 LPA.",
             "source": "official_website",
             "course": "MCA"
          }
        ]
        with open("scraped_data.json", "w") as f:
            json.dump(sample_data, f)
        target_data = "scraped_data.json"
        
    ingest(target_data)
