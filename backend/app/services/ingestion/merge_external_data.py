"""
Merge External Data with FAISS Index

Pipeline:
1. Load extracted documents from document_processor
2. Clean & normalize text
3. Embed with sentence-transformers
4. Add to existing FAISS index
5. Version control (snapshots before/after)
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

# Import from existing modules
from app.services.embeddings.embedding_service import embed_batch
from app.services.retrieval.faiss_index import FAISSIndex, get_index


class ExternalDataMerger:
    """
    Merge external data (PDFs, structured) into FAISS index
    
    Safely integrates new documents while preserving existing index
    """
    
    def __init__(self):
        """Initialize merger"""
        self.index = get_index()
        self.external_docs: List[Dict[str, Any]] = []
        logger.info("External data merger initialized")
    
    def load_extracted_documents(self, json_file: str) -> List[Dict[str, Any]]:
        """
        Load documents from extraction phase
        
        Format:
        [{
            "content": "Rich text from PDF",
            "source": "fees_brochure.pdf",
            "metadata": {"category": "fees", "page": 2}
        }, ...]
        """
        try:
            with open(json_file, 'r') as f:
                docs = json.load(f)
            
            self.external_docs = docs
            logger.info(f"Loaded {len(docs)} external documents")
            return docs
        
        except Exception as e:
            logger.error(f"Failed to load extracted documents: {e}")
            return []
    
    def normalize_text(self, text: str) -> str:
        """Clean and normalize document text"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Remove special characters but preserve meaning
        text = text.replace('\n', ' ').replace('\r', '')
        return text.strip()
    
    def chunk_document(self, doc: Dict[str, Any], 
                      max_chunk_size: int = 500) -> List[Dict[str, Any]]:
        """
        Split long documents into chunks
        
        Args:
            doc: Document from extraction
            max_chunk_size: Characters per chunk
        
        Returns:
            List of chunks
        """
        content = doc.get("content", "")
        normalized = self.normalize_text(content)
        
        if len(normalized) <= max_chunk_size:
            return [doc]
        
        # Split by sentences (preserves meaning better than char count)
        sentences = normalized.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunk_doc = doc.copy()
                    chunk_doc["content"] = current_chunk.strip()
                    chunks.append(chunk_doc)
                current_chunk = sentence + ". "
        
        # Add final chunk
        if current_chunk:
            chunk_doc = doc.copy()
            chunk_doc["content"] = current_chunk.strip()
            chunks.append(chunk_doc)
        
        return chunks
    
    def merge_documents(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main merge pipeline:
        1. Chunk documents
        2. Embed
        3. Add to FAISS
        4. Return stats
        """
        try:
            # Step 1: Chunk all documents
            all_chunks = []
            for doc in docs:
                chunks = self.chunk_document(doc, max_chunk_size=500)
                all_chunks.extend(chunks)
            
            logger.info(f"Created {len(all_chunks)} chunks from {len(docs)} documents")
            
            if not all_chunks:
                logger.warning("No chunks to add")
                return {"success": False, "reason": "No chunks"}
            
            # Step 2: Extract texts to embed
            texts_to_embed = [chunk["content"] for chunk in all_chunks]
            
            # Step 3: Embed batch
            logger.info(f"Embedding {len(texts_to_embed)} chunks...")
            embeddings = embed_batch(texts_to_embed)
            logger.info(f"✅ Embedded {len(embeddings)} vectors")
            
            # Step 4: Extract metadata
            sources = [chunk.get("source", "unknown") for chunk in all_chunks]
            headings = [chunk.get("source", "External Data") for chunk in all_chunks]
            
            # Step 5: Add to FAISS
            logger.info("Adding to FAISS index...")
            self.index.add_documents(
                texts=texts_to_embed,
                embeddings=embeddings,
                urls=sources,
                headings=headings
            )
            
            # Step 6: Save updated index
            self.index.save()
            logger.info("✅ Index saved")
            
            # Step 7: Return stats
            stats = self.index.get_stats()
            return {
                "success": True,
                "chunks_added": len(all_chunks),
                "index_stats": stats,
                "before_doc_count": stats["document_count"] - len(texts_to_embed),
                "after_doc_count": stats["document_count"]
            }
        
        except Exception as e:
            logger.error(f"Merge failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def merge_from_json(self, extracted_docs_file: str) -> Dict[str, Any]:
        """
        Complete pipeline:
        Load extracted docs → Merge into FAISS
        """
        docs = self.load_extracted_documents(extracted_docs_file)
        if not docs:
            return {"error": "No documents loaded"}
        
        return self.merge_documents(docs)


class IncrementalMergePipeline:
    """
    Safe incremental merging with version control
    
    Workflow:
    1. Snapshot current index
    2. Merge new data
    3. Validate
    4. Keep or rollback
    """
    
    def __init__(self):
        """Initialize pipeline"""
        self.merger = ExternalDataMerger()
        self.snapshots_dir = Path("/tmp/chatbot_ingest/snapshots")
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
    
    def safe_merge(self, extracted_docs_file: str, 
                   snapshot_name: str = None) -> Dict[str, Any]:
        """
        Safely merge with automatic snapshots
        
        Args:
            extracted_docs_file: JSON file from document_processor
            snapshot_name: Optional name for snapshot
        
        Returns:
            Merge result with stats
        """
        import shutil
        from app.services.ingestion.document_processor import DataVersioning
        
        # Create snapshot before merge
        if not snapshot_name:
            snapshot_name = f"before_merge"
        
        logger.info(f"Creating snapshot: {snapshot_name}")
        if not DataVersioning.create_snapshot(snapshot_name):
            return {"error": "Failed to create snapshot"}
        
        # Perform merge
        logger.info("Starting merge...")
        result = self.merger.merge_from_json(extracted_docs_file)
        
        if result.get("success"):
            logger.info("✅ Merge successful")
            return {
                "success": True,
                "snapshot": snapshot_name,
                "result": result
            }
        else:
            logger.error(f"Merge failed: {result.get('error')}")
            logger.info(f"Rolling back to snapshot: {snapshot_name}")
            DataVersioning.restore_snapshot(snapshot_name)
            return {
                "success": False,
                "error": result.get("error"),
                "rolled_back": True
            }


# ============================================================================
# INTEGRATION SCRIPT (to be run by user)
# ============================================================================

def merge_production_workflow():
    """
    Complete production workflow for merging external data
    
    Usage:
        cd /Users/maneeth/Desktop/Chat-Bot
        python -c "from backend.app.services.ingestion.merge_external_data import merge_production_workflow; merge_production_workflow()"
    """
    import json
    from datetime import datetime
    
    logger.info("="*70)
    logger.info("EXTERNAL DATA MERGE WORKFLOW")
    logger.info("="*70)
    
    # Simulate extracted documents (in practice, comes from document_processor)
    extracted_docs = [
        {
            "content": "MBA Fee Structure: Total cost 2,400,000 INR. Payment options: Annual (2.4L), Semester (600K), or Monthly installments at 5% interest.",
            "source": "fees_brochure_2024.pdf",
            "metadata": {"category": "fees", "page": 1}
        },
        {
            "content": "2023-24 Placement Report: 410 students placed out of 450 (91% placement rate). Average salary: 8.5 lakhs. Highest package: 15 lakhs. Top recruiters: TCS, Infosys, Accenture, Cognizant.",
            "source": "placement_report_2024.pdf",
            "metadata": {"category": "placements", "year": "2023-24"}
        },
        {
            "content": "Scholarships: Merit Scholarship for 90%+ students (up to 20% off). Sports Scholarship available. Gender Diversity Scholarship (2-5% for underrepresented genders).",
            "source": "scholarships_2024.json",
            "metadata": {"category": "scholarships"}
        },
        {
            "content": "Hostel Facilities: Boys hostel (200 capacity), Girls hostel (150 capacity). Both air-conditioned. WiFi available in all rooms. Common dining hall with multi-cuisine food.",
            "source": "campus_guide_2024.pdf",
            "metadata": {"category": "facilities"}
        }
    ]
    
    # Save to temp file
    docs_file = "/tmp/extracted_docs_demo.json"
    with open(docs_file, 'w') as f:
        json.dump(extracted_docs, f)
    
    # Run merge pipeline
    pipeline = IncrementalMergePipeline()
    result = pipeline.safe_merge(docs_file, snapshot_name=f"before_external_data_{datetime.now().strftime('%Y%m%d')}")
    
    logger.info("\nMERGE RESULTS:")
    logger.info(json.dumps(result, indent=2))
    
    if result.get("success"):
        logger.info("\n✅ External data successfully merged")
        logger.info(f"Before: {result['result']['before_doc_count']} documents")
        logger.info(f"After: {result['result']['after_doc_count']} documents")
        logger.info(f"Added: {result['result']['chunks_added']} chunks")
    else:
        logger.info(f"\n❌ Merge failed and rolled back: {result.get('error')}")


if __name__ == "__main__":
    merge_production_workflow()
