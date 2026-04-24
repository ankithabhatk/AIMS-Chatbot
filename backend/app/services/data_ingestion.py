"""
Data Ingestion Pipeline

Coordinates: scrape -> chunk -> embed -> store -> index
"""

import logging
from typing import List, Tuple
from app.services.scraper.playwright_scraper import scrape_aims_website_enhanced
from app.services.embeddings.embedding_service import embed_batch
from app.services.retrieval.faiss_index import get_index

logger = logging.getLogger(__name__)


def ingest_college_data() -> dict:
    """
    Full ingestion pipeline: scrape AIMS website (Playwright), chunk, embed, index
    
    Returns:
        Stats dict with counts
    """
    logger.info("🔄 Starting enhanced data ingestion pipeline...")
    
    # 1. Scrape
    docs = scrape_aims_website_enhanced()
    
    if not docs:
        logger.warning("No documents scraped")
        return {"status": "failed", "message": "No documents scraped"}
    
    logger.info(f"✅ Scraped {len(docs)} documents")
    
    # 2. Chunk
    chunks = []
    chunk_metadata = []  # (text, url, heading)
    
    from app.services.scraper.college_scraper import AIMSWebScraper
    
    for doc in docs:
        url = doc.get("url", "")
        title = doc.get("title", "")
        content = doc.get("content", "")
        
        page_chunks = AIMSWebScraper.chunk_text(content, chunk_size=600, overlap=60)
        for chunk in page_chunks:
            chunks.append(chunk)
            chunk_metadata.append((chunk, url, title))
    
    logger.info(f"✅ Created {len(chunks)} text chunks")
    
    # 3. Embed
    logger.info("Generating embeddings...")
    embeddings = embed_batch(chunks)
    logger.info(f"✅ Generated {len(embeddings)} embeddings")
    
    # 4. Index
    index = get_index()
    texts = [meta[0] for meta in chunk_metadata]
    urls = [meta[1] for meta in chunk_metadata]
    headings = [meta[2] for meta in chunk_metadata]
    
    index.add_documents(texts, embeddings, urls, headings)
    index.save()
    
    stats = index.get_stats()
    logger.info(f"✅ Ingestion complete. Stats: {stats}")
    
    return {
        "status": "success",
        "docs_scraped": len(docs),
        "chunks_created": len(chunks),
        "embeddings_generated": len(embeddings),
        "index_stats": stats
    }


def test_with_sample_data() -> dict:
    """
    For testing: add sample data without scraping real website
    
    Returns:
        Stats dict
    """
    logger.info("Loading sample data for testing...")
    
    sample_texts = [
        "AIMS College offers undergraduate and postgraduate programs in engineering, management, and sciences.",
        "Admissions are open for BTech, MSc, and MBA programs. Apply online at admissions.theaims.ac.in",
        "AIMS has excellent placement records with 95% students placed in top companies.",
        "The college has modern infrastructure including computer labs, libraries, and sports facilities.",
        "Faculty members are highly qualified with PhD degrees from leading universities.",
    ]
    
    sample_urls = ["https://www.theaims.ac.in"] * len(sample_texts)
    sample_headings = ["About AIMS", "Admissions", "Placements", "Campus", "Faculty"] 
    
    # Embed
    embeddings = embed_batch(sample_texts)
    
    # Index
    index = get_index()
    index.add_documents(sample_texts, embeddings, sample_urls, sample_headings)
    index.save()
    
    stats = index.get_stats()
    logger.info(f"✅ Sample data loaded. Stats: {stats}")
    
    return {
        "status": "success",
        "samples_added": len(sample_texts),
        "index_stats": stats
    }
