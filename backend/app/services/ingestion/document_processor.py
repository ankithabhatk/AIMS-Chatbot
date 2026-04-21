"""
PDF/Document Data Ingestion Pipeline (Production-Grade)

Handles:
- PDF extraction
- Excel/CSV parsing
- Structured data integration
- Merging with existing FAISS index
- Versioning & rollback
"""

import logging
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)

# Paths
INGEST_DIR = Path("/tmp/chatbot_ingest")
EXTERNAL_DATA_DIR = INGEST_DIR / "external_data"
SNAPSHOTS_DIR = INGEST_DIR / "snapshots"


class DocumentProcessor:
    """
    Process documents from college
    - PDFs (Fees, placement reports)
    - Structured data (CSV/JSON)
    """
    
    def __init__(self):
        """Initialize processor"""
        EXTERNAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Document processor ready: {EXTERNAL_DATA_DIR}")
    
    def process_fee_document(self, pdf_path: str) -> List[Dict[str, str]]:
        """
        Extract fee structure from PDF
        
        Returns:
            List of chunks with structured data:
            [{
                "program": "MBA",
                "fee_total": "2400000",
                "fee_per_semester": "600000",
                "payment_options": "Annual/Semester/Monthly",
                "content": "Rich text content",
                "source": "fees_brochure.pdf"
            }, ...]
        """
        try:
            import PyPDF2
            chunks = []
            
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    
                    # Parse structured data from text
                    # (In production: use layout detection + ML)
                    if "fee" in text.lower() or "cost" in text.lower():
                        chunk = {
                            "type": "fee_structure",
                            "page": page_num + 1,
                            "content": text,
                            "source": Path(pdf_path).name,
                            "metadata": {
                                "document_type": "fees_brochure",
                                "extracted_at": datetime.now().isoformat()
                            }
                        }
                        chunks.append(chunk)
            
            logger.info(f"Extracted {len(chunks)} fee chunks from {pdf_path}")
            return chunks
        
        except Exception as e:
            logger.error(f"Failed to process fee PDF: {e}")
            return []
    
    def process_placement_report(self, pdf_path: str) -> List[Dict[str, str]]:
        """
        Extract placement data from PDF/Excel
        
        Returns:
            [{
                "year": "2023-24",
                "total_students": "450",
                "placed": "410",
                "placement_rate": "91%",
                "avg_salary": "850000",
                "content": "...",
                "source": "placement_2024.pdf"
            }, ...]
        """
        try:
            chunks = []
            
            if pdf_path.endswith('.pdf'):
                import PyPDF2
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page_num, page in enumerate(reader.pages):
                        text = page.extract_text()
                        if any(word in text.lower() for word in ["placement", "salary", "company", "recruit"]):
                            chunk = {
                                "type": "placement_data",
                                "page": page_num + 1,
                                "content": text,
                                "source": Path(pdf_path).name,
                                "metadata": {
                                    "document_type": "placement_report",
                                    "extracted_at": datetime.now().isoformat()
                                }
                            }
                            chunks.append(chunk)
            
            elif pdf_path.endswith(('.xlsx', '.csv')):
                import pandas as pd
                df = pd.read_excel(pdf_path) if pdf_path.endswith('.xlsx') else pd.read_csv(pdf_path)
                
                # Convert rows to text chunks
                for idx, row in df.iterrows():
                    chunk = {
                        "type": "placement_data",
                        "row": idx,
                        "content": row.to_json(),
                        "source": Path(pdf_path).name,
                        "metadata": {
                            "document_type": "placement_report",
                            "extracted_at": datetime.now().isoformat()
                        }
                    }
                    chunks.append(chunk)
            
            logger.info(f"Extracted {len(chunks)} placement chunks from {pdf_path}")
            return chunks
        
        except Exception as e:
            logger.error(f"Failed to process placement document: {e}")
            return []
    
    def process_structured_data(self, json_path: str) -> List[Dict[str, str]]:
        """
        Load structured data (college provides JSON/JSONL)
        
        Expected format:
        {
            "category": "scholarships",
            "items": [
                {
                    "name": "Merit Scholarship",
                    "eligibility": "90%+ in previous exam",
                    "amount": "20% off tuition"
                },
                ...
            ]
        }
        """
        try:
            chunks = []
            
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            category = data.get("category", "general")
            items = data.get("items", [])
            
            for item in items:
                item_text = json.dumps(item, indent=2)
                chunk = {
                    "type": f"{category}_item",
                    "content": item_text,
                    "source": Path(json_path).name,
                    "metadata": {
                        "document_type": "structured_data",
                        "category": category,
                        "extracted_at": datetime.now().isoformat()
                    }
                }
                chunks.append(chunk)
            
            logger.info(f"Loaded {len(chunks)} structured items from {json_path}")
            return chunks
        
        except Exception as e:
            logger.error(f"Failed to process structured data: {e}")
            return []
    
    def batch_ingest_directory(self, directory: str) -> Dict[str, Any]:
        """
        Ingest all documents in a directory
        
        Directory structure:
        external_data/
        ├── fees/
        │   └── fee_structure_2024.pdf
        ├── placements/
        │   └── placement_report_2024.xlsx
        ├── facilities/
        │   └── campus_guide.pdf
        └── structured/
            ├── scholarships.json
            └── eligibility.json
        """
        try:
            base_dir = Path(directory)
            results = {
                "timestamp": datetime.now().isoformat(),
                "total_chunks": 0,
                "categories": {}
            }
            
            # Process fees
            fees_dir = base_dir / "fees"
            if fees_dir.exists():
                fee_chunks = []
                for pdf in fees_dir.glob("*.pdf"):
                    fee_chunks.extend(self.process_fee_document(str(pdf)))
                results["categories"]["fees"] = len(fee_chunks)
                results["total_chunks"] += len(fee_chunks)
                logger.info(f"✅ Fees: {len(fee_chunks)} chunks")
            
            # Process placements
            placement_dir = base_dir / "placements"
            if placement_dir.exists():
                placement_chunks = []
                for doc in placement_dir.glob("*.*"):
                    placement_chunks.extend(self.process_placement_report(str(doc)))
                results["categories"]["placements"] = len(placement_chunks)
                results["total_chunks"] += len(placement_chunks)
                logger.info(f"✅ Placements: {len(placement_chunks)} chunks")
            
            # Process facilities
            facilities_dir = base_dir / "facilities"
            if facilities_dir.exists():
                facility_chunks = []
                for pdf in facilities_dir.glob("*.pdf"):
                    facility_chunks.extend(self.process_fee_document(str(pdf)))
                results["categories"]["facilities"] = len(facility_chunks)
                results["total_chunks"] += len(facility_chunks)
                logger.info(f"✅ Facilities: {len(facility_chunks)} chunks")
            
            # Process structured
            structured_dir = base_dir / "structured"
            if structured_dir.exists():
                structured_chunks = []
                for json_file in structured_dir.glob("*.json"):
                    structured_chunks.extend(self.process_structured_data(str(json_file)))
                results["categories"]["structured"] = len(structured_chunks)
                results["total_chunks"] += len(structured_chunks)
                logger.info(f"✅ Structured: {len(structured_chunks)} chunks")
            
            logger.info(f"Total chunks ingested: {results['total_chunks']}")
            return results
        
        except Exception as e:
            logger.error(f"Batch ingest failed: {e}")
            return {"error": str(e)}


class DataVersioning:
    """Manage FAISS index versions before/after ingestion"""
    
    @staticmethod
    def create_snapshot(name: str) -> bool:
        """Create snapshot of current FAISS index"""
        try:
            source = Path("/tmp/chatbot_faiss")
            dest = SNAPSHOTS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if source.exists():
                shutil.copytree(source, dest)
                logger.info(f"✅ Snapshot created: {dest.name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Snapshot creation failed: {e}")
            return False
    
    @staticmethod
    def restore_snapshot(snapshot_name: str) -> bool:
        """Restore FAISS index from snapshot"""
        try:
            snapshot = next(SNAPSHOTS_DIR.glob(f"{snapshot_name}*"))
            dest = Path("/tmp/chatbot_faiss")
            
            if dest.exists():
                shutil.rmtree(dest)
            
            shutil.copytree(snapshot, dest)
            logger.info(f"✅ Restored from snapshot: {snapshot_name}")
            return True
        except Exception as e:
            logger.error(f"Snapshot restore failed: {e}")
            return False
    
    @staticmethod
    def list_snapshots() -> List[str]:
        """List available snapshots"""
        return [s.name for s in SNAPSHOTS_DIR.glob("*")]


# Global instance
_processor: Optional[DocumentProcessor] = None


def get_document_processor() -> DocumentProcessor:
    """Get or initialize document processor"""
    global _processor
    if _processor is None:
        _processor = DocumentProcessor()
    return _processor


# ============================================================================
# USAGE EXAMPLE (in docs)
# ============================================================================

"""
PRODUCTION WORKFLOW:

1. College provides documents:
   mkdir -p /tmp/chatbot_ingest/external_data/{fees,placements,facilities,structured}
   cp college_fees_2024.pdf /tmp/chatbot_ingest/external_data/fees/
   cp placement_2024.xlsx /tmp/chatbot_ingest/external_data/placements/

2. Create backup before ingestion:
   DataVersioning.create_snapshot("before_data_v1")

3. Ingest documents:
   processor = get_document_processor()
   results = processor.batch_ingest_directory("/tmp/chatbot_ingest/external_data")

4. Merge with existing FAISS:
   # (Next file: merge_external_data_with_faiss.py)

5. Re-validate:
   python backend/scripts/test_reliability_30queries.py

6. If good: keep
   If bad: DataVersioning.restore_snapshot("before_data_v1")
"""
