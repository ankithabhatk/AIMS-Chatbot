"""
Main Data Ingestion Orchestration Script

Pipeline:
URL → Scrape → Clean → Chunk → Embed → Dedup → Supabase → FAISS Index
"""

import logging
import asyncio
import json
import sys
from typing import List, Dict
from datetime import datetime
import uuid

# Add parent to path
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.scraper.web_scraper import WebScraper
from app.services.data_cleaning import TextCleaner, SmartChunker, chunk_documents
from app.services.embeddings.embed_pipeline import EmbeddingPipeline
from app.services.retrieval.faiss_builder import build_faiss_index_from_embeddings
from app.services.database.supabase_client import SupabaseClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    """Complete data ingestion orchestrator"""
    
    def __init__(self):
        self.scraper = WebScraper(max_depth=2, delay=0.5)
        self.cleaner = TextCleaner()
        self.chunker = SmartChunker()
        self.embeddings = EmbeddingPipeline()
        self.db = SupabaseClient()
        
        self.stats = {
            'scraped_pages': 0,
            'cleaned_documents': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
            'stored_documents': 0,
            'failed_documents': 0,
            'duplicates_skipped': 0
        }
    
    async def run(self, url: str, source: str = "college_website") -> Dict:
        """
        Execute full ingestion pipeline
        
        Args:
            url: Website URL to scrape
            source: Source identifier (e.g., 'aims_website')
        
        Returns:
            Ingestion results summary
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting data ingestion pipeline")
        logger.info(f"URL: {url}, Source: {source}")
        logger.info(f"{'='*60}\n")
        
        try:
            # Step 1: Scrape
            logger.info("STEP 1: Web Scraping")
            logger.info("-" * 40)
            scraped = await self._scrape_website(url)
            
            # Step 2: Clean
            logger.info("\nSTEP 2: Text Cleaning")
            logger.info("-" * 40)
            cleaned = await self._clean_documents(scraped)
            
            # Step 3: Chunk
            logger.info("\nSTEP 3: Intelligent Chunking")
            logger.info("-" * 40)
            chunks = await self._chunk_documents(cleaned)
            
            # Step 4: Embed
            logger.info("\nSTEP 4: Generate Embeddings")
            logger.info("-" * 40)
            embeddings, metadata, chunk_ids = await self._embed_chunks(chunks)
            
            # Step 5: Dedup & Store
            logger.info("\nSTEP 5: Deduplication & Supabase Storage")
            logger.info("-" * 40)
            stored_docs = await self._store_in_supabase(
                embeddings, metadata, chunk_ids, source
            )
            
            # Step 6: Build Index
            logger.info("\nSTEP 6: Build FAISS Index")
            logger.info("-" * 40)
            await self._build_faiss_index(stored_docs, embeddings)
            
            # Summary
            logger.info(f"\n{'='*60}")
            logger.info("INGESTION COMPLETE")
            logger.info(f"{'='*60}")
            logger.info(self._format_summary())
            
            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats
            }
        
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats
            }
    
    async def _scrape_website(self, url: str) -> List[Dict]:
        """Scrape website and return raw documents"""
        logger.info(f"Scraping: {url}")
        
        documents = self.scraper.scrape_website(url)
        self.stats['scraped_pages'] = len(documents)
        
        logger.info(f"✓ Scraped {len(documents)} pages")
        for doc in documents[:3]:
            logger.info(f"  - {doc['title'][:60]}... ({len(doc['content'])} chars)")
        if len(documents) > 3:
            logger.info(f"  ... and {len(documents)-3} more")
        
        return documents
    
    async def _clean_documents(self, documents: List[Dict]) -> List[Dict]:
        """Clean scraped documents"""
        logger.info(f"Cleaning {len(documents)} documents")
        
        cleaned = []
        for doc in documents:
            cleaned_doc = {
                'title': doc.get('title', ''),
                'content': self.cleaner.clean(doc.get('content', '')),
                'url': doc.get('url', '')
            }
            cleaned.append(cleaned_doc)
        
        self.stats['cleaned_documents'] = len(cleaned)
        logger.info(f"✓ Cleaned {len(cleaned)} documents")
        
        return cleaned
    
    async def _chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """Chunk documents into 400-600 token pieces"""
        logger.info(f"Chunking {len(documents)} documents")
        
        chunks = chunk_documents(
            documents,
            target_tokens=500,
            min_tokens=300,
            max_tokens=700,
            overlap_tokens=75
        )
        
        self.stats['chunks_created'] = len(chunks)
        
        logger.info(f"✓ Created {len(chunks)} chunks")
        stats = self._chunk_statistics(chunks)
        logger.info(f"  - Avg tokens per chunk: {stats['avg_tokens']:.0f}")
        logger.info(f"  - Token range: {stats['min_tokens']}-{stats['max_tokens']}")
        
        return chunks
    
    async def _embed_chunks(self, chunks: List[Dict]) -> tuple:
        """Generate embeddings for chunks"""
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        texts = [chunk['content'] for chunk in chunks]
        embeddings = self.embeddings.embed_batch(texts)
        
        metadata = [
            {
                'url': chunk['url'],
                'heading': chunk.get('heading', ''),
                'chunk_index': chunk.get('chunk_index', 0),
                'tokens': chunk.get('tokens', 0)
            }
            for chunk in chunks
        ]
        
        chunk_ids = [
            f"{chunk['url']}#{chunk.get('chunk_index', 0)}"
            for chunk in chunks
        ]
        
        self.stats['embeddings_generated'] = len(embeddings)
        logger.info(f"✓ Generated {len(embeddings)} embeddings")
        logger.info(f"  - Shape: {embeddings.shape}")
        logger.info(f"  - Type: {embeddings.dtype}")
        
        return embeddings.tolist(), metadata, chunk_ids
    
    async def _store_in_supabase(
        self,
        embeddings: List[List[float]],
        metadata: List[Dict],
        chunk_ids: List[str],
        source: str
    ) -> List[str]:
        """Store chunks in Supabase with deduplication"""
        logger.info(f"Storing {len(embeddings)} documents in Supabase")
        
        stored_docs = []
        
        for embedding, meta, chunk_id in zip(embeddings, metadata, chunk_ids):
            try:
                # Check if already exists (dedup)
                # Note: This is a simple check - production would use vector similarity
                existing = await self.db.document_store.get_all_documents()
                if any(d.get('chunk_id') == chunk_id for d in existing):
                    self.stats['duplicates_skipped'] += 1
                    continue
                
                # Create document record
                doc_id = str(uuid.uuid4())
                
                # Store in Supabase
                result = await self.db.document_store.store_document(
                    id=doc_id,
                    content=meta,  # Store metadata as content for now
                    url=meta['url'],
                    heading=meta['heading'],
                    chunk_index=meta['chunk_index'],
                    source=source,
                    tokens=meta['tokens']
                )
                
                stored_docs.append(doc_id)
                self.stats['stored_documents'] += 1
            
            except Exception as e:
                logger.warning(f"Failed to store document: {e}")
                self.stats['failed_documents'] += 1
                continue
        
        logger.info(f"✓ Stored {len(stored_docs)} documents")
        logger.info(f"  - Duplicates skipped: {self.stats['duplicates_skipped']}")
        logger.info(f"  - Failed: {self.stats['failed_documents']}")
        
        return stored_docs
    
    async def _build_faiss_index(
        self,
        doc_ids: List[str],
        embeddings: List[List[float]]
    ) -> None:
        """Build FAISS index from embeddings"""
        logger.info(f"Building FAISS index for {len(doc_ids)} documents")
        
        metadata = [{'doc_id': doc_id} for doc_id in doc_ids]
        
        index = build_faiss_index_from_embeddings(
            embeddings=embeddings,
            documents=metadata,
            doc_ids=doc_ids
        )
        
        logger.info(f"✓ FAISS index built and saved")
        logger.info(f"  - Total vectors: {index.index.ntotal}")
        logger.info(f"  - Index path: {index.index_path}")
    
    def _chunk_statistics(self, chunks: List[Dict]) -> Dict:
        """Calculate chunk statistics"""
        tokens = [chunk.get('tokens', 0) for chunk in chunks]
        return {
            'total_chunks': len(chunks),
            'avg_tokens': sum(tokens) / len(tokens) if tokens else 0,
            'min_tokens': min(tokens) if tokens else 0,
            'max_tokens': max(tokens) if tokens else 0
        }
    
    def _format_summary(self) -> str:
        """Format ingestion summary"""
        lines = [
            f"\nPages scraped:       {self.stats['scraped_pages']}",
            f"Documents cleaned:   {self.stats['cleaned_documents']}",
            f"Chunks created:      {self.stats['chunks_created']}",
            f"Embeddings:          {self.stats['embeddings_generated']}",
            f"Stored in Supabase:  {self.stats['stored_documents']}",
            f"Duplicates skipped:  {self.stats['duplicates_skipped']}",
            f"Failed:              {self.stats['failed_documents']}",
        ]
        return "\n".join(lines)


async def main():
    """Main entry point"""
    pipeline = DataIngestionPipeline()
    
    # Ingest AIMS website
    result = await pipeline.run(
        url="https://www.theaims.ac.in",
        source="aims_website"
    )
    
    # Save result
    with open('/tmp/ingest_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"\nResult saved to /tmp/ingest_result.json")
    
    return 0 if result['success'] else 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
