import sys
import os
import json
import numpy as np

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.retrieval.faiss_index import get_index
from app.services.embeddings.embedding_service import embed_batch

def ingest():
    print("Loading supplemental knowledge...")
    with open("backend/app/data/supplemental_knowledge.json", "r") as f:
        data = json.load(f)
    
    texts = [item["text"] for item in data]
    urls = [item["url"] for item in data]
    headings = [item["heading"] for item in data]
    
    # Metadata in faiss_index.py expected format is handled by add_documents
    # which also adds course and category if we pass them.
    # Wait, add_documents only takes urls and headings.
    # I should check if I can pass more.
    
    print(f"Embedding {len(texts)} documents...")
    embeddings = embed_batch(texts)
    
    print("Updating FAISS index...")
    index = get_index()
    index.add_documents(texts, embeddings, urls=urls, headings=headings)
    
    # Manually add the extra metadata fields if needed, 
    # but add_documents does its own metadata creation.
    # Let's see if we can patch it to include course/category.
    # In faiss_index.py, add_documents creates metadata with text, url, heading.
    
    index.save()
    print("Done!")

if __name__ == "__main__":
    ingest()
