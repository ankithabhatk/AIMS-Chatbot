import os
from typing import List, Dict, Optional
from pinecone import Pinecone
import logging

logger = logging.getLogger(__name__)

# Initialize Pinecone
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "aims-index")

try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
except Exception as e:
    logger.error(f"Failed to initialize Pinecone: {e}")
    index = None

def query_pinecone(query_embedding: List[float], top_k: int = 5, course: Optional[str] = None, intent: Optional[str] = None) -> List[Dict]:
    """Query Pinecone with metadata filtering and safety checks."""
    if index is None:
        logger.warning("Pinecone index not initialized. Returning empty results.")
        return []

    # Apply metadata filters
    filter_dict = {}
    if course and course != "GENERAL":
        filter_dict["course"] = course
    if intent and intent != "general":
        filter_dict["intent"] = intent

    try:
        response = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict if filter_dict else None
        )
    except Exception as e:
        logger.error(f"Pinecone query failed: {e}")
        return []

    # Extract clean results and apply score threshold
    clean_results = []
    for match in response.get("matches", []):
        score = match.get("score", 0)
        
        # SAFETY: discard low confidence results
        if score < 0.6:
            continue
            
        metadata = match.get("metadata", {})
        clean_results.append({
            "text": metadata.get("text", ""),
            "score": score,
            "course": metadata.get("course", "unknown"),
            "intent": metadata.get("intent", "unknown")
        })

    print(f"Pinecone matches: {len(clean_results)}")
    return clean_results
