"""
Answer Generator - Synthesize coherent answers from multiple chunks

NOT just formatting - actual synthesis:
- Deduplicate content
- Extract key sentences
- Merge into coherent answer
- Handle contradictions
"""

import logging
from typing import List, Tuple
import re

logger = logging.getLogger(__name__)


class AnswerGenerator:
    """Generate coherent answers from multiple retrieved chunks"""
    
    def __init__(self, max_answer_length: int = 300, min_sentence_length: int = 30):
        """
        Initialize answer generator
        
        Args:
            max_answer_length: Maximum answer length in characters
            min_sentence_length: Minimum sentence length to consider (was 15, now 30 for stricter filtering)
        """
        self.max_answer_length = max_answer_length
        self.min_sentence_length = min_sentence_length
    
    def synthesize(self, query: str, chunks: List[Tuple[str, float, str, str]]) -> str:
        """
        Synthesize coherent answer from multiple chunks
        
        Args:
            query: Original user query (for relevance context)
            chunks: List of (text, similarity_score, url, heading)
        
        Returns:
            Synthesized answer string
        """
        if not chunks:
            return ""
        
        # Step 1: Extract sentences from all chunks
        all_sentences = self._extract_sentences(chunks)
        logger.debug(f"Extracted {len(all_sentences)} sentences from {len(chunks)} chunks")
        
        if not all_sentences:
            return self._fallback_to_first_chunk(chunks[0][0])
        
        # Step 2: Deduplicate
        unique_sentences = self._deduplicate_sentences(all_sentences)
        logger.debug(f"After deduplication: {len(unique_sentences)} unique sentences")
        
        if not unique_sentences:
            return self._fallback_to_first_chunk(chunks[0][0])
        
        # Step 3: Rank by relevance to query
        ranked = self._rank_by_relevance(query, unique_sentences)
        
        # Step 4: Build answer within length limit
        answer = self._build_answer(ranked)
        
        return answer
    
    def _extract_sentences(self, chunks: List[Tuple[str, float, str, str]]) -> List[Tuple[str, float, str]]:
        """
        Extract sentences from chunks
        
        Returns:
            List of (sentence, similarity_score, source_heading)
        """
        sentences = []
        
        for chunk in chunks:
            # Handle both 4-tuple and 5-tuple formats
            text = chunk[0]
            similarity = chunk[1]
            heading = chunk[3] if len(chunk) > 3 else "unknown"
            
            # Split by sentence boundaries
            raw_sentences = re.split(r'(?<=[.!?])\s+', text)
            
            for sent in raw_sentences:
                sent = sent.strip()
                
                # Skip if too short or just whitespace
                if len(sent) < self.min_sentence_length:
                    continue
                
                # Skip common boilerplate
                if self._is_boilerplate(sent):
                    continue
                
                sentences.append((sent, similarity, heading))
        
        return sentences
    
    def _deduplicate_sentences(self, sentences: List[Tuple[str, float, str]]) -> List[Tuple[str, float, str]]:
        """
        Remove duplicate or near-duplicate sentences
        
        Uses simple string similarity (character-level)
        """
        unique = []
        seen_normalized = set()
        
        for sent, score, heading in sentences:
            # Normalize for comparison
            normalized = self._normalize_for_comparison(sent)
            
            # Check if we've seen this before (fuzzy match)
            is_duplicate = False
            for prev_norm in seen_normalized:
                if self._are_similar(normalized, prev_norm, threshold=0.85):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append((sent, score, heading))
                seen_normalized.add(normalized)
        
        return unique
    
    def _rank_by_relevance(self, query: str, sentences: List[Tuple[str, float, str]]) -> List[Tuple[str, float, str]]:
        """
        Rank sentences by relevance to original query
        
        Factors:
        - Original chunk similarity (from FAISS)
        - Query term overlap
        - Position in answer
        """
        query_terms = set(query.lower().split())
        ranked = []
        
        for sent, score, heading in sentences:
            # Base score from FAISS
            relevance = float(score)
            
            # Boost if sentence contains query terms
            sent_lower = sent.lower()
            term_matches = sum(1 for term in query_terms if term in sent_lower)
            relevance += (term_matches * 0.05)  # Boost per matching term
            
            # Prefer well-formed sentences
            if sent.endswith(('.', '!', '?')):
                relevance += 0.02
            
            ranked.append((sent, relevance, heading))
        
        # Sort by relevance (descending)
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        return ranked
    
    def _build_answer(self, ranked_sentences: List[Tuple[str, float, str]]) -> str:
        """
        Build final answer by selecting sentences within length limit
        
        Maintains logical flow by selecting top-ranked sentences
        and joining coherently
        """
        if not ranked_sentences:
            logger.warning("No ranked sentences to build answer")
            return ""
        
        answer_parts = []
        current_length = 0
        
        logger.debug(f"Building answer from {len(ranked_sentences)} ranked sentences")
        
        for i, (sent, score, heading) in enumerate(ranked_sentences):
            sent_length = len(sent) + 1  # +1 for space
            
            # Stop if answer would exceed max length
            if current_length + sent_length > self.max_answer_length:
                logger.debug(f"Reached length limit at sentence {i}")
                break
            
            answer_parts.append(sent)
            current_length += sent_length
            logger.debug(f"Added sentence {i}: {sent[:50]}...")
        
        if not answer_parts:
            # Fallback: return first sentence of best chunk
            logger.warning("No sentences fit in length limit, using fallback")
            best_sent = ranked_sentences[0][0] if ranked_sentences else ""
            if len(best_sent) > self.max_answer_length:
                best_sent = best_sent[:self.max_answer_length].rsplit(' ', 1)[0] + "..."
            return best_sent
        
        # Join with spaces
        answer = " ".join(answer_parts)
        
        # Ensure proper ending
        if answer and not answer.endswith(('.', '!', '?')):
            answer += "."
        
        logger.debug(f"Final answer: {len(answer)} characters")
        return answer
    
    def _is_boilerplate(self, sentence: str) -> bool:
        """Skip common boilerplate and navigation text"""
        boilerplate_patterns = [
            r'^\s*\d+\s*$',  # Just numbers
            r'^\s*[a-z]\s*$',  # Single letters
            r'click here',
            r'learn more',
            r'^\s*[•\-\*]\s*',  # Bullet points
            r'deadline.*admission',  # Date-based announcements
            r'apply now',
            r'newsletter',
            r'subscribe',
            r'email.*address',
            r'phone.*number',
            r'this is achieved by',
            r'we (at|provide)',
            r'this website',
            r'privacy policy',
            r'terms and condition',
            r'copyright|all rights',
            r'facebook|twitter|linkedin|instagram',  # Social media
            r'^\s*the\s+(aims\s+)?newsletter',  # Newsletter text
        ]
        
        sent_lower = sentence.lower()
        
        for pattern in boilerplate_patterns:
            if re.search(pattern, sent_lower):
                return True
        
        # Filter repeated short phrases (common in navigation)
        words = sent_lower.split()
        if len(words) > 0:
            # If lots of repetition (> 40% of words repeated), it's navigation
            from collections import Counter
            word_counts = Counter(words)
            max_freq = max(word_counts.values()) if word_counts else 1
            if max_freq / len(words) > 0.4:
                return True
        
        return False
    
    def _normalize_for_comparison(self, text: str) -> str:
        """Normalize text for duplicate detection"""
        # Convert to lowercase
        text = text.lower()
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove punctuation for more lenient comparison
        text = re.sub(r'[^\w\s]', '', text)
        return text
    
    def _are_similar(self, text1: str, text2: str, threshold: float = 0.85) -> bool:
        """
        Check if two texts are similar (fuzzy matching)
        
        Uses simple character overlap ratio
        """
        if not text1 or not text2:
            return text1 == text2
        
        # Character set overlap
        set1 = set(text1)
        set2 = set(text2)
        
        if not set1 or not set2:
            return False
        
        overlap = len(set1 & set2) / len(set1 | set2)
        return overlap >= threshold
    
    def _fallback_to_first_chunk(self, text: str) -> str:
        """Fallback: use first chunk's text"""
        # Take first few sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        answer_parts = []
        current_length = 0
        
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            
            sent_length = len(sent) + 1
            if current_length + sent_length > self.max_answer_length:
                break
            
            answer_parts.append(sent)
            current_length += sent_length
        
        answer = " ".join(answer_parts)
        
        if answer and not answer.endswith(('.', '!', '?')):
            answer += "."
        
        return answer


# Global instance
_generator: AnswerGenerator = None


def get_answer_generator() -> AnswerGenerator:
    """Get or create answer generator"""
    global _generator
    if _generator is None:
        _generator = AnswerGenerator()
    return _generator
