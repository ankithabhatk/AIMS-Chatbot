"""
Minimal Data Ingestion Pipeline (SYNCHRONOUS, LOCAL-ONLY)

Pipeline:
Scrape → Clean → Chunk → Embed → FAISS Index → Save Locally

No async, no database — just local validation.
"""

import logging
import json
import sys
import os
from typing import List, Dict, Tuple
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scraper.web_scraper import WebScraper
from app.services.scraper.playwright_scraper import scrape_aims_website_enhanced
from app.services.data_cleaning import TextCleaner, SmartChunker, chunk_documents
from app.services.embeddings.embed_pipeline import EmbeddingPipeline
from app.services.retrieval.faiss_builder import build_faiss_index_from_embeddings
from app.services.improved_content_filter import ImprovedContentFilter

try:
    from app.services.database.supabase_vector_store import SupabaseVectorStore
except ImportError:
    SupabaseVectorStore = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    """Minimal, testable data ingestion pipeline with dual storage (FAISS + Supabase)"""
    
    def __init__(self):
        self.scraper = WebScraper(max_depth=3, delay=0.5)  # Fallback static scraper
        self.use_playwright = True  # Use JS-aware scraper as primary
        self.cleaner = TextCleaner()
        self.chunker = SmartChunker()
        self.embeddings = EmbeddingPipeline()
        
        # Initialize Supabase vector store (parallel, optional)
        try:
            self.supabase_store = SupabaseVectorStore()
            self.use_supabase = True
            logger.info("ℹ️  Supabase vector store initialized (dual storage enabled)")
        except Exception as e:
            self.supabase_store = None
            self.use_supabase = False
            logger.warning(f"⚠️  Supabase not available, using FAISS only: {e}")
        
        self.stats = {
            'scraped_pages': 0,
            'cleaned_documents': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
            'faiss_saved': False,
            'supabase_stored': 0,
            'supabase_failed': 0
        }
    
    def run(self, url: str = "https://www.theaims.ac.in") -> Dict:
        """Execute full ingestion pipeline synchronously"""
        logger.info("\n" + "="*60)
        logger.info("STARTING DATA INGESTION PIPELINE")
        logger.info(f"URL: {url}")
        logger.info("="*60 + "\n")
        
        try:
            # STEP 1: Scrape
            logger.info("STEP 1: Web Scraping")
            logger.info("-" * 40)
            scraped = self._scrape_website()
            
            # STEP 1.5: Filter low-quality content (IMPROVED version)
            logger.info("\nSTEP 1.5: Content Quality Filtering (Improved)")
            logger.info("-" * 40)
            filtered = ImprovedContentFilter.filter_documents_v2(scraped)
            
            # STEP 2: Clean
            logger.info("\nSTEP 2: Text Cleaning")
            logger.info("-" * 40)
            cleaned = self._clean_documents(filtered)
            
            logger.info("\nSTEP 3: Intelligent Chunking")
            logger.info("-" * 40)
            chunks = self._chunk_documents(cleaned)

            # STEP 3.5: Inject OFFICIAL knowledge (PRIMARY data source)
            # Official chunks: institution-provided, verified, tagged priority=2
            # These beat all scraped data in the reranker
            logger.info("\nSTEP 3.5: Injecting Official Knowledge Base (PRIMARY SOURCE)")
            logger.info("-" * 40)
            from app.services.knowledge.official_knowledge import get_official_chunks
            from app.services.data_cleaning import TextCleaner, estimate_tokens
            cleaner_ok = TextCleaner()
            official_raw = get_official_chunks()
            official_chunks = []
            for doc in official_raw:
                # Official KB chunks are already clean structured text.
                # Do NOT run through TextCleaner — it collapses newlines/bullets
                # which breaks the sentence splitter in answer_generator.
                content = doc.get('content', '').strip()
                official_chunks.append({
                    'content': content,
                    'url': doc.get('url', ''),
                    'heading': doc.get('title', 'Official Knowledge'),
                    'chunk_index': 0,
                    'tokens': estimate_tokens(content),
                    'source': 'official',   # ← reranker uses this
                    'priority': 2,           # ← highest priority
                    'category': doc.get('category', 'general'),
                })
            chunks = chunks + official_chunks
            logger.info(f"✓ Injected {len(official_chunks)} official knowledge chunks (total: {len(chunks)})")

            # STEP 4: Embed
            logger.info("\nSTEP 4: Generate Embeddings")
            logger.info("-" * 40)
            embeddings, metadata, chunk_ids = self._embed_chunks(chunks)
            
            # STEP 5: Store in FAISS + Supabase (parallel)
            logger.info("\nSTEP 5: Build FAISS Index & Store in Supabase")
            logger.info("-" * 40)
            index_path = self._build_faiss_and_store_embeddings(chunks, chunk_ids, embeddings, metadata)
            
            # STEP 6: Save Checkpoints
            logger.info("\nSTEP 6: Save Local Checkpoints")
            logger.info("-" * 40)
            self._save_checkpoints(chunks, embeddings, metadata, chunk_ids)
            
            # Summary
            logger.info("\n" + "="*60)
            logger.info("✓ INGESTION COMPLETE")
            logger.info("="*60)
            self._print_summary(index_path)
            
            return {
                'success': True,
                'stats': self.stats,
                'index_path': index_path,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"\n❌ PIPELINE FAILED: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats,
                'timestamp': datetime.now().isoformat()
            }
    
    def _scrape_website(self) -> List[Dict]:
        """Scrape website using Playwright (JS-aware) + static knowledge injection"""
        logger.info("Scraping website (Playwright + static knowledge)...")

        # PRIMARY: Playwright JS-aware scraper (handles Next.js)
        if self.use_playwright:
            try:
                documents = scrape_aims_website_enhanced()
                logger.info(f"✓ Playwright + static knowledge: {len(documents)} documents")
            except Exception as e:
                logger.warning(f"⚠️  Playwright scrape failed ({e}), falling back to requests scraper")
                documents = self.scraper.scrape_website()
        else:
            documents = self.scraper.scrape_website()

        # SUPPLEMENTAL: Load any manually saved browser data
        supplemental_path = os.path.join(os.path.dirname(__file__), 'aims_browser_data.json')
        if os.path.exists(supplemental_path):
            try:
                with open(supplemental_path, 'r') as f:
                    supplemental_data = json.load(f)
                existing_urls = {doc.get('url') for doc in documents}
                new_docs = [d for d in supplemental_data if d.get('url') not in existing_urls]
                if new_docs:
                    logger.info(f"➕  Added {len(new_docs)} supplemental documents from JSON")
                    documents.extend(new_docs)
            except Exception as e:
                logger.warning(f"⚠️  Failed to load supplemental data: {e}")

        self.stats['scraped_pages'] = len(documents)
        logger.info(f"✓ Total pages for ingestion: {len(documents)}")
        return documents
    
    def _clean_documents(self, documents: List[Dict]) -> List[Dict]:
        """Clean scraped documents"""
        logger.info(f"Cleaning {len(documents)} documents")
        
        cleaned = []
        for doc in documents:
            cleaned_doc = {
                'title': doc.get('title', ''),
                'content': self.cleaner.clean(doc.get('content', '')),
                'url': doc.get('url', ''),
                'type': doc.get('type', 'page')  # Preserve FAQ type if present
            }
            cleaned.append(cleaned_doc)
        
        self.stats['cleaned_documents'] = len(cleaned)
        logger.info(f"✓ Cleaned {len(cleaned)} documents")
        
        return cleaned
    
    def _chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """Chunk documents into 400-600 token pieces"""
        logger.info(f"Chunking {len(documents)} documents")
        
        chunks = chunk_documents(
            documents,
            target_tokens=500,
            overlap_tokens=75
        )
        
        self.stats['chunks_created'] = len(chunks)
        
        logger.info(f"✓ Created {len(chunks)} chunks")
        if chunks:
            tokens = [c.get('tokens', 0) for c in chunks]
            avg = sum(tokens) / len(tokens) if tokens else 0
            logger.info(f"  • Avg tokens: {avg:.0f}")
            logger.info(f"  • Range: {min(tokens)}-{max(tokens)}")
        
        return chunks
    
    def _embed_chunks(self, chunks: List[Dict]) -> Tuple[List, List, List]:
        """Generate embeddings for chunks"""
        logger.info(f"Embedding {len(chunks)} chunks")
        
        texts = [chunk['content'] for chunk in chunks]
        embeddings = self.embeddings.embed_batch(texts)
        
        # Include the full chunk content in metadata (required for synthesis)
        metadata = [
            {
                'text': chunk['content'],  # IMPORTANT: Include actual chunk text
                'url': chunk['url'],
                'heading': chunk.get('heading', ''),
                'chunk_index': chunk.get('chunk_index', 0),
                'tokens': chunk.get('tokens', 0),
                'type': chunk.get('type', 'page'),   # Preserve FAQ type
                'source': chunk.get('source', 'web'),    # ← official or web
                'priority': chunk.get('priority', 1),    # ← 2=official, 1=scraped
                'category': chunk.get('category', ''),
            }
            for chunk in chunks
        ]
        
        chunk_ids = [
            f"{chunk['url']}#{chunk.get('chunk_index', 0)}"
            for chunk in chunks
        ]
        
        self.stats['embeddings_generated'] = len(embeddings)
        logger.info(f"✓ Generated {len(embeddings)} embeddings")
        logger.info(f"  • Shape: {embeddings.shape}")
        logger.info(f"  • Type: {embeddings.dtype}")
        
        return embeddings.tolist(), metadata, chunk_ids
    
    def _build_faiss_and_store_embeddings(
        self,
        chunks: List[Dict],
        doc_ids: List[str],
        embeddings: List[List[float]],
        metadata: List[Dict]
    ) -> str:
        """Build FAISS index AND store embeddings in Supabase (parallel)"""
        
        # PRIMARY: Build FAISS Index (always)
        logger.info(f"Building FAISS index for {len(doc_ids)} documents")
        index = build_faiss_index_from_embeddings(
            embeddings=embeddings,
            documents=metadata,
            doc_ids=doc_ids
        )
        logger.info(f"✓ FAISS index built")
        logger.info(f"  • Vectors: {index.index.ntotal}")
        logger.info(f"  • Path: {index.index_path}")
        self.stats['faiss_saved'] = True
        
        # SECONDARY: Store in Supabase (optional, parallel)
        if self.use_supabase:
            logger.info(f"\nStoring embeddings in Supabase...")
            for i, (embedding, chunk) in enumerate(zip(embeddings, chunks)):
                try:
                    self.supabase_store.insert_embedding(
                        content=chunk['content'],
                        embedding=embedding,
                        metadata=metadata[i]
                    )
                    self.stats['supabase_stored'] += 1
                except Exception as e:
                    logger.warning(f"  ⚠️  Failed to store chunk {i}: {e}")
                    self.stats['supabase_failed'] += 1
            
            logger.info(f"✓ Supabase: {self.stats['supabase_stored']} stored, {self.stats['supabase_failed']} failed")
        else:
            logger.info("ℹ️  Supabase not available (FAISS-only mode)")
        
        return index.index_path
    
    def _save_checkpoints(
        self,
        chunks: List[Dict],
        embeddings: List[List[float]],
        metadata: List[Dict],
        chunk_ids: List[str]
    ) -> None:
        """Save data locally for checkpoint/debugging"""
        checkpoint_dir = "/tmp/chatbot_ingest"
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        # Save chunks
        chunks_file = os.path.join(checkpoint_dir, "chunks.json")
        with open(chunks_file, 'w') as f:
            json.dump(chunks, f, indent=2)
        logger.info(f"✓ Saved chunks: {chunks_file}")
        
        # Save metadata
        metadata_file = os.path.join(checkpoint_dir, "metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump({
                'chunk_ids': chunk_ids,
                'metadata': metadata,
                'total_embeddings': len(embeddings)
            }, f, indent=2)
        logger.info(f"✓ Saved metadata: {metadata_file}")
    
    def _print_summary(self, index_path: str) -> None:
        """Print final summary"""
        logger.info(f"\nPipeline Statistics:")
        logger.info(f"  Scraped pages:        {self.stats['scraped_pages']}")
        logger.info(f"  Cleaned documents:    {self.stats['cleaned_documents']}")
        logger.info(f"  Chunks created:       {self.stats['chunks_created']}")
        logger.info(f"  Embeddings generated: {self.stats['embeddings_generated']}")
        logger.info(f"  FAISS index saved:    {self.stats['faiss_saved']}")
        logger.info(f"\nOutput locations:")
        logger.info(f"  FAISS index:    {index_path}/")
        logger.info(f"  Checkpoints:    /tmp/chatbot_ingest/")


def main():
    """Main entry point"""
    pipeline = DataIngestionPipeline()
    result = pipeline.run()
    
    # Exit with status
    return 0 if result['success'] else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
