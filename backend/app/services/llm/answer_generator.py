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

import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')
from app.config import get_settings

logger = logging.getLogger(__name__)


class AnswerGenerator:
    """Generate coherent answers from multiple retrieved chunks"""
    
    def __init__(
        self,
        max_answer_length: int = 1400,
        min_sentence_length: int = 20,
        max_answer_tokens: int = 320,
        max_context_tokens: int = 900,
    ):
        """
        Initialize answer generator
        
        Args:
            max_answer_length: Maximum answer length in characters
            min_sentence_length: Minimum sentence length
            max_answer_tokens: Final response token budget
            max_context_tokens: Max retrieved context consumed by synthesis
        """
        self.max_answer_length = max_answer_length
        self.min_sentence_length = min_sentence_length
        self.max_answer_tokens = max_answer_tokens
        self.max_context_tokens = max_context_tokens
    
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

        chunks = self._limit_context(chunks)
        
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
            
            # Split by sentence boundaries AND newlines (official KB uses newline-delimited facts)
            raw_sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
            
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
        - Factual priority (LPA, recruiters, brands)
        """
        query_terms = set(query.lower().split())
        query_lower = query.lower()
        ranked = []
        
        # Query-aware factual keyword groups — only boost terms relevant to this specific query
        FACTUAL_GROUPS = {
            'placement': {
                'triggers': ['recruiter', 'placement', 'package', 'salary', 'lpa', 'placed', 'company', 'hiring'],
                'boost_terms': ['lpa', 'package', 'recruiter', 'amazon', 'deloitte', 'ey', 'kpmg', 'accenture',
                                'infosys', 'wipro', 'tcs', 'cognizant', '27', '16.5', '84%', 'placement']
            },
            'hostel': {
                'triggers': ['hostel', 'accommodation', 'stay', 'dorm', 'resident'],
                'boost_terms': ['hostel', 'mess', 'security', 'cctv', 'biometric', 'wi-fi', 'wifi', 'laundry', 'furnished']
            },
            'accreditation': {
                'triggers': ['accreditat', 'naac', 'iacbe', 'aicte', 'ranking', 'nirf'],
                'boost_terms': ['naac', 'iacbe', 'aicte', 'accredited', 'accreditation', 'nirf', 'a grade']
            },
            'admission': {
                'triggers': ['admission', 'eligibility', 'eligible', 'apply', 'entrance', 'exam'],
                'boost_terms': ['eligibility', 'cat', 'mat', 'xat', 'cmat', '65', '70', 'percentile',
                                'bachelor', '50%', '45%', 'pgcet', 'entrance']
            },
            'specialization': {
                'triggers': ['specializ', 'subject', 'stream', 'track', 'course'],
                'boost_terms': ['finance', 'marketing', 'hr', 'analytics', 'healthcare', 'bfsi', 'logistics', 'operations']
            },
            'programs': {
                'triggers': ['program', 'course', 'degree', 'offer', 'phd', 'doctoral'],
                'boost_terms': ['mba', 'bba', 'mca', 'bca', 'b.com', 'phd', 'bachelor', 'master', 'doctoral']
            },
            'faqs': {
                'triggers': ['compulsory', 'mandatory', 'medium', 'english', 'instruction', 'lateral', 'visit', 'loan'],
                'boost_terms': ['optional', 'not compulsory', 'english', 'yes', 'no', 'loan', 'sbi', 'bank', 'visit']
            },
        }

        # Determine which factual group applies to this query
        active_boost_terms = set()
        for group_name, group in FACTUAL_GROUPS.items():
            if any(t in query_lower for t in group['triggers']):
                active_boost_terms.update(group['boost_terms'])

        # Fallback: use all terms if no group matched
        if not active_boost_terms:
            active_boost_terms = {'lpa', 'package', 'recruiter', 'hostel', 'admission', 'apply'}

        is_admission_query = any(k in query_lower for k in ["admission", "eligibility", "criteria", "process", "apply"])

        for sent, score, heading in sentences:
            relevance = float(score)
            sent_lower = sent.lower()

            # Boost if sentence contains query terms
            term_matches = sum(1 for term in query_terms if term in sent_lower)
            relevance += (term_matches * 0.05)

            # FACTUAL PRIORITY BOOST — only for query-relevant factual terms
            if any(k in sent_lower for k in active_boost_terms):
                relevance += 0.8

            # ELIGIBILITY FILTER: Skip eligibility text for non-admission queries
            if "applicant must satisfy" in sent_lower and not is_admission_query:
                relevance -= 0.6

            # Prefer well-formed sentences
            if sent.endswith(('.', '!', '?')):
                relevance += 0.02

            ranked.append((sent, relevance, heading))

        # Sort by relevance (descending)
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        return ranked
    
    def _build_answer(self, ranked_sentences: List[Tuple[str, float, str]]) -> str:
        """
        Build final answer with structured bullet points
        """
        if not ranked_sentences:
            return ""
        
        answer_parts = []
        current_length = 0
        current_tokens = 0
        
        logger.debug(f"Building structured answer from {len(ranked_sentences)} sentences")
        
        for i, (sent, score, heading) in enumerate(ranked_sentences):
            # Avoid double-prefix: if sentence already starts with '-' or '•', don't add another '•'
            stripped = sent.strip()
            if stripped.startswith('-') or stripped.startswith('•'):
                bullet_sent = stripped          # keep as-is
            else:
                bullet_sent = f"• {stripped}"
            
            sent_length = len(bullet_sent) + 1  # +1 for newline
            sent_tokens = self._estimate_tokens(bullet_sent)
            
            # Stop if answer would exceed max length
            if current_length + sent_length > self.max_answer_length:
                break
            if current_tokens + sent_tokens > self.max_answer_tokens:
                break
            
            answer_parts.append(bullet_sent)
            current_length += sent_length
            current_tokens += sent_tokens
        
        if not answer_parts:
            # Fallback: use raw first chunk content — always better than empty
            return self._fallback_to_first_chunk(ranked_sentences[0][0])
        
        # Join with newlines — no artificial header
        return "\n".join(answer_parts)
    
    def _is_boilerplate(self, sentence: str) -> bool:
        """Skip common boilerplate and navigation text"""
        boilerplate_patterns = [
            r'^\s*\d+\s*$',  # Just numbers
            r'^\s*[a-z]\s*$',  # Single letters
            r'click here',
            r'learn more',
            # NOTE: Do NOT filter bullet points — our official KB uses '- ' format for key facts
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
        current_tokens = 0
        
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            
            sent_length = len(sent) + 1
            sent_tokens = self._estimate_tokens(sent)
            if current_length + sent_length > self.max_answer_length:
                break
            if current_tokens + sent_tokens > self.max_answer_tokens:
                break
            
            answer_parts.append(sent)
            current_length += sent_length
            current_tokens += sent_tokens
        
        answer = " ".join(answer_parts)
        
        if answer and not answer.endswith(('.', '!', '?')):
            answer += "."
        
        return answer

    def _limit_context(self, chunks: List[Tuple[str, float, str, str]]) -> List[Tuple[str, float, str, str]]:
        """Trim retrieved context to a bounded token budget."""
        selected = []
        token_total = 0
        for chunk in chunks:
            text = chunk[0] if chunk else ""
            tokens = self._estimate_tokens(text)
            if selected and token_total + tokens > self.max_context_tokens:
                break
            selected.append(chunk)
            token_total += tokens
        return selected or chunks[:1]

    def _estimate_tokens(self, text: str) -> int:
        return max(len((text or "").split()), len((text or "")) // 4)


# Global instance
_generator: AnswerGenerator = None


def get_answer_generator() -> AnswerGenerator:
    """Get or create answer generator"""
    global _generator
    if _generator is None:
        settings = get_settings()
        _generator = AnswerGenerator(
            max_answer_length=1400,
            max_answer_tokens=getattr(settings, "answer_token_limit", 320),
            max_context_tokens=getattr(settings, "context_token_limit", 900),
        )
    return _generator
