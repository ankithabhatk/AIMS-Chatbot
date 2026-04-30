"""
Signal Extraction Hardening - Production-Grade

Robust signal extraction that handles messy real-world input:
    - Slang and informal language ("idk", "bro", "lol")
    - Broken grammar and typos
    - Multiple signals per sentence
    - Weak/strong clarity signals
    - Fuzzy matching instead of exact keyword lookup

Architecture:
    extract_robust_signals(text) → List[Signal]
    
Properties:
    ✓ Deterministic: No ML models, rule-based only
    ✓ Fuzzy: Handles typos and variations
    ✓ Multi-signal: Extracts ALL signals from sentence
    ✓ Confident: Weights each signal with confidence
    ✓ Messy-proof: Handles slang, broken English, grammar

Signal Types:
    - interest (what user likes/wants)
    - constraint (what user is bad at / limits them)
    - goal (what user wants to achieve)
    - clarity (how certain user is)
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import re
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ════════════════════════════════════════════════════════════════════════════

class SignalType(Enum):
    """Types of signals we extract."""
    INTEREST = "interest"
    CONSTRAINT = "constraint"
    GOAL = "goal"
    CLARITY = "clarity"
    MARKS = "marks"
    COURSE = "course"


class ClarityLevel(Enum):
    """How certain is the user about this signal?"""
    STRONG = 0.95      # "I definitely want..."
    HIGH = 0.85        # "I want..."
    MODERATE = 0.70    # "maybe I want..."
    WEAK = 0.55        # "idk, maybe..."
    UNCERTAIN = 0.40   # "not sure...", "might be..."


@dataclass
class Signal:
    """Represents a single extracted signal."""
    type: SignalType
    value: str
    confidence: float  # 0.0-1.0, combines clarity + matching strength
    clarity_level: ClarityLevel
    raw_text: str  # The text this was extracted from
    source_match: str  # Which keyword/pattern matched
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "type": self.type.value,
            "value": self.value,
            "confidence": self.confidence,
            "clarity": self.clarity_level.name,
            "raw_text": self.raw_text,
            "source": self.source_match,
        }


@dataclass
class RobustSignalResult:
    """Result of robust signal extraction."""
    signals: List[Signal]
    raw_text: str
    num_sentences: int
    ambiguity_score: float  # 0.0-1.0, how unclear is the input overall
    is_messy: bool  # True if input has slang, typos, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            "signals": [s.to_dict() for s in self.signals],
            "raw_text": self.raw_text,
            "num_sentences": self.num_sentences,
            "ambiguity_score": self.ambiguity_score,
            "is_messy": self.is_messy,
        }


# ════════════════════════════════════════════════════════════════════════════
# SLANG & INFORMAL LANGUAGE NORMALIZATION
# ════════════════════════════════════════════════════════════════════════════

# Map slang to formal equivalents
SLANG_NORMALIZATION = {
    # Uncertainty markers
    "idk": "don't know",
    "dunno": "don't know",
    "not sure": "uncertain",
    "kinda": "kind of",
    "sorta": "sort of",
    "ish": "",  # "coding-ish" → "coding"
    
    # Enthusiasm/negation
    "hate": "dislike strongly",
    "love": "like very much",
    "gonna": "going to",
    "wanna": "want to",
    "can't": "cannot",
    "won't": "will not",
    "shouldn't": "should not",
    "couldn't": "could not",
    
    # Filler words to remove
    "bro": "",
    "dude": "",
    "like": "",  # "I like, really like coding" → "I really like coding"
    "lol": "",
    "omg": "oh my god",
    "btw": "by the way",
    "tbh": "to be honest",
    
    # Emphasis
    "so": "",  # "so coding" → "coding"
    "really": "",  # Often repetitive
}

# Patterns that indicate weak/uncertain signals
WEAK_SIGNAL_PREFIXES = [
    "maybe", "possibly", "perhaps", "might", "could", "may",
    "not sure", "idk", "dunno", "sort of", "kinda", "somewhat",
    "i guess", "i think", "probably"
]

STRONG_SIGNAL_PREFIXES = [
    "definitely", "absolutely", "for sure", "i know", "i'm sure",
    "without a doubt", "clearly", "obviously", "absolutely"
]

NEGATION_PATTERNS = [
    r"\b(?:not|no|never|don't|won't|can't|shouldn't|wouldn't|couldn't|isn't|aren't)\b"
]


def normalize_slang(text: str) -> Tuple[str, bool]:
    """
    Normalize slang to clearer language.
    
    Returns: (normalized_text, is_messy)
        - normalized_text: cleaned text
        - is_messy: True if original had significant slang/informality
    """
    text_lower = text.lower()
    original_length = len(text)
    changes = 0
    
    for slang, formal in SLANG_NORMALIZATION.items():
        pattern = r'\b' + re.escape(slang) + r'\b'
        if re.search(pattern, text_lower):
            text_lower = re.sub(pattern, formal, text_lower)
            changes += 1
    
    # Check for other slang indicators
    slang_indicators = ["lol", "haha", "xx", "!!!", "???", "bro", "dude"]
    is_messy = any(indicator in text_lower for indicator in slang_indicators) or changes > 2
    
    return text_lower, is_messy


def detect_clarity_from_prefixes(text: str) -> ClarityLevel:
    """
    Detect clarity level from sentence prefixes.
    
    Examples:
        "I definitely want coding" → STRONG
        "maybe coding" → WEAK
        "I'm not sure but coding" → UNCERTAIN
    """
    text_lower = text.lower()
    
    # Check strong signals first
    for prefix in STRONG_SIGNAL_PREFIXES:
        if prefix in text_lower:
            return ClarityLevel.STRONG
    
    # Check weak signals
    for prefix in WEAK_SIGNAL_PREFIXES:
        if prefix in text_lower:
            return ClarityLevel.WEAK
    
    # Check for negation
    if any(re.search(pattern, text_lower) for pattern in NEGATION_PATTERNS):
        return ClarityLevel.WEAK
    
    # Default to moderate
    return ClarityLevel.MODERATE


# ════════════════════════════════════════════════════════════════════════════
# FUZZY MATCHING & SIGNAL DETECTION
# ════════════════════════════════════════════════════════════════════════════

def fuzzy_match(text: str, keywords: List[str], threshold: float = 0.75) -> Optional[Tuple[str, float]]:
    """
    Fuzzy match text against keyword list.
    
    Handles typos, partial matches, and variations.
    
    Returns: (matched_keyword, confidence)
        Example: fuzzy_match("codin", ["coding", "programming"]) 
                 → ("coding", 0.92)
    """
    text_lower = text.lower().strip()
    
    best_match = None
    best_score = 0.0
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        
        # Exact match = perfect score
        if text_lower == keyword_lower:
            return keyword, 1.0
        
        # Substring match = very high score
        if keyword_lower in text_lower or text_lower in keyword_lower:
            return keyword, 0.95
        
        # Fuzzy match using SequenceMatcher
        ratio = SequenceMatcher(None, text_lower, keyword_lower).ratio()
        
        if ratio > best_score:
            best_score = ratio
            best_match = keyword
    
    # Return only if above threshold
    if best_score >= threshold:
        return best_match, best_score
    
    return None


# Interest signal groups (production-grade)
INTEREST_SIGNALS = {
    "coding": ["coding", "programming", "software", "developer", "code", "coder", "dev"],
    "business": ["business", "commerce", "management", "entrepreneur", "entrepreneurship"],
    "finance": ["finance", "accounting", "accounts", "banking", "money", "accounting"],
    "tech": ["tech", "technology", "it", "computers", "computer", "digital"],
    "hospitality": ["hotel", "hospitality", "event", "tourism", "travel"],
    "data": ["data", "analytics", "analysis", "statistics"],
    "ai_ml": ["ai", "artificial intelligence", "machine learning", "ml"],
}

# Constraint/limitation signals
CONSTRAINT_SIGNALS = {
    "weak_math": ["math", "maths", "mathematics", "numbers", "calculus", "algebra"],
    "bad_at": ["bad at", "weak in", "poor at", "struggle", "difficult"],
    "study_effort": ["study", "hard work", "dedication", "effort", "commitment"],
    "time": ["time", "busy", "schedule", "available", "available hours"],
}

# Goal signals
GOAL_SIGNALS = {
    "job": ["job", "placement", "employment", "work", "career"],
    "high_salary": ["high salary", "good money", "earn", "package", "salary"],
    "higher_studies": ["mba", "mca", "masters", "further study", "pg"],
    "stability": ["stable", "security", "safe", "predictable"],
    "entrepreneurship": ["startup", "own business", "entrepreneur", "independent"],
}


def extract_signal_by_type(text: str, signal_type: SignalType) -> List[Signal]:
    """
    Extract all signals of a given type from text.
    
    This is the workhorse function that:
    1. Normalizes slang
    2. Detects clarity
    3. Fuzzy matches against signal groups
    4. Weights confidence
    """
    signals = []
    normalized_text, is_messy = normalize_slang(text)
    clarity = detect_clarity_from_prefixes(normalized_text)
    
    # Choose signal group based on type
    if signal_type == SignalType.INTEREST:
        signal_groups = INTEREST_SIGNALS
    elif signal_type == SignalType.CONSTRAINT:
        signal_groups = CONSTRAINT_SIGNALS
    elif signal_type == SignalType.GOAL:
        signal_groups = GOAL_SIGNALS
    else:
        return signals
    
    # For each signal group, try fuzzy match
    for signal_name, keywords in signal_groups.items():
        # Split text into words/phrases for matching
        words = normalized_text.split()
        
        for i, word in enumerate(words):
            # Single word match
            match = fuzzy_match(word, keywords, threshold=0.70)
            if match:
                matched_keyword, fuzzy_score = match
                # Combine clarity + fuzzy score
                confidence = (clarity.value * 0.6) + (fuzzy_score * 0.4)
                
                signals.append(
                    Signal(
                        type=signal_type,
                        value=signal_name,
                        confidence=confidence,
                        clarity_level=clarity,
                        raw_text=text,
                        source_match=matched_keyword,
                    )
                )
            
            # Multi-word match (2-3 word phrases)
            if i < len(words) - 1:
                phrase = " ".join(words[i:i+2])
                match = fuzzy_match(phrase, keywords, threshold=0.75)
                if match:
                    matched_keyword, fuzzy_score = match
                    confidence = (clarity.value * 0.6) + (fuzzy_score * 0.4)
                    
                    signals.append(
                        Signal(
                            type=signal_type,
                            value=signal_name,
                            confidence=confidence,
                            clarity_level=clarity,
                            raw_text=text,
                            source_match=matched_keyword,
                        )
                    )
    
    return signals


# ════════════════════════════════════════════════════════════════════════════
# MULTI-SIGNAL EXTRACTION
# ════════════════════════════════════════════════════════════════════════════

def extract_robust_signals(text: str) -> RobustSignalResult:
    """
    Main extraction function: Handle messy input, extract multiple signals.
    
    Process:
        1. Normalize slang
        2. Split into sentences
        3. For each sentence, extract ALL signal types
        4. Weight by clarity and fuzzy match score
        5. Detect overall ambiguity
    
    Example:
        Input: "idk bro maybe coding but like I suck at math lol"
        Output: [
            Signal(type=interest, value="coding", confidence=0.75),
            Signal(type=constraint, value="weak_math", confidence=0.88),
            Signal(type=clarity, value=weak),
        ]
    """
    if not text or not text.strip():
        return RobustSignalResult(
            signals=[],
            raw_text=text,
            num_sentences=0,
            ambiguity_score=1.0,  # Completely ambiguous
            is_messy=False,
        )
    
    # Step 1: Detect messiness
    normalized_text, is_messy = normalize_slang(text)
    
    # Step 2: Split into sentences
    # Handle various punctuation
    sentence_pattern = r'[.!?;]|\band\b|\bbut\b'
    sentences = re.split(sentence_pattern, normalized_text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Step 3: Extract signals from each sentence
    all_signals = []
    
    for sentence in sentences:
        # Extract each signal type
        interest_signals = extract_signal_by_type(sentence, SignalType.INTEREST)
        constraint_signals = extract_signal_by_type(sentence, SignalType.CONSTRAINT)
        goal_signals = extract_signal_by_type(sentence, SignalType.GOAL)
        
        all_signals.extend(interest_signals)
        all_signals.extend(constraint_signals)
        all_signals.extend(goal_signals)
    
    # Step 4: De-duplicate signals (same value, keep highest confidence)
    deduplicated = {}
    for signal in all_signals:
        key = (signal.type, signal.value)
        if key not in deduplicated or signal.confidence > deduplicated[key].confidence:
            deduplicated[key] = signal
    
    all_signals = list(deduplicated.values())
    
    # Step 5: Calculate ambiguity
    if not all_signals:
        ambiguity_score = 1.0  # No signals = completely unclear
    else:
        # Average confidence of signals
        avg_confidence = sum(s.confidence for s in all_signals) / len(all_signals)
        # Invert: low confidence = high ambiguity
        ambiguity_score = 1.0 - avg_confidence
    
    # Step 6: Add clarity signal
    overall_clarity = detect_clarity_from_prefixes(normalized_text)
    clarity_signal = Signal(
        type=SignalType.CLARITY,
        value=overall_clarity.name.lower(),
        confidence=overall_clarity.value,
        clarity_level=overall_clarity,
        raw_text=text,
        source_match="prefix_detection",
    )
    all_signals.append(clarity_signal)
    
    # Sort by confidence (descending)
    all_signals.sort(key=lambda s: s.confidence, reverse=True)
    
    return RobustSignalResult(
        signals=all_signals,
        raw_text=text,
        num_sentences=len(sentences),
        ambiguity_score=ambiguity_score,
        is_messy=is_messy,
    )


# ════════════════════════════════════════════════════════════════════════════
# SIGNAL FILTERING & AGGREGATION
# ════════════════════════════════════════════════════════════════════════════

def filter_high_confidence_signals(signals: List[Signal], min_confidence: float = 0.65) -> List[Signal]:
    """
    Filter signals by minimum confidence threshold.
    
    Use this to get only "reliable" signals for decision-making.
    """
    return [s for s in signals if s.confidence >= min_confidence]


def aggregate_signals_by_type(signals: List[Signal]) -> Dict[SignalType, List[Signal]]:
    """
    Group signals by type for easier processing.
    
    Returns:
        {
            SignalType.INTEREST: [Signal, Signal],
            SignalType.CONSTRAINT: [Signal],
            ...
        }
    """
    by_type = {}
    
    for signal in signals:
        if signal.type not in by_type:
            by_type[signal.type] = []
        by_type[signal.type].append(signal)
    
    return by_type


def get_top_signals_per_type(signals: List[Signal], top_n: int = 2) -> Dict[SignalType, List[Signal]]:
    """
    Get top N signals for each type (by confidence).
    
    Useful for highlighting the most important signals.
    """
    by_type = aggregate_signals_by_type(signals)
    
    for signal_type in by_type:
        by_type[signal_type].sort(key=lambda s: s.confidence, reverse=True)
        by_type[signal_type] = by_type[signal_type][:top_n]
    
    return by_type


# ════════════════════════════════════════════════════════════════════════════
# DIAGNOSTIC FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def diagnose_extraction(result: RobustSignalResult) -> str:
    """
    Generate diagnostic report for debugging extraction.
    
    Example output:
        "Extracted 3 signals from 2 sentences (ambiguity: 0.25, messy: True)
         - coding (interest, confidence: 0.82)
         - weak_math (constraint, confidence: 0.88)
         - weak (clarity)"
    """
    lines = [
        f"Extraction Report for: {result.raw_text[:50]}...",
        f"  Signals: {len(result.signals)} (sentences: {result.num_sentences})",
        f"  Ambiguity: {result.ambiguity_score:.2f} (messiness: {result.is_messy})",
    ]
    
    for signal in result.signals[:5]:  # Top 5
        lines.append(
            f"    - {signal.value} ({signal.type.value}, "
            f"conf: {signal.confidence:.2f}, {signal.clarity_level.name})"
        )
    
    return "\n".join(lines)


def extract_primary_signal(result: RobustSignalResult) -> Optional[Signal]:
    """
    Extract the single most important signal from result.
    
    Useful when you need just one "best" signal (e.g., primary interest).
    """
    # Filter out clarity signals
    content_signals = [s for s in result.signals if s.type != SignalType.CLARITY]
    
    if content_signals:
        # Return highest confidence
        return content_signals[0]
    
    return None
