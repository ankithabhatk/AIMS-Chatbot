#!/usr/bin/env python3
"""
FAISS Re-Index from Scraped Pages

Loads scraped content → embeds → updates FAISS index
Replaces old noisy index with clean content

Usage:
    python scripts/reindex.py --scraped data/scraped_pages.json --rebuild
"""

import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def load_scraped_pages(input_file: str) -> list:
    """Load scraped pages from JSON"""
    with open(input_file) as f:
        return json.load(f)


def prepare_chunks(pages: list) -> list:
    """Extract all chunks with metadata"""
    chunks = []
    
    for page in pages:
        url = page.get("url", "")
        title = page.get("heading") or page.get("title", "")
        
        for chunk_text in page.get("chunks", []):
            if not chunk_text or len(chunk_text) < 30:
                continue
            
            chunks.append({
                "text": chunk_text,
                "url": url,
                "heading": title,
            })
    
    logger.info(f"Prepared {len(chunks)} chunks from {len(pages)} pages")
    return chunks


def build_faiss_index(chunks: list, embed_func) -> tuple:
    """Build FAISS index from chunks"""
    if not chunks:
        logger.error("No chunks to index")
        return None, []
    
    embeddings = []
    metadatas = []
    
    for i, chunk in enumerate(chunks):
        if i % 10 == 0:
            logger.info(f"Embedding chunk {i}/{len(chunks)}...")
        
        try:
            emb = embed_func(chunk["text"])
            embeddings.append(emb)
            metadatas.append({
                "full_text": chunk["text"],
                "url": chunk["url"],
                "heading": chunk.get("heading", ""),
            })
        except Exception as e:
            logger.warning(f"Embed error: {e}")
            continue
    
    if not embeddings:
        logger.error("No embeddings generated")
        return None, []
    
    embeddings = np.array(embeddings).astype("float32")
    faiss.normalize_L2(embeddings)
    
    import faiss
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    
    logger.info(f"Built index with {index.ntotal} vectors")
    return index, metadatas


def save_index(index, metadatas, output_dir: str):
    """Save FAISS index and metadata"""
    os.makedirs(output_dir, exist_ok=True)
    
    index_path = os.path.join(output_dir, "index.faiss")
    meta_path = os.path.join(output_dir, "metadata.json")
    
    import faiss
    faiss.write_index(index, index_path)
    
    with open(meta_path, "w") as f:
        json.dump(metadatas, f, indent=2)
    
    logger.info(f"Saved index to {index_path}")
    logger.info(f"Saved metadata to {meta_path}")


def main():
    parser = argparse.ArgumentParser(description="FAISS Re-Index from Scraped Pages")
    parser.add_argument("--scraped", default="data/scraped_pages.json", help="Scraped pages JSON")
    parser.add_argument("--output", default="data/faiss_index", help="Output directory")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild index from scratch")
    args = parser.parse_args()
    
    if not os.path.exists(args.scraped):
        logger.error(f"Scraped file not found: {args.scraped}")
        logger.info("Run scrape_pages.py first")
        return
    
    # Load pages
    pages = load_scraped_pages(args.scraped)
    logger.info(f"Loaded {len(pages)} scraped pages")
    
    if not pages:
        logger.error("No pages loaded")
        return
    
    # Prepare chunks
    chunks = prepare_chunks(pages)
    
    # Load embedding model
    logger.info("Loading embedding model...")
    try:
        from app.services.embeddings.embedding_service import load_embedding_model
        model = load_embedding_model()
        embed_func = lambda text: model.encode([text])[0]
        logger.info("Embedding model loaded")
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return
    
    # Build index
    logger.info("Building FAISS index...")
    index, metadatas = build_faiss_index(chunks, embed_func)
    
    if index is None:
        return
    
    # Save
    save_index(index, metadatas, args.output)
    
    logger.info(f"✅ Complete! Index has {index.ntotal} documents")


if __name__ == "__main__":
    main()