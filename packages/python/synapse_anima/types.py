"""
Type definitions for Synapse Anima Agent Kit.

This module contains dataclasses and type definitions used throughout the SDK.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


# ===== Enums =====

class MessageRole(str, Enum):
    """Message roles in chat."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class GoalStatus(str, Enum):
    """Goal status values."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    ABANDONED = "abandoned"


class MemoryType(str, Enum):
    """Memory types."""
    GOAL = "goal"
    BREAKTHROUGH = "breakthrough"
    EMOTIONAL_PATTERN = "emotional_pattern"
    IDENTITY = "identity"
    BELIEF = "belief"
    INSIGHT = "insight"


class MemoryScope(str, Enum):
    """Memory scopes."""
    CORE = "core"  # Permanent across all contexts
    CHAT = "chat"  # Session-specific
    TRANSIENT = "transient"  # Temporary working memory


class BeliefCategory(str, Enum):
    """Belief categories."""
    VALUES = "values"
    IDENTITY = "identity"
    RELATIONSHIPS = "relationships"
    WORK = "work"
    GROWTH = "growth"
    PURPOSE = "purpose"
    ETHICS = "ethics"
    WORLD_VIEW = "world_view"


class GoalCategory(str, Enum):
    """Goal categories for classification."""
    FINANCIAL = "financial"
    PERSONAL = "personal"
    PROFESSIONAL = "professional"
    HEALTH = "health"
    LEARNING = "learning"
    CREATIVE = "creative"
    RELATIONSHIP = "relationship"
    OTHER = "other"


class GoalTimeframe(str, Enum):
    """Goal timeframe classification."""
    SHORT_TERM = "short_term"  # Days to weeks
    MEDIUM_TERM = "medium_term"  # Weeks to months
    LONG_TERM = "long_term"  # Months to years


class InterestDomain(str, Enum):
    """Interest domain categories."""
    TECHNOLOGY = "technology"
    ARTS = "arts"
    SCIENCE = "science"
    SPORTS = "sports"
    MUSIC = "music"
    LITERATURE = "literature"
    BUSINESS = "business"
    HEALTH = "health"
    TRAVEL = "travel"
    COOKING = "cooking"
    GAMING = "gaming"
    FINANCE = "finance"
    EDUCATION = "education"
    OTHER = "other"


class ProficiencyLevel(str, Enum):
    """User proficiency level for an interest."""
    CURIOUS = "curious"  # Just discovered
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class MemoryCategory(str, Enum):
    """Memory categories for graduation system."""
    CORE = "core"  # Permanent, high significance (never deleted)
    IMPORTANT = "important"  # Cross-session, frequently accessed
    SESSION = "session"  # Current session context
    TRANSIENT = "transient"  # Temporary, may be graduated or deleted


class PolyvagalState(str, Enum):
    """Polyvagal theory autonomic states."""
    VENTRAL_VAGAL = "ventral_vagal"     # Safe, social engagement (0.3-0.7 arousal)
    SYMPATHETIC = "sympathetic"          # Fight/flight mobilization (0.7-1.0 arousal)
    DORSAL_VAGAL = "dorsal_vagal"        # Shutdown, immobilization (0.0-0.3 arousal)


class YerkesDodsonZone(str, Enum):
    """Yerkes-Dodson performance zones."""
    UNDERSTIMULATED = "understimulated"  # Too low arousal (0.0-0.2)
    OPTIMAL = "optimal"                  # Peak performance (0.2-0.7)
    OVERSTIMULATED = "overstimulated"    # Declining performance (0.7-1.0)


class MemoryDomain(str, Enum):
    """Memory domain classification."""
    GENERAL = "general"
    EMOTIONAL = "emotional"
    GOAL = "goal"
    FINANCE = "finance"
    IDENTITY = "identity"
    RELATIONSHIP = "relationship"
    WORK = "work"
    INTEREST = "interest"


# ===== Core Data Classes =====

@dataclass
class ClinicalArousal:
    """10-stage clinical arousal model with polyvagal and Yerkes-Dodson mapping.

    Used for clinical assessment of emotional arousal state, mapping the
    raw 0.0-1.0 arousal value to clinical stages, polyvagal states, and
    Yerkes-Dodson performance zones.
    """
    stage: int                    # 1-10 clinical stage
    raw_value: float              # Original 0.0-1.0 value
    polyvagal_state: str          # PolyvagalState value
    yerkes_dodson_zone: str       # YerkesDodsonZone value
    description: str              # Human-readable stage description


@dataclass
class Message:
    """Chat message."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmotionalContext:
    """Emotional context for a message or interaction."""
    # Base emotions (8 primary)
    love: float = 0.0
    joy: float = 0.0
    sadness: float = 0.0
    anger: float = 0.0
    fear: float = 0.0
    surprise: float = 0.0
    trust: float = 0.0
    anticipation: float = 0.0

    # Metadata
    dominant: str = "neutral"  # Dominant emotion
    intensity: float = 0.5  # Overall intensity [0.0, 1.0]
    wonder_index: float = 0.0  # Novelty/discovery measure
    complexity: str = "simple"  # simple, moderate, complex
    discovery_level: str = "routine"  # routine, unusual, breakthrough
    paradoxes: List[str] = field(default_factory=list)  # Emotional contradictions

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmotionalContext":
        """Create from dictionary."""
        return cls(
            love=data.get("love", 0.0),
            joy=data.get("joy", 0.0),
            sadness=data.get("sadness", 0.0),
            anger=data.get("anger", 0.0),
            fear=data.get("fear", 0.0),
            surprise=data.get("surprise", 0.0),
            trust=data.get("trust", 0.0),
            anticipation=data.get("anticipation", 0.0),
            dominant=data.get("dominant", "neutral"),
            intensity=data.get("intensity", 0.5),
            wonder_index=data.get("wonder_index", 0.0),
            complexity=data.get("complexity", "simple"),
            discovery_level=data.get("discovery_level", "routine"),
            paradoxes=data.get("paradoxes", []),
        )


@dataclass
class EmotionalTrajectoryPoint:
    """Point in emotional trajectory."""
    emotion: str
    intensity: float
    complexity: float
    timestamp: datetime
    wonder_index: float = 0.0
    discovery_level: str = "routine"


@dataclass
class Goal:
    """User goal."""
    goal_id: str
    user_id: str
    title: str
    description: str
    category: str  # Can use GoalCategory enum value
    priority: int = 3  # 1-5
    status: GoalStatus = GoalStatus.NOT_STARTED
    progress: float = 0.0  # 0.0-1.0
    deadline: Optional[datetime] = None
    wonder_index: float = 0.0
    emotional_intensity: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Enhanced fields for traits detection
    timeframe: Optional[str] = None  # GoalTimeframe value
    measurable_target: Optional[str] = None  # e.g., "$10,000", "10 pounds"
    confidence: float = 0.5  # Detection confidence 0.0-1.0
    keywords: List[str] = field(default_factory=list)

    # Relationships
    sub_goals: List[str] = field(default_factory=list)  # Sub-goal IDs
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    obstacles: List[Dict[str, Any]] = field(default_factory=list)
    related_memories: List[str] = field(default_factory=list)
    driven_by_beliefs: List[str] = field(default_factory=list)  # Belief IDs
    related_interests: List[str] = field(default_factory=list)  # Interest IDs


@dataclass
class Belief:
    """User belief."""
    belief_id: str
    user_id: str
    category: BeliefCategory
    statement: str
    strength: float = 0.5  # 0.0-1.0
    established_date: datetime = field(default_factory=datetime.now)
    user_confirmed: bool = False

    # Enhanced fields for traits detection
    reference_count: int = 0  # Times this belief was referenced
    last_referenced: Optional[datetime] = None
    confidence: float = 0.5  # Detection confidence 0.0-1.0
    keywords: List[str] = field(default_factory=list)

    # Emotional signature
    emotional_signature: Optional[Dict[str, Any]] = None

    # Relationships
    related_experiences: List[str] = field(default_factory=list)
    related_goals: List[str] = field(default_factory=list)


@dataclass
class CoreMemory:
    """Core memory."""
    memory_id: str
    user_id: str
    content: str
    memory_type: MemoryType
    scope: MemoryScope = MemoryScope.CORE
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    emotional_signature: Optional[Dict[str, Any]] = None
    wonder_index: float = 0.0
    thread_count: int = 0  # Number of threads this memory appears in

    # Enhanced fields for graduation system
    category: str = "session"  # MemoryCategory value
    domain: str = "general"  # MemoryDomain value
    significance: float = 0.5  # 0.0-1.0 importance score
    access_count: int = 0  # Times this memory was accessed
    connection_count: int = 0  # Number of linked entities
    last_accessed: Optional[datetime] = None
    graduation_eligible: bool = False

    # Relationships
    relates_to_goals: List[str] = field(default_factory=list)
    involves_interests: List[str] = field(default_factory=list)
    aligns_with_beliefs: List[str] = field(default_factory=list)


@dataclass
class Interest:
    """User interest with proficiency tracking."""
    interest_id: str
    user_id: str
    name: str
    domain: str = "other"  # InterestDomain value
    proficiency: str = "curious"  # ProficiencyLevel value
    weight: float = 0.5  # 0.0-1.0 engagement/importance level
    confidence: float = 0.5  # Detection confidence 0.0-1.0
    keywords: List[str] = field(default_factory=list)
    interaction_count: int = 1  # Times mentioned/referenced
    first_mentioned: datetime = field(default_factory=datetime.now)
    last_mentioned: datetime = field(default_factory=datetime.now)

    # Relationships
    related_goals: List[str] = field(default_factory=list)
    related_memories: List[str] = field(default_factory=list)
    source_messages: List[str] = field(default_factory=list)  # Message IDs where detected


@dataclass
class ExtractedTrait:
    """Base class for extracted traits from conversation."""
    trait_type: str  # "goal", "belief", "interest", "memory"
    content: str
    confidence: float  # Detection confidence 0.0-1.0
    keywords: List[str] = field(default_factory=list)
    source_text: str = ""  # Original text that triggered extraction
    category: Optional[str] = None  # Category classification
    metadata: Dict[str, Any] = field(default_factory=dict)


# ===== Detected Trait Types (lightweight, pre-storage) =====

@dataclass
class DetectedGoal:
    """Goal detected from conversation (lightweight, pre-storage).

    These fields match what Kaya reads from goals_detected:
    title, description, category, confidence
    """
    title: str
    description: str
    category: str
    confidence: float
    keywords: List[str] = field(default_factory=list)
    timeframe: Optional[str] = None
    measurable_target: Optional[str] = None


@dataclass
class DetectedBelief:
    """Belief detected from conversation (lightweight, pre-storage).

    These fields match what Kaya reads from beliefs_detected:
    statement, category, confidence
    """
    statement: str
    category: str
    confidence: float
    keywords: List[str] = field(default_factory=list)


@dataclass
class DetectedInterest:
    """Interest detected from conversation (lightweight, pre-storage)."""
    name: str
    domain: str
    proficiency: str
    weight: float
    confidence: float
    keywords: List[str] = field(default_factory=list)


@dataclass
class Breakthrough:
    """Breakthrough moment."""
    breakthrough_id: str
    user_id: str
    type: str
    significance: float  # 0.0-1.0
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    related_goals: List[str] = field(default_factory=list)
    emotional_context: Optional[EmotionalContext] = None


# ===== Response Types =====

@dataclass
class ChatResponse:
    """Response from agent chat."""
    content: str
    emotions: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None
    goals_detected: List[Dict[str, Any]] = field(default_factory=list)
    beliefs_detected: List[Dict[str, Any]] = field(default_factory=list)
    interests_detected: List[Dict[str, Any]] = field(default_factory=list)
    memories_detected: List[Dict[str, Any]] = field(default_factory=list)
    wonder_index: float = 0.0
    breakthrough_detected: bool = False
    crisis_detected: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    context_metadata: Optional[Dict[str, Any]] = None  # Goals, beliefs, memories, emotions used
    llm_usage: Optional[Dict[str, Any]] = None  # Token counts including reasoning_tokens


@dataclass
class StreamChunk:
    """Chunk of streamed response.

    Used by stream_chat() for token-by-token streaming.

    Attributes:
        content: Token(s) content
        chunk_type: Type of chunk - "token" for content, "status" for pipeline updates, "done" for completion
        done: Whether this is the final chunk
        metadata: Optional metadata (e.g., usage stats on final chunk)
    """
    content: str
    chunk_type: str = "token"  # "token" | "status" | "done"
    done: bool = False
    metadata: Optional[Dict[str, Any]] = None


# ===== Agent Preferences =====

@dataclass
class AgentPreferences:
    """Agent personality and behavior preferences."""

    # Personality settings
    communication_style: str = "balanced"  # formal, casual, technical, supportive
    response_verbosity: str = "balanced"  # concise, balanced, detailed, comprehensive
    energy_level: str = "medium"  # low, medium, high
    certainty_expression: str = "confident"  # hedged, cautious, confident, direct
    emoji_usage: str = "minimal"  # never, minimal, moderate, frequent
    proactivity: str = "balanced"  # reactive, balanced, proactive

    # Context settings
    memory_inclusion: str = "relevant"  # minimal, relevant, comprehensive
    goal_visibility: str = "summary"  # hide, summary, detailed
    belief_injection: str = "light"  # disabled, light, full
    emotional_tracking: str = "subtle"  # disabled, subtle, explicit
    conversation_history_depth: int = 20  # Number of messages to include

    # Tool settings
    auto_tool_execution: str = "ask_expensive"  # ask_always, ask_expensive, auto_all
    tool_verbosity: str = "summary"  # silent, summary, detailed
