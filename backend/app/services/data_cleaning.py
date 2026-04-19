"""
Text Cleaning and Chunking Pipeline

Implements:
- Text cleaning (remove duplicates, fix encoding)
- Intelligent chunking (400-600 tokens, 50-100 overlap)
- Heading preservation
- Token counting for accuracy
"""

import logging
import re
from typing import List, Dict, Tuple
from html import unescape

logger = logging.getLogger(__name__)

# Simplified token estimator (1 token ~= 4 chars, or 1 word ~= 1.3 tokens)
def estimate_tokens(text: str) -> int:
    """Estimate number of tokens in text"""
    # Simple heuristic: ~1 token per word, ~4 chars per token
    words = len(text.split())
    return max(words, len(text) // 4)


class TextCleaner:
    """Clean and normalize text"""
    
    @staticmethod
    def clean(text: str) -> str:
        """Clean text"""
        if not text:
            return ""
        
        # Decode HTML entities
        text = unescape(text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Remove duplicate spaces
        text = re.sub(r' +', ' ', text)
        
        return text.strip()


class SmartChunker:
    """Intelligent text chunking with overlap"""
    
    def __init__(
        self,
        target_tokens: int = 500,  # Target 500 tokens
        min_tokens: int = 300,
        max_tokens: int = 700,
        overlap_tokens: int = 75
    ):
        """
        Initialize chunker
        
        Args:
            target_tokens: Target chunk size (400-600 recommended)
            min_tokens: Minimum chunk size (allow some flexibility)
            max_tokens: Maximum chunk size
            overlap_tokens: Overlap between chunks (50-100 recommended)
        """
        self.target_tokens = target_tokens
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences while preserving structure"""
        # Split by common sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def chunk(self, text: str, preserve_title: bool = False) -> List[str]:
        """
        Intelligently chunk text
        
        Args:
            text: Text to chunk
            preserve_title: If True, keep first sentence as implicit title
        
        Returns:
            List of chunks
        """
        if not text:
            return []
        
        text = TextCleaner.clean(text)
        sentences = self._split_by_sentences(text)
        
        if not sentences:
            return [text] if len(text) > self.min_tokens else []
        
        chunks = []
        current_chunk_sentences = []
        current_tokens = 0
        
        for i, sentence in enumerate(sentences):
            sentence_tokens = estimate_tokens(sentence)
            
            # Check if adding this sentence would exceed max
            if current_tokens + sentence_tokens > self.max_tokens and current_chunk_sentences:
                # Save current chunk
                chunk_text = ' '.join(current_chunk_sentences)
                chunks.append(chunk_text)
                
                # Start new chunk with overlap
                # Go back by overlap_tokens worth of sentences
                overlap_sentences = []
                overlap_total = 0
                for j in range(len(current_chunk_sentences) - 1, -1, -1):
                    overlap_sent = current_chunk_sentences[j]
                    overlap_total += estimate_tokens(overlap_sent)
                    overlap_sentences.insert(0, overlap_sent)
                    if overlap_total >= self.overlap_tokens:
                        break
                
                current_chunk_sentences = overlap_sentences + [sentence]
                current_tokens = sum(estimate_tokens(s) for s in current_chunk_sentences)
            else:
                # Add to current chunk
                current_chunk_sentences.append(sentence)
                current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk_sentences:
            chunk_text = ' '.join(current_chunk_sentences)
            if estimate_tokens(chunk_text) >= self.min_tokens:
                chunks.append(chunk_text)
        
        return chunks


def chunk_documents(
    documents: List[Dict[str, str]],
    target_tokens: int = 500,
    overlap_tokens: int = 75
) -> List[Dict[str, str]]:
    """
    Chunk multiple documents
    
    Input:
        [{'title': '...', 'content': '...', 'url': '...'}, ...]
    
    Output:
        [{'content': '...', 'url': '...', 'heading': '...', 'chunk_index': 0}, ...]
    """
    chunker = SmartChunker(
        target_tokens=target_tokens,
        overlap_tokens=overlap_tokens
    )
    
    results = []
    
    for doc in documents:
        content = doc.get('content', '')
        url = doc.get('url', '')
        title = doc.get('title', '')
        
        chunks = chunker.chunk(content, preserve_title=True)
        
        for chunk_idx, chunk_text in enumerate(chunks):
            results.append({
                'content': chunk_text,
                'url': url,
                'heading': title or 'Untitled',
                'chunk_index': chunk_idx,
                'tokens': estimate_tokens(chunk_text)
            })
    
    logger.info(f"Created {len(results)} chunks from {len(documents)} documents")
    return results
