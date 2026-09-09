"""
Configuration management for Synapse Anima Agent Kit.

This module defines the main configuration class for the SDK.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class ChatMode(str, Enum):
    """Chat modes that determine the focus of the conversation."""
    ASK_ADVICE = "ask_advice"  # Seeking guidance and insights
    SET_GOALS = "set_goals"   # Goal-setting and planning focused
    EXPLORE = "explore"       # Open exploration and discovery


class ConversationStyle(str, Enum):
    """Conversation styles that affect the tone and approach."""
    BALANCED = "balanced"       # Emotionally intelligent with balanced approach
    THERAPEUTIC = "therapeutic" # Deep emotional support and validation
    CRISIS = "crisis"           # Immediate stabilization and grounding
    COACHING = "coaching"       # Performance optimization and growth
    CASUAL = "casual"           # Relaxed, flowing conversation
    ANALYTICAL = "analytical"   # Deep pattern analysis and insights


class PersonalityMode(str, Enum):
    """Personality modes for the agent."""
    BALANCED = "balanced"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    SUPPORTIVE = "supportive"


class ReasoningMode(str, Enum):
    """Reasoning modes for the agent."""
    QUICK = "quick"
    DEEP = "deep"


@dataclass
class AnimaConfig:
    """Configuration for Synapse Anima Agent Kit.

    This class manages all configuration options for the agent,
    including LLM provider, emotion analysis, storage, auth, and features.
    """

    # ===== Core Settings =====
    app_name: str = "Synapse Anima Agent"
    app_version: str = "1.0.0"

    # ===== LLM Settings =====
    llm_provider: str = "mistral"  # mistral, nous
    llm_model: Optional[str] = None  # Uses provider default if None
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    llm_timeout: int = 120  # seconds

    # Provider-specific API keys
    mistral_api_key: Optional[str] = None
    nous_api_key: Optional[str] = None

    # ===== Emotion Analysis Settings =====
    emotion_provider: str = "synapse"  # synapse, local
    synapse_api_key: Optional[str] = None
    synapse_base_url: str = "https://api.kaikostudios.xyz"
    synapse_timeout: int = 30  # seconds

    # ===== Storage Settings =====
    storage_provider: str = "memory"  # memory, neo4j
    storage_uri: Optional[str] = None

    # Neo4j specific
    neo4j_username: Optional[str] = None
    neo4j_password: Optional[str] = None
    neo4j_database: str = "neo4j"

    # ===== Auth Settings =====
    auth_provider: str = "none"  # none, jwt, supabase
    auth_secret: Optional[str] = None

    # Supabase specific
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None

    # ===== Personality Settings =====
    default_personality_mode: PersonalityMode = PersonalityMode.BALANCED
    custom_identity: Optional[str] = None  # Override ANIMA identity
    custom_guidelines: Optional[str] = None  # Additional guidelines
    enable_quirks: bool = True  # Enable personality quirks

    # ===== Context Settings =====
    max_context_messages: int = 20  # Max messages in context
    memory_inclusion: str = "relevant"  # minimal, relevant, comprehensive
    goal_visibility: str = "summary"  # hide, summary, detailed
    belief_injection: str = "light"  # disabled, light, full

    # ===== Server Settings =====
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    websocket_path: str = "/ws/chat"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    log_level: str = "INFO"

    # ===== Feature Flags =====
    enable_emotion_analysis: bool = True
    enable_memory_persistence: bool = True
    enable_crisis_detection: bool = True
    enable_breakthrough_detection: bool = True
    enable_wonder_tracking: bool = True

    @classmethod
    def from_env(cls) -> "AnimaConfig":
        """Create config from environment variables.

        Environment variables follow the pattern: ANIMA_{SETTING_NAME}
        For example: ANIMA_LLM_PROVIDER, ANIMA_STORAGE_PROVIDER

        Returns:
            AnimaConfig: Configuration loaded from environment
        """
        return cls(
            # Core
            app_name=os.getenv("ANIMA_APP_NAME", "Synapse Anima Agent"),

            # LLM
            llm_provider=os.getenv("ANIMA_LLM_PROVIDER", "mistral"),
            llm_model=os.getenv("ANIMA_LLM_MODEL"),
            llm_temperature=float(os.getenv("ANIMA_LLM_TEMPERATURE", "0.7")),
            llm_max_tokens=int(os.getenv("ANIMA_LLM_MAX_TOKENS", "4096")),
            mistral_api_key=os.getenv("MISTRAL_API_KEY"),
            nous_api_key=os.getenv("NOUS_API_KEY"),

            # Emotion
            emotion_provider=os.getenv("ANIMA_EMOTION_PROVIDER", "synapse"),
            synapse_api_key=os.getenv("SYNAPSE_API_KEY"),
            synapse_base_url=os.getenv("SYNAPSE_BASE_URL", "https://api.kaikostudios.xyz"),

            # Storage
            storage_provider=os.getenv("ANIMA_STORAGE_PROVIDER", "memory"),
            storage_uri=os.getenv("ANIMA_STORAGE_URI"),
            neo4j_username=os.getenv("NEO4J_USERNAME"),
            neo4j_password=os.getenv("NEO4J_PASSWORD"),
            neo4j_database=os.getenv("NEO4J_DATABASE", "neo4j"),

            # Auth
            auth_provider=os.getenv("ANIMA_AUTH_PROVIDER", "none"),
            auth_secret=os.getenv("ANIMA_AUTH_SECRET"),
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_anon_key=os.getenv("SUPABASE_ANON_KEY"),
            supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),

            # Server
            server_host=os.getenv("ANIMA_SERVER_HOST", "0.0.0.0"),
            server_port=int(os.getenv("ANIMA_SERVER_PORT", "8000")),
            cors_origins=os.getenv("ANIMA_CORS_ORIGINS", "*").split(","),
            log_level=os.getenv("ANIMA_LOG_LEVEL", "INFO"),

            # Features
            enable_emotion_analysis=os.getenv("ANIMA_ENABLE_EMOTIONS", "true").lower() == "true",
            enable_memory_persistence=os.getenv("ANIMA_ENABLE_MEMORY", "true").lower() == "true",
            enable_crisis_detection=os.getenv("ANIMA_ENABLE_CRISIS", "true").lower() == "true",
        )

    def validate(self) -> None:
        """Validate configuration and raise errors if invalid.

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate LLM provider
        if self.llm_provider not in ["mistral", "nous"]:
            raise ValueError(f"Invalid llm_provider: {self.llm_provider}")

        # Validate API keys
        if self.llm_provider == "mistral" and not self.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY is required when using Mistral provider")
        if self.llm_provider == "nous" and not self.nous_api_key:
            raise ValueError("NOUS_API_KEY is required when using Nous provider")

        # Validate emotion provider
        if self.enable_emotion_analysis:
            if self.emotion_provider == "synapse" and not self.synapse_api_key:
                raise ValueError("SYNAPSE_API_KEY is required for emotion analysis")

        # Validate storage
        if self.storage_provider == "neo4j":
            if not self.storage_uri:
                raise ValueError("ANIMA_STORAGE_URI is required for Neo4j storage")
            if not self.neo4j_username or not self.neo4j_password:
                raise ValueError("NEO4J_USERNAME and NEO4J_PASSWORD are required")

        # Validate auth
        if self.auth_provider == "supabase":
            if not self.supabase_url or not self.supabase_service_role_key:
                raise ValueError("Supabase URL and service role key are required")

    def get_llm_api_key(self) -> str:
        """Get the API key for the current LLM provider.

        Returns:
            str: API key for the configured LLM provider

        Raises:
            ValueError: If API key is not set
        """
        if self.llm_provider == "mistral":
            if not self.mistral_api_key:
                raise ValueError("MISTRAL_API_KEY not configured")
            return self.mistral_api_key
        elif self.llm_provider == "nous":
            if not self.nous_api_key:
                raise ValueError("NOUS_API_KEY not configured")
            return self.nous_api_key
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")
