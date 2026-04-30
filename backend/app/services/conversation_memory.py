"""
Conversation Memory - Session-based user profile tracking for multi-turn intelligence.

This module provides:
- Session memory store for user signals across turns
- Profile extraction from natural language queries
- Memory-aware routing and response generation
- Follow-up continuity (combining signals from multiple turns)
"""

import re
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ToneProfile:
    """Tone parameters for a specific confidence level."""
    
    # Opening phrase to inject before recommendation
    prefix: str
    
    # Strength of judgment language ("I'd recommend" vs "Consider")
    judgment_phrase: str
    
    # Confidence strength indicator
    confidence_strength: str  # "exploratory", "balanced", "decisive"
    
    def __post_init__(self):
        """Validate tone profile parameters."""
        valid_strengths = {"exploratory", "balanced", "decisive"}
        if self.confidence_strength not in valid_strengths:
            raise ValueError(f"Invalid confidence_strength: {self.confidence_strength}")


@dataclass
class UserProfile:
    """Tracks user signals extracted across conversation turns."""

    # Interests (what they like/enjoy)
    interests: Set[str] = field(default_factory=set)

    # Constraints (weaknesses, limitations, concerns)
    constraints: Set[str] = field(default_factory=set)

    # Goals (what they want to achieve)
    goals: Set[str] = field(default_factory=set)

    # Education level
    education_level: Optional[str] = None

    # Ambiguity signals (confusion, uncertainty)
    ambiguity_signals: Set[str] = field(default_factory=set)

    # Previous intents seen in this session
    previous_intents: List[str] = field(default_factory=list)

    # NEW: Cognitive State Tracking (Emotions & Importance)
    interest_importance: Dict[str, float] = field(default_factory=dict)
    recent_emotions: Set[str] = field(default_factory=set)

    # NEW: Dynamic confidence score (0.0-1.0) - replaces static confidence_level
    confidence_score: float = 0.3  # Start at low baseline

    # DEPRECATED: Flat signal history (kept for backward compatibility)
    confidence_signals: List[str] = field(default_factory=list)
    
    # NEW: Per-turn signal history for stable dampening logic
    # Each element is a list of signals from one turn
    # Example: [["ambiguity"], ["ambiguity", "weak_clarity"], ["strong_clarity"]]
    confidence_signal_history: List[List[str]] = field(default_factory=list)

    @property
    def confidence_category(self) -> str:
        """
        Map confidence score to category for backward compatibility with tone layer.
        
        Returns:
            "low", "medium", or "high" based on score thresholds
        """
        from app.services.confidence_engine import map_score_to_category
        return map_score_to_category(self.confidence_score)
    
    # DEPRECATED: Keep for backward compatibility during migration
    @property
    def confidence_level(self) -> str:
        """Deprecated: Use confidence_category instead."""
        return self.confidence_category

    def to_dict(self) -> Dict:
        return {
            "interests": list(self.interests),
            "constraints": list(self.constraints),
            "goals": list(self.goals),
            "education_level": self.education_level,
            "ambiguity_signals": list(self.ambiguity_signals),
            "previous_intents": self.previous_intents,
            "confidence_score": self.confidence_score,
            "confidence_signals": self.confidence_signals,
            "confidence_signal_history": self.confidence_signal_history,
            "interest_importance": self.interest_importance,
            "recent_emotions": list(self.recent_emotions),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "UserProfile":
        return cls(
            interests=set(data.get("interests", [])),
            constraints=set(data.get("constraints", [])),
            goals=set(data.get("goals", [])),
            education_level=data.get("education_level"),
            ambiguity_signals=set(data.get("ambiguity_signals", [])),
            previous_intents=data.get("previous_intents", []),
            confidence_score=data.get("confidence_score", 0.3),
            confidence_signals=data.get("confidence_signals", []),
            confidence_signal_history=data.get("confidence_signal_history", []),
            interest_importance=data.get("interest_importance", {}),
            recent_emotions=set(data.get("recent_emotions", [])),
        )


class ConversationMemory:
    """In-memory session store for user profiles and conversation context."""

    def __init__(self):
        # session_id -> UserProfile
        self._sessions: Dict[str, UserProfile] = {}

    def get_profile(self, session_id: str) -> UserProfile:
        """Get or create profile for session."""
        if session_id not in self._sessions:
            self._sessions[session_id] = UserProfile()
        return self._sessions[session_id]

    def update_profile(self, session_id: str, signals: Dict, query: str = "") -> UserProfile:
        """Update session profile with new signals extracted from query."""
        profile = self.get_profile(session_id)

        # Decay existing importance slightly (stale chatter decays)
        for k in profile.interest_importance.keys():
            profile.interest_importance[k] *= 0.9

        # Merge interests and boost importance
        if "interests" in signals:
            for interest in signals["interests"]:
                profile.interests.add(interest)
                profile.interest_importance[interest] = profile.interest_importance.get(interest, 0.0) + 1.0

        # Merge constraints and boost importance
        if "constraints" in signals:
            for constraint in signals["constraints"]:
                profile.constraints.add(constraint)
                profile.interest_importance[constraint] = profile.interest_importance.get(constraint, 0.0) + 1.0

        # Merge goals
        if "goals" in signals:
            profile.goals.update(signals["goals"])

        # Update education level (overwrite if new info)
        if signals.get("education_level"):
            profile.education_level = signals["education_level"]

        # Merge ambiguity signals
        if "ambiguity_signals" in signals:
            profile.ambiguity_signals.update(signals["ambiguity_signals"])

        # Update recent emotions
        if "emotions" in signals:
            profile.recent_emotions = set(signals["emotions"])

        # Track intent
        if signals.get("intent"):
            profile.previous_intents.append(signals["intent"])
            # Keep only last 5 intents
            profile.previous_intents = profile.previous_intents[-5:]

        # NEW: Update confidence score using confidence engine
        if "confidence_signals" in signals and signals["confidence_signals"]:
            from app.services.confidence_engine import update_confidence_score

            # Get previous score (None for brand new profiles that haven't been updated yet)
            # Check if this is the first update by seeing if any signals have been collected
            is_first_update = (
                not profile.interests and
                not profile.constraints and
                not profile.goals and
                not profile.ambiguity_signals and
                not profile.confidence_signals
            )
            prev_score = None if is_first_update else profile.confidence_score

            # Update score using confidence engine (SINGLE SOURCE OF TRUTH)
            # Pass query for context-aware signal interpretation
            new_score = update_confidence_score(
                prev_score,
                signals["confidence_signals"],
                query=query,  # For pivot disambiguation and emotional context
                profile=profile
            )
            logger.debug(
                f"[confidence] {prev_score} -> {new_score} | "
                f"signals={signals['confidence_signals']} | query={query[:40] if query else ''!r}"
            )
            profile.confidence_score = new_score
            
            # Track signal history for debugging (DEPRECATED: flat list)
            profile.confidence_signals.extend(signals["confidence_signals"])
            # Keep only last 10 signals
            profile.confidence_signals = profile.confidence_signals[-10:]
            
            # NEW: Track per-turn signal history for stable dampening
            profile.confidence_signal_history.append(signals["confidence_signals"])
            # Keep only last 5 turns
            profile.confidence_signal_history = profile.confidence_signal_history[-5:]

        return profile

    def clear_session(self, session_id: str) -> None:
        """Clear session memory (e.g., on explicit exit)."""
        if session_id in self._sessions:
            del self._sessions[session_id]

    def get_all_profiles(self) -> Dict[str, UserProfile]:
        """Return all session profiles (for debugging)."""
        return dict(self._sessions)


# Global singleton instance
_memory_store = ConversationMemory()


def get_memory_store() -> ConversationMemory:
    """Get the global conversation memory store."""
    return _memory_store


def extract_confidence_signals(query: str, profile: Optional[UserProfile] = None) -> List[str]:
    """
    Extract confidence-related signals from query for confidence engine.
    
    Returns list of signal identifiers:
    - "ambiguity": "idk", "maybe", "not sure", "confused"
    - "weak_clarity": "I like", "I want", "I need", OR mentions specific interest
    - "strong_clarity": "I decided", "I'm sure", "I will"
    - "decision_request": "what should I do?", "recommend", "suggest"
    - "pivot": "actually", "wait", "instead" - direction change signals
    - "negative_sentiment": "boring", "scary", "stressful", "hard" - emotional resistance
    - "contradiction": Conflicting statements (requires profile context)
    
    Args:
        query: User query text
        profile: Optional existing profile for contradiction detection
        
    Returns:
        List of signal identifiers (e.g., ["ambiguity", "weak_clarity"])
    """
    q = query.lower()
    signals = []
    
    # ===== PRIORITY 1: CONTRADICTION DETECTION (runs FIRST) =====
    # Strong contradiction: absolute rejection ("I hate", "absolutely hate")
    strong_contradiction_keywords = [
        "hate", "really hate", "absolutely hate", "terrible", "awful",
        "can't do this", "cannot do this", "never want", "not for me", "horrible"
    ]
    if any(kw in q for kw in strong_contradiction_keywords):
        signals.append("strong_contradiction")
    # Normal contradiction: clear negation ("don't like", "dislike")
    elif any(kw in q for kw in ["don't like", "dont like", "dislike", "not interested"]):
        signals.append("contradiction")
    
    # ===== PRIORITY 2: AMBIGUITY SIGNALS =====
    ambiguity_keywords = [
        "idk", "i don't know", "i dont know", "not sure", "unsure",
        "maybe", "perhaps", "confused", "confusing", "uncertain", "wondering"
    ]
    if any(kw in q for kw in ambiguity_keywords):
        signals.append("ambiguity")
    
    # ===== PRIORITY 3: PIVOT SIGNALS (after contradiction) =====
    # Pivot signals: direction change without explicit negation
    # Refinement: same-domain introspective comparison is reinforcement, not pivot.
    pivot_keywords = ["actually", "wait", "instead"]
    if any(kw in q for kw in pivot_keywords):
        should_add_pivot = True

        # Example: "I actually like coding more than I thought"
        # This compares current certainty vs past self-assessment in the same domain.
        # It should reinforce confidence, not trigger pivot.
        if (
            "actually" in q
            and "more than" in q
            and profile
            and profile.interests
        ):
            introspective_markers = [
                "more than i thought",
                "more than i expected",
                "more than i realized",
                "than i thought",
                "than i expected",
                "than i realized",
            ]

            domain_keywords = [
                "coding", "programming", "software", "tech", "developer",
                "business", "entrepreneur", "startup", "management", "mba", "manager",
                "hotel", "hospitality", "tourism", "commerce", "accounting", "finance",
                "design", "creative", "art", "music", "writing", "teaching", "medicine", "law",
            ]

            mentioned_domains = {d for d in domain_keywords if d in q}
            existing_domains = {
                d for d in domain_keywords
                if any(d in interest.lower() for interest in profile.interests)
            }
            has_new_domain = bool(mentioned_domains - existing_domains)
            has_existing_interest_mention = any(
                interest.lower() in q for interest in profile.interests
            )

            if (
                has_existing_interest_mention
                and not has_new_domain
                and any(marker in q for marker in introspective_markers)
            ):
                should_add_pivot = False

        if should_add_pivot:
            signals.append("pivot")
    
    # Negative sentiment signals: emotional resistance (not explicit negation)
    negative_sentiment_keywords = [
        "boring", "scary", "stressful", "hard", "difficult", "overwhelming",
        "no jobs", "not enough", "too much"
    ]
    if any(kw in q for kw in negative_sentiment_keywords):
        signals.append("negative_sentiment")
    
    # Strong clarity signals (handle word variations and word stems)
    # Check both full phrases and word stems
    has_strong_clarity = (
        "decided" in q or
        "certain" in q or  # matches "certain", "certainly", "sure"
        "definitely" in q or
        "will" in q or
        "going" in q or  # matches "going to"
        "feels right" in q or
        "feel right" in q or
        "makes sense" in q
    )
    if has_strong_clarity:
        signals.append("strong_clarity")
    
    # Weak clarity signals with AMPLIFICATION
    # 1. Explicit: "I like", "I want", "I need"
    # 2. Implicit: Mentions specific interest area (coding, business, etc.)
    
    # BUT: Don't add clarity if there's strong negation (contradiction context)
    has_strong_negation = any(neg in q for neg in [
        "i don't like", "i dont like", "i hate", "i dislike"
    ])
    
    if not has_strong_negation:
        # Count clarity indicators for amplification
        clarity_count = 0
        
        # Explicit clarity indicators (handle word variations by checking key phrases)
        explicit_clarity_patterns = [
            "like", "love", "want", "need", "enjoy", "prefer"
        ]
        
        # Simple approach: check if pattern appears in query
        # This handles "I like", "I really like", "I don't like", etc.
        has_i = any(word in q.split() for word in ["i", "i'm", "i'm", "im"])
        for pattern in explicit_clarity_patterns:
            if has_i and pattern in q:
                clarity_count += 1
                break  # Only count once even if multiple patterns
        
        # Implicit interest mentions
        interest_keywords = [
            "coding", "programming", "software", "tech", "developer",
            "business", "entrepreneur", "startup",
            "management", "mba", "manager",
            "hotel", "hospitality", "tourism",
            "commerce", "accounting", "finance",
            "design", "creative", "art"
        ]
        if any(kw in q for kw in interest_keywords):
            clarity_count += 1
        
        # AMPLIFICATION RULE: Multiple clarity indicators → strong clarity
        if clarity_count >= 2:
            if "strong_clarity" not in signals:
                signals.append("strong_clarity")
        elif clarity_count == 1:
            if "strong_clarity" not in signals:
                signals.append("weak_clarity")
    
    # Decision request signals
    decision_keywords = [
        "what should i do", "what do you suggest", "what do you recommend",
        "which one should i", "what's your recommendation", "suggest me",
        "recommend me", "help me decide", "what's best", "which is best"
    ]
    if any(kw in q for kw in decision_keywords):
        signals.append("decision_request")
    
    return signals



def extract_user_profile(query: str, existing_profile: Optional[UserProfile] = None) -> Dict:
    """
    Extract user signals from natural language query.

    This is the core extraction function that identifies:
    - Interests (coding, business, etc.)
    - Constraints (weak in math, not good at studies, etc.)
    - Goals (high salary, quick job, etc.)
    - Ambiguity (confused, not sure, etc.)
    - Confidence signals (for confidence engine)

    Returns dict of signals to merge into session profile.
    """
    q = query.lower()
    signals: Dict = {
        "interests": set(),
        "constraints": set(),
        "goals": set(),
        "ambiguity_signals": set(),
        "confidence_signals": [],  # NEW: For confidence engine
    }

    # ========== INTEREST SIGNALS ==========
    # Pattern: "I like/love/enjoy [X]"
    interest_keywords = {
        "coding": ["coding", "programming", "software", "tech", "computer", "app", "website", "developer", "python", "java", "javascript"],
        "business": ["business", "entrepreneur", "startup", "company", "sales", "marketing", "own business"],
        "management": ["management", "mba", "manager", "leadership", "corporate", "managing"],
        "hospitality": ["hotel", "hospitality", "tourism", "restaurant", "chef", "culinary", "food service"],
        "commerce": ["commerce", "accounting", "finance", "banking", "taxation", "ca", "cma"],
        "design": ["design", "creative", "art", "graphics", "ui", "ux"],
    }

    # Explicit interest patterns
    interest_patterns = [
        r"\bi\s+(like|love|enjoy|want to learn|interested in)\s+(\w+)",
        r"\bi'm\s+(good at|interested in|passionate about)\s+(\w+)",
        r"\bmy\s+(interest|passion|goal)\s+is\s+(\w+)",
    ]

    for pattern in interest_patterns:
        matches = re.findall(pattern, q)
        for match in matches:
            interest_text = match[-1] if isinstance(match, tuple) else match
            for area, keywords in interest_keywords.items():
                if any(kw in interest_text or interest_text in kw for kw in keywords):
                    signals["interests"].add(area)

    # Direct keyword matching for interests
    for area, keywords in interest_keywords.items():
        if any(kw in q for kw in keywords):
            signals["interests"].add(area)

    # ========== CONSTRAINT SIGNALS ==========
    # Weakness/constraint patterns
    constraint_patterns = [
        (r"\bweak in\s+(\w+)", "weak_{}"),
        (r"\bbad at\s+(\w+)", "bad_at_{}"),
        (r"\bnot good at\s+(\w+)", "not_good_at_{}"),
        (r"\bpoor at\s+(\w+)", "poor_at_{}"),
        (r"\bstruggle with\s+(\w+)", "struggle_{}"),
        (r"\bdifficulty with\s+(\w+)", "difficulty_{}"),
        (r"\bnot great at\s+(\w+)", "not_great_at_{}"),
    ]

    for pattern, template in constraint_patterns:
        matches = re.findall(pattern, q)
        for match in matches:
            signals["constraints"].add(template.format(match))

    # Direct constraint keywords
    constraint_keywords = {
        "weak_in_math": ["weak in math", "bad at math", "not good at math", "poor at math", "math phobia", "hate math"],
        "weak_in_studies": ["not great at studies", "not good at studies", "weak student", "poor grades", "low marks", "not a good student"],
        "budget_constraint": ["low budget", "cannot afford", "expensive", "too much fees", "affordable"],
        "time_constraint": ["quickly", "fast", "short time", "less time", "early"],
        "not_science": ["not science", "no science", "without science", "non-science"],
    }

    for constraint_key, phrases in constraint_keywords.items():
        if any(phrase in q for phrase in phrases):
            signals["constraints"].add(constraint_key)

    # ========== GOAL SIGNALS ==========
    goal_patterns = [
        (r"\bwant\s+(.+?)(?:\s|$|but|and|or)", "goal_{}"),
        (r"\blooking for\s+(.+?)(?:\s|$|but|and|or)", "goal_{}"),
        (r"\bneed\s+(.+?)(?:\s|$|but|and|or)", "goal_{}"),
    ]

    for pattern, template in goal_patterns:
        matches = re.findall(pattern, q)
        for match in matches:
            goal_text = match.strip()
            if len(goal_text) > 2:
                signals["goals"].add(f"goal_{goal_text[:20]}")

    # Direct goal keywords
    goal_keywords = {
        "high_salary": ["high salary", "good salary", "good package", "good pay", "high pay", "lpa", "lakhs", "money", "earning"],
        "quick_job": ["job quickly", "fast job", "quick placement", "early job", "job fast", "quick job"],
        "stable_career": ["stable career", "secure job", "government job", "permanent"],
        "higher_studies": ["higher studies", "masters", "phd", "research", "mca", "mba"],
        "entrepreneurship": ["own business", "startup", "entrepreneur", "business owner"],
        "work_abroad": ["work abroad", "foreign job", "overseas", "international"],
    }

    for goal_key, phrases in goal_keywords.items():
        if any(phrase in q for phrase in phrases):
            signals["goals"].add(goal_key)

    # ========== AMBIGUITY SIGNALS ==========
    ambiguity_keywords = [
        "not sure", "confused", "don't know", "dont know", "idk",
        "unsure", "uncertain", "wondering", "maybe", "perhaps",
        "what should i", "which one", "help me choose", "recommend",
    ]

    if any(phrase in q for phrase in ambiguity_keywords):
        signals["ambiguity_signals"].add("uncertain")

    # ========== EMOTIONAL TAXONOMY (NEW) ==========
    emotions = []
    
    if any(kw in q for kw in ["scared", "worried", "too hard", "afraid", "what if i fail", "nervous"]):
        emotions.append("fear")
    if any(kw in q for kw in ["skip that", "don't want to", "avoid", "hate", "boring", "not interested"]):
        emotions.append("avoidance")
    if any(kw in q for kw in ["annoying", "tired of", "frustrated", "too much", "giving up", "sucks"]):
        emotions.append("frustration")
    if any(kw in q for kw in ["bad at", "not smart enough", "failing", "too dumb", "struggle with"]):
        emotions.append("insecurity")
    if any(kw in q for kw in ["what about", "how does", "tell me more", "sounds interesting", "curious"]):
        emotions.append("curiosity")
        
    if emotions:
        signals["emotions"] = emotions

    # ========== CONFIDENCE SIGNALS (NEW) ==========
    # Extract signals for confidence engine
    signals["confidence_signals"] = extract_confidence_signals(query, existing_profile)

    # ========== EDUCATION LEVEL SIGNALS ==========
    education_patterns = [
        (r"\b12th|class 12|grade 12|std 12\b", "12th"),
        (r"\b10th|class 10|grade 10|std 10\b", "10th"),
        (r"\bbca|b\.?c\.?a\.?\b", "bca"),
        (r"\bbba|b\.?b\.?a\.?\b", "bba"),
        (r"\bb\.?com\.?|b\.?comm\.?\b", "bcom"),
        (r"\bbhm|hotel management\b", "bhm"),
        (r"\bgraduation|graduate|bachelor|degree\b", "graduate"),
        (r"\bpost graduation|postgraduate|masters|master\b", "postgraduate"),
    ]

    for pattern, level in education_patterns:
        if re.search(pattern, q):
            signals["education_level"] = level
            break

    # ========== PARENTAL PRESSURE SIGNALS ==========
    if any(phrase in q for phrase in ["parents want", "family wants", "parents say", "family pressure"]):
        signals["constraints"].add("parental_pressure")

    # ========== CONFLICT SIGNALS ==========
    if any(phrase in q for phrase in ["but i", "however i", "although i", "but my", "however my"]):
        signals["constraints"].add("internal_conflict")

    return signals


def should_force_counselor(profile: UserProfile, query: str) -> bool:
    """
    Determine if query should be routed to counselor based on accumulated profile.

    Returns True if:
    - User has constraints (weak in X, not good at Y)
    - User has ambiguity signals (confused, not sure)
    - User has conflicting signals (parents want X but I like Y)
    - Query contains follow-up indicators with existing profile
    """
    q = query.lower()

    # Constraints always trigger counselor
    if profile.constraints:
        return True

    # Ambiguity triggers counselor
    if profile.ambiguity_signals:
        return True

    # Follow-up with existing interests
    if profile.interests and len(profile.previous_intents) > 0:
        # Check if this looks like a follow-up
        follow_up_indicators = ["what about", "then", "so", "okay", "but", "and", "what if"]
        if any(q.startswith(ind) for ind in follow_up_indicators):
            return True

    # Parental pressure or conflict
    if "parental_pressure" in profile.constraints or "internal_conflict" in profile.constraints:
        return True

    return False


def build_memory_context(profile: UserProfile) -> str:
    """
    Build a summary of accumulated user context for response generation.

    Returns a string summarizing what we know about the user.
    """
    parts = []

    if profile.interests:
        parts.append(f"Interested in: {', '.join(profile.interests)}")

    if profile.constraints:
        constraint_display = []
        for c in profile.constraints:
            # Convert internal keys to readable format
            readable = c.replace("_", " ").replace("weak in", "weak in ").replace("not good at", "not good at ")
            constraint_display.append(readable)
        parts.append(f"Constraints: {', '.join(constraint_display)}")

    if profile.goals:
        goal_display = []
        for g in profile.goals:
            readable = g.replace("goal_", "").replace("_", " ")
            goal_display.append(readable)
        parts.append(f"Goals: {', '.join(goal_display)}")

    if profile.education_level:
        parts.append(f"Education: {profile.education_level}")

    if profile.ambiguity_signals:
        parts.append("User seems uncertain/confused")

    return "; ".join(parts) if parts else ""


def is_decision_query(query: str) -> bool:
    """Detect if query is asking for a final recommendation/decision."""
    q = query.lower()
    
    decision_signals = [
        "what should i do",
        "what do you suggest",
        "what do you recommend",
        "which one should i",
        "what's your recommendation",
        "what would you recommend",
        "suggest me",
        "recommend me",
        "help me decide",
        "final decision",
        "what's best",
        "which is best",
    ]
    
    return any(signal in q for signal in decision_signals)


def _build_base_recommendation(profile: UserProfile, query: str, force: bool) -> Optional[str]:
    """
    Build base recommendation without tone (existing logic).
    
    This is the existing build_final_recommendation logic extracted
    into a separate function for clarity.
    
    Args:
        profile: UserProfile with interests, constraints, goals
        query: Decision query ("what should I do")
        force: If True, override uncertainty handling and provide recommendation
        
    Returns:
        Optional[str]: Base recommendation or None if insufficient data
    """
    # Task 4.3: Avoid final recommendations when confidence is low
    # UNLESS force=True (Task 3.3 override)
    # Let the progressive response builder handle low confidence cases
    if profile.confidence_category == "low" and not force:
        return None
    
    # Need at least interest to make recommendation
    if not profile.interests:
        return None
    
    # Detect primary interest
    primary_interest = None
    if "coding" in profile.interests:
        primary_interest = "coding"
    elif "business" in profile.interests:
        primary_interest = "business"
    elif "management" in profile.interests:
        primary_interest = "management"
    elif "commerce" in profile.interests:
        primary_interest = "commerce"
    elif "hospitality" in profile.interests:
        primary_interest = "hospitality"
    
    if not primary_interest:
        return None
    
    # Build recommendation based on interest + constraints + goals
    parts = []
    
    # Header: Acknowledge what we know
    parts.append("Based on what you've told me:")
    profile_summary = []
    if profile.interests:
        profile_summary.append(f"• You like {', '.join(profile.interests)}")
    if profile.constraints:
        readable_constraints = []
        for c in profile.constraints:
            if "weak" in c or "not_good" in c or "not_great" in c:
                readable_constraints.append(c.replace("_", " "))
        if readable_constraints:
            profile_summary.append(f"• You're {', '.join(readable_constraints[:2])}")
    if profile.goals:
        readable_goals = []
        for g in profile.goals:
            if "salary" in g:
                readable_goals.append("want a good salary")
            elif "quick" in g:
                readable_goals.append("want a job quickly")
        if readable_goals:
            profile_summary.append(f"• You {', '.join(readable_goals[:2])}")
    
    parts.append("\n".join(profile_summary))
    parts.append("")
    
    # Recommendation based on primary interest
    if primary_interest == "coding":
        # Check constraints
        has_math_constraint = any("math" in c for c in profile.constraints)
        has_study_constraint = any("stud" in c or "grade" in c for c in profile.constraints)
        wants_high_salary = any("salary" in g for g in profile.goals)
        wants_quick_job = any("quick" in g for g in profile.goals)
        
        # CONFLICT DETECTION: Both high salary AND quick job
        if wants_high_salary and wants_quick_job:
            parts.append("**I notice you have two competing goals:**")
            parts.append("• High salary → requires longer path (BCA + MCA = 5 years)")
            parts.append("• Quick job → shorter path (BCA only = 3 years)")
            parts.append("")
            parts.append("**The risk with rushing into a decision is you might lock yourself into something that doesn't fit long-term.**")
            parts.append("")
            parts.append("**You need to choose your priority:**")
            parts.append("")
            
            parts.append("**Option 1 (Fast entry):**")
            parts.append("👉 BCA (3 years) → ₹3-6 LPA initially")
            parts.append("• Good if: You need income sooner")
            parts.append("• Trade-off: Lower starting salary")
            if has_math_constraint:
                parts.append("• Since you're weak in math: Focus on web/app development (less math-heavy)")
            parts.append("")
            
            parts.append("**Option 2 (Better long-term):**")
            parts.append("👉 BCA + MCA (5 years) → ₹6-16 LPA")
            parts.append("• Good if: You can invest more time")
            parts.append("• Trade-off: Delayed income, but higher ceiling")
            if has_math_constraint:
                parts.append("• Math improves with practice — MCA is still doable")
            parts.append("")
            
            parts.append("**My recommendation (balanced approach):**")
            parts.append("Start with BCA → try campus placements → decide on MCA after seeing real job market.")
            parts.append("")
            parts.append("**Why this works:**")
            parts.append("• You get job exposure after 3 years")
            parts.append("• You can earn while deciding on MCA")
            parts.append("• Many companies sponsor MCA for working professionals")
            if has_math_constraint:
                parts.append("• By then, your math skills will have improved through coding practice")
            parts.append("")
            parts.append("**What NOT to do:**")
            if has_math_constraint:
                parts.append("• Avoid data science/analytics roles initially (math-heavy)")
            parts.append("• Don't skip building projects — degree alone won't get high salary")
            parts.append("• Don't rush MCA decision — see the job market first")
            parts.append("")
            parts.append("---")
            parts.append("")
            parts.append("**If I were in your position**, I'd start with BCA and keep MCA open. Get real experience first, then decide.")
            
        elif wants_quick_job and not wants_high_salary:
            recommended_path = "BCA (3 years)"
            reasoning = [
                "• Coding relies more on logic than heavy math",
                "• BCA gets you job-ready faster",
                "• You can start earning sooner (₹3-6 LPA initially)",
            ]
            if has_math_constraint:
                reasoning.append("• You'll need basic math (logic, stats) but it's manageable")
            
            parts.append(f"**Here's the honest path:**")
            parts.append(f"👉 **{recommended_path}**")
            parts.append("")
            parts.append("**Why:**")
            parts.append("\n".join(reasoning))
            parts.append("")
            
            if has_math_constraint:
                parts.append("**Since you're weak in math:**")
                parts.append("• Focus on web/app development (React, Node.js, mobile apps)")
                parts.append("• Avoid data science/analytics initially")
                parts.append("• Math skills improve naturally through coding practice")
                parts.append("")
            
            parts.append("**Trade-off**: Lower starting salary, but faster entry into workforce")
            parts.append("")
            parts.append("**The risk with rushing into a decision is you might lock yourself into something that doesn't fit long-term.** Take time to explore your options.")
            parts.append("")
            parts.append("---")
            parts.append("")
            parts.append(f"👉 **My recommendation**: Start with BCA, focus on building projects and practical skills")
            parts.append("")
            parts.append("**If I were in your position**, I'd prioritize getting real-world experience quickly. You can always pursue MCA later if needed.")
            
        elif wants_high_salary or (not wants_quick_job):
            recommended_path = "BCA → MCA (3+2 years)"
            reasoning = [
                "• Coding relies more on logic than heavy math",
                "• MCA opens doors to higher salary brackets (₹6-16 LPA)",
                "• More time to build deep expertise",
            ]
            if has_math_constraint:
                reasoning.append("• You'll need basic math (logic, stats) but it improves with practice")
            if has_study_constraint:
                reasoning.append("• Interest matters more than grades — you'll find motivation if you genuinely like coding")
            
            parts.append(f"**Here's the honest path:**")
            parts.append(f"👉 **{recommended_path}**")
            parts.append("")
            parts.append("**Why:**")
            parts.append("\n".join(reasoning))
            parts.append("")
            
            if has_math_constraint:
                parts.append("**Since you're weak in math:**")
                parts.append("• Focus on development roles (web/app/mobile)")
                parts.append("• Avoid data science/ML initially")
                parts.append("• Your math will improve through coding — logic is more important")
                parts.append("")
            
            parts.append("**But be aware:**")
            awareness = []
            if has_math_constraint:
                awareness.append("• You'll still need basic math (logic, stats) — not zero math")
            awareness.append("• Building projects is essential — degree alone won't get high salary")
            if has_study_constraint:
                awareness.append("• Consistent effort required — but interest drives motivation")
            parts.append("\n".join(awareness))
            parts.append("")
            
            parts.append("**Trade-off**: Longer path (5 years total), but higher salary potential")
            parts.append("")
            parts.append("**The risk with rushing into a decision is you might lock yourself into something that doesn't fit long-term.** Consider your long-term goals carefully.")
            parts.append("")
            parts.append("---")
            parts.append("")
            parts.append(f"👉 **My recommendation**: Start with BCA, focus on development skills, and decide on MCA later based on your progress")
            parts.append("")
            parts.append("**If I were in your position**, I'd commit to the BCA+MCA path but stay flexible. Your progress and market conditions will guide the MCA decision.")
            
        else:
            # Default: BCA with option for MCA
            recommended_path = "BCA → MCA (recommended)"
            reasoning = [
                "• Coding relies more on logic than heavy math",
                "• BCA gets you started, MCA takes you higher",
                "• Flexible path — you can decide after BCA",
            ]
            
            parts.append(f"**Here's the honest path:**")
            parts.append(f"👉 **{recommended_path}**")
            parts.append("")
            parts.append("**Why:**")
            parts.append("\n".join(reasoning))
            parts.append("")
            
            if has_math_constraint:
                parts.append("**Since you're weak in math:**")
                parts.append("• Focus on development (web/app) — less math-intensive")
                parts.append("• Avoid data science initially")
                parts.append("• Math improves with coding practice")
                parts.append("")
            
            parts.append("**Two options**: BCA alone (₹3-6 LPA, 3 years) or BCA+MCA (₹6-16 LPA, 5 years)")
            parts.append("")
            parts.append("---")
            parts.append("")
            parts.append(f"👉 **My recommendation**: Start with BCA, focus on building projects, and decide on MCA based on your progress")
            parts.append("")
            parts.append("**If I were in your position**, I'd start with BCA and keep your options open. Build strong fundamentals first, then decide on MCA based on your interests and market opportunities.")
        
    elif primary_interest == "business":
        wants_high_salary = any("salary" in g for g in profile.goals)
        wants_quick_job = any("quick" in g for g in profile.goals)
        
        if wants_quick_job:
            recommended_path = "BBA (3 years)"
            reasoning = [
                "• Gets you into business roles faster",
                "• Learn practical business skills",
                "• Start earning sooner (₹3-6 LPA)",
            ]
            tradeoff = "**Trade-off**: Lower starting salary, but faster entry"
            next_step = "Start with BBA, focus on internships and networking"
        else:
            recommended_path = "BBA → MBA (3+2 years)"
            reasoning = [
                "• MBA opens doors to management roles",
                "• Higher salary potential (₹6-16 LPA)",
                "• Better for leadership positions",
            ]
            tradeoff = "**Trade-off**: Longer path (5 years), but higher career ceiling"
            next_step = "Start with BBA, build business skills, and pursue MBA for management roles"
        
        parts.append(f"**Here's the honest path:**")
        parts.append(f"👉 **{recommended_path}**")
        parts.append("")
        parts.append("**Why:**")
        parts.append("\n".join(reasoning))
        parts.append("")
        parts.append(tradeoff)
        parts.append("")
        parts.append("**The risk with rushing into a decision is you might lock yourself into something that doesn't fit long-term.** Think about where you want to be in 5 years.")
        parts.append("")
        parts.append("---")
        parts.append("")
        parts.append(f"👉 **My recommendation**: {next_step}")
        parts.append("")
        if wants_quick_job:
            parts.append("**If I were in your position**, I'd focus on getting hands-on business experience early. Internships and networking matter more than the degree itself.")
        else:
            parts.append("**If I were in your position**, I'd invest in the longer path for better career growth. Management skills compound over time.")
    
    else:
        # Generic recommendation for other interests
        return None
    
    return "\n".join(parts)


def build_final_recommendation(profile: UserProfile, query: str, force: bool = False) -> Optional[str]:
    """
    Build a final recommendation based on accumulated profile.
    
    This is the decision synthesis layer that combines:
    - Interests (what they like)
    - Constraints (what limits them)
    - Goals (what they want to achieve)
    
    NEW: Applies confidence-calibrated tone as final step.
    
    Returns a human-level recommendation with:
    - Clear path forward
    - Reasoning based on their profile
    - Trade-offs explained
    - Conflict resolution (if goals conflict)
    - Specific next steps
    - Confidence-appropriate tone
    
    Returns None if insufficient data to make recommendation OR if confidence is low (unless forced).
    
    Args:
        profile: UserProfile with interests, constraints, goals
        query: Decision query ("what should I do")
        force: If True, override uncertainty handling and provide recommendation
        
    Returns:
        Optional[str]: Human-feeling recommendation with confidence-appropriate tone or None if insufficient data
    """
    # Build base recommendation (all existing logic)
    base_recommendation = _build_base_recommendation(profile, query, force)
    
    if base_recommendation is None:
        return None
    
    # NEW: Apply confidence-appropriate tone
    # CRITICAL: Tone MUST be strictly bound to confidence_category
    final_recommendation = apply_confidence_tone(
        base_recommendation=base_recommendation,
        confidence=profile.confidence_category,
        force=force
    )
    
    return final_recommendation


def _inject_tone_prefix(recommendation: str, prefix: str) -> str:
    """
    Inject tone-appropriate prefix into recommendation opening.
    
    Strategy: Replace or prepend to the first line that starts with
    "Based on what you've told me" or similar opening phrases.
    
    Args:
        recommendation: Original recommendation text
        prefix: Tone-appropriate prefix to inject
        
    Returns:
        Recommendation with prefix injected
    """
    lines = recommendation.split("\n")
    
    # Find opening line patterns to replace
    opening_patterns = [
        "Based on what you've told me:",
        "Here's the honest path:",
        "Based on your",
    ]
    
    for i, line in enumerate(lines):
        for pattern in opening_patterns:
            if line.strip().startswith(pattern):
                # Inject prefix before this line
                lines.insert(i, prefix)
                lines.insert(i + 1, "")  # Add blank line for readability
                return "\n".join(lines)
    
    # No opening pattern found — prepend prefix to start
    return f"{prefix}\n\n{recommendation}"


def _adjust_judgment_strength(recommendation: str, judgment_phrase: str) -> str:
    """
    Adjust judgment phrase strength in recommendation.
    
    Strategy: Replace existing judgment phrases with confidence-appropriate ones.
    
    Args:
        recommendation: Recommendation text
        judgment_phrase: Confidence-appropriate judgment phrase
        
    Returns:
        Recommendation with adjusted judgment strength
    """
    # Map of phrases to replace based on judgment strength
    replacements = {
        "My recommendation": judgment_phrase,
        "I'd recommend": judgment_phrase,
        "I recommend": judgment_phrase,
    }
    
    modified = recommendation
    for old_phrase, new_phrase in replacements.items():
        modified = modified.replace(old_phrase, new_phrase)
    
    return modified


def apply_confidence_tone(
    base_recommendation: str,
    confidence: str,
    force: bool = False
) -> str:
    """
    Apply confidence-appropriate tone to a base recommendation.
    
    This is a PURE FUNCTION that transforms recommendation tone without
    modifying decision logic or accessing user profile.
    
    Architecture Constraint: This function receives a COMPLETE recommendation
    and returns a MODIFIED recommendation. It does NOT build recommendations.
    
    CRITICAL: Tone is STRICTLY bound to confidence category.
    No heuristics, no implicit logic, no bypassing.
    
    Args:
        base_recommendation: Complete recommendation string from decision engine
        confidence: User confidence category ("low", "medium", "high")
        force: Whether decision override is active
        
    Returns:
        Recommendation with confidence-appropriate tone applied
        
    Edge Cases:
        - Empty recommendation: Returns empty string
        - Invalid confidence: Defaults to "medium" tone
        - force=True + low confidence: Uses "soft decision" tone
    """
    # ASSERTION: Validate confidence category
    valid_categories = {"low", "medium", "high"}
    if confidence not in valid_categories:
        # Log warning but don't crash - default to medium
        confidence = "medium"
    
    # Edge case: empty recommendation
    if not base_recommendation or not base_recommendation.strip():
        return ""
    
    # Edge case: force override with low confidence
    # Use gentle but decisive tone (not fully confident, not purely exploratory)
    if force and confidence == "low":
        tone = ToneProfile(
            prefix="It's okay to feel unsure — but based on what you've told me, here's how I'd approach this.",
            judgment_phrase="I'd recommend",
            confidence_strength="balanced"
        )
    else:
        tone = get_tone_profile(confidence)
    
    # Surgical injection: modify only opening and judgment phrases
    modified = _inject_tone_prefix(base_recommendation, tone.prefix)
    modified = _adjust_judgment_strength(modified, tone.judgment_phrase)
    
    return modified


def get_tone_profile(confidence: str) -> ToneProfile:
    """
    Map confidence level to tone parameters.
    
    Args:
        confidence: User confidence level ("low", "medium", "high")
        
    Returns:
        ToneProfile with appropriate tone parameters
    """
    tone_map = {
        "low": ToneProfile(
            prefix="It's okay to feel unsure — but here's one way to approach this.",
            judgment_phrase="Consider",
            confidence_strength="exploratory"
        ),
        "medium": ToneProfile(
            prefix="Based on what you've told me, here's a practical path:",
            judgment_phrase="I'd recommend",
            confidence_strength="balanced"
        ),
        "high": ToneProfile(
            prefix="Based on your clear goals, here's what I'd strongly suggest:",
            judgment_phrase="I'd strongly recommend",
            confidence_strength="decisive"
        )
    }
    
    # Default to medium for invalid/missing confidence
    if confidence not in tone_map:
        return tone_map["medium"]
    
    return tone_map[confidence]


def get_confidence_adjusted_tone(profile: UserProfile) -> str:
    """
    Get response tone based on user's confidence level.

    - low confidence: slower, more questions, reassuring
    - medium confidence: balanced
    - high confidence: direct, action-oriented
    """
    if profile.confidence_category == "low":
        return "slow"
    elif profile.confidence_category == "high":
        return "direct"
    return "balanced"
