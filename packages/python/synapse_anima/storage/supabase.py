"""
Supabase Postgres storage provider for Synapse Anima Agent Kit.

This module provides a Supabase implementation using Postgres with RLS support
for user profiles, chat sessions, messages, and agent preferences.
"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from postgrest.exceptions import APIError

from .base import BaseStorageProvider


class SupabaseStorageProvider(BaseStorageProvider):
    """Supabase Postgres storage provider.

    This provider uses Supabase (Postgres) for storage with Row Level Security (RLS)
    support. It implements the schema from the specification with tables for:
    - profiles: User profile information
    - chat_sessions: Chat session metadata
    - chat_messages: Individual chat messages
    - agent_preferences: User-specific agent configuration

    Additionally supports:
    - goals: User goals tracking
    - beliefs: Core beliefs
    - memories: Core memories
    - emotions: Emotional trajectory points

    Example:
        ```python
        async with SupabaseStorageProvider(
            url="https://your-project.supabase.co",
            key="your-anon-key"
        ) as storage:
            await storage.create_user("user123", display_name="Alice")
            user = await storage.get_user("user123")
        ```
    """

    def __init__(
        self,
        url: str,
        key: str,
        schema: str = "public",
        auto_refresh_token: bool = True,
        persist_session: bool = True,
    ):
        """Initialize the Supabase storage provider.

        Args:
            url: Supabase project URL
            key: Supabase anonymous or service role key
            schema: Database schema (default: "public")
            auto_refresh_token: Auto refresh auth tokens
            persist_session: Persist session to local storage
        """
        self._url = url
        self._key = key
        self._schema = schema
        self._auto_refresh_token = auto_refresh_token
        self._persist_session = persist_session
        self._client: Optional[Client] = None

    async def __aenter__(self):
        """Async context manager entry."""
        options = ClientOptions(
            schema=self._schema,
            auto_refresh_token=self._auto_refresh_token,
            persist_session=self._persist_session,
        )

        self._client = create_client(
            supabase_url=self._url,
            supabase_key=self._key,
            options=options,
        )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            # Close any open connections
            self._client = None

    def _check_client(self):
        """Check if client is initialized."""
        if not self._client:
            raise RuntimeError(
                "Supabase client not initialized. Use 'async with' context manager."
            )

    def _handle_error(self, error: Exception, operation: str):
        """Handle and wrap Supabase errors."""
        if isinstance(error, APIError):
            raise ValueError(f"{operation} failed: {error.message}") from error
        raise

    # ===== User Management =====

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data.

        Args:
            user_id: User identifier (UUID)

        Returns:
            Dict with user data or None if not found
        """
        self._check_client()

        try:
            response = self._client.table("profiles").select("*").eq("id", user_id).execute()

            if not response.data:
                return None

            return response.data[0]
        except Exception as e:
            self._handle_error(e, "Get user")

    async def create_user(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Create a new user.

        Args:
            user_id: User identifier (UUID)
            **kwargs: Additional user properties (display_name, avatar_url, etc.)

        Returns:
            Dict with created user data

        Raises:
            ValueError: If user already exists
        """
        self._check_client()

        # Check if user exists
        existing = await self.get_user(user_id)
        if existing:
            raise ValueError(f"User {user_id} already exists")

        try:
            user_data = {
                "id": user_id,
                "display_name": kwargs.get("display_name"),
                "avatar_url": kwargs.get("avatar_url"),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Add any additional fields
            for key, value in kwargs.items():
                if key not in ["display_name", "avatar_url"]:
                    user_data[key] = value

            response = self._client.table("profiles").insert(user_data).execute()

            return response.data[0]
        except Exception as e:
            self._handle_error(e, "Create user")

    # ===== Message Management =====

    async def save_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> str:
        """Save a chat message.

        Args:
            user_id: User identifier
            session_id: Session/context identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata (emotions, reasoning, etc.)
            timestamp: Optional timestamp (defaults to now)

        Returns:
            str: Message ID
        """
        self._check_client()

        try:
            # Ensure session exists
            session_response = (
                self._client.table("chat_sessions")
                .select("session_id")
                .eq("session_id", session_id)
                .execute()
            )

            if not session_response.data:
                # Create session
                session_data = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "last_message_at": datetime.utcnow().isoformat(),
                    "message_count": 0,
                }
                self._client.table("chat_sessions").insert(session_data).execute()

            # Save message
            message_id = str(uuid.uuid4())
            message_data = {
                "message_id": message_id,
                "session_id": session_id,
                "user_id": user_id,
                "role": role,
                "content": content,
                "metadata": metadata or {},
                "timestamp": (timestamp or datetime.utcnow()).isoformat(),
            }

            self._client.table("chat_messages").insert(message_data).execute()

            # Update session
            self._client.table("chat_sessions").update({
                "last_message_at": datetime.utcnow().isoformat(),
                "message_count": session_response.data[0].get("message_count", 0) + 1
                if session_response.data else 1,
            }).eq("session_id", session_id).execute()

            return message_id
        except Exception as e:
            self._handle_error(e, "Save message")

    async def get_messages(
        self,
        user_id: str,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get recent messages for a session.

        Args:
            user_id: User identifier
            session_id: Session/context identifier
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of message dicts
        """
        self._check_client()

        try:
            response = (
                self._client.table("chat_messages")
                .select("*")
                .eq("user_id", user_id)
                .eq("session_id", session_id)
                .order("timestamp", desc=False)
                .range(offset, offset + limit - 1)
                .execute()
            )

            return response.data
        except Exception as e:
            self._handle_error(e, "Get messages")

    # ===== Emotion Tracking =====

    async def save_emotion(
        self,
        user_id: str,
        session_id: str,
        emotion_data: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Save emotional state.

        Args:
            user_id: User identifier
            session_id: Session/context identifier
            emotion_data: Dict with emotion analysis results
            timestamp: Optional timestamp (defaults to now)
        """
        self._check_client()

        try:
            emotion_entry = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "session_id": session_id,
                "emotion": emotion_data.get("emotion", "unknown"),
                "intensity": emotion_data.get("intensity", 0.0),
                "complexity": emotion_data.get("complexity", 0.0),
                "wonder_index": emotion_data.get("wonder_index", 0.0),
                "metadata": {
                    k: v for k, v in emotion_data.items()
                    if k not in ["emotion", "intensity", "complexity", "wonder_index"]
                },
                "timestamp": (timestamp or datetime.utcnow()).isoformat(),
            }

            self._client.table("emotions").insert(emotion_entry).execute()
        except Exception as e:
            self._handle_error(e, "Save emotion")

    async def get_emotional_trajectory(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get recent emotional trajectory.

        Args:
            user_id: User identifier
            session_id: Optional session filter (None = all sessions)
            limit: Maximum number of emotion points

        Returns:
            List of emotion dicts
        """
        self._check_client()

        try:
            query = self._client.table("emotions").select("*").eq("user_id", user_id)

            if session_id:
                query = query.eq("session_id", session_id)

            response = query.order("timestamp", desc=False).limit(limit).execute()

            return response.data
        except Exception as e:
            self._handle_error(e, "Get emotional trajectory")

    # ===== Goals Management =====

    async def save_goal(
        self,
        user_id: str,
        goal_data: Dict[str, Any],
    ) -> str:
        """Save a user goal.

        Args:
            user_id: User identifier
            goal_data: Dict with goal properties

        Returns:
            str: Goal ID
        """
        self._check_client()

        try:
            goal_id = str(uuid.uuid4())
            goal = {
                "id": goal_id,
                "user_id": user_id,
                "title": goal_data.get("title", ""),
                "description": goal_data.get("description", ""),
                "category": goal_data.get("category", "general"),
                "priority": goal_data.get("priority", 5),
                "status": goal_data.get("status", "not_started"),
                "progress": goal_data.get("progress", 0.0),
                "wonder_index": goal_data.get("wonder_index", 0.0),
                "emotional_intensity": goal_data.get("emotional_intensity", 0.0),
                "metadata": {
                    k: v for k, v in goal_data.items()
                    if k not in ["title", "description", "category", "priority",
                                 "status", "progress", "wonder_index", "emotional_intensity"]
                },
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            self._client.table("goals").insert(goal).execute()

            return goal_id
        except Exception as e:
            self._handle_error(e, "Save goal")

    async def get_goals(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get user goals.

        Args:
            user_id: User identifier
            status: Optional status filter
            limit: Maximum number of goals

        Returns:
            List of goal dicts
        """
        self._check_client()

        try:
            query = self._client.table("goals").select("*").eq("user_id", user_id)

            if status:
                query = query.eq("status", status)

            response = (
                query.order("priority", desc=True)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            return response.data
        except Exception as e:
            self._handle_error(e, "Get goals")

    async def update_goal_progress(
        self,
        goal_id: str,
        progress: float,
        status: Optional[str] = None,
    ) -> None:
        """Update goal progress.

        Args:
            goal_id: Goal identifier
            progress: Progress value 0.0-1.0
            status: Optional new status

        Raises:
            ValueError: If goal not found or progress is out of range
        """
        self._check_client()

        if not 0.0 <= progress <= 1.0:
            raise ValueError(f"Progress must be between 0.0 and 1.0, got {progress}")

        try:
            update_data = {
                "progress": progress,
                "updated_at": datetime.utcnow().isoformat(),
            }

            if status:
                update_data["status"] = status

            response = (
                self._client.table("goals")
                .update(update_data)
                .eq("id", goal_id)
                .execute()
            )

            if not response.data:
                raise ValueError(f"Goal {goal_id} not found")
        except Exception as e:
            self._handle_error(e, "Update goal progress")

    # ===== Beliefs Management =====

    async def save_belief(
        self,
        user_id: str,
        belief_data: Dict[str, Any],
    ) -> str:
        """Save a user belief.

        Args:
            user_id: User identifier
            belief_data: Dict with belief properties

        Returns:
            str: Belief ID
        """
        self._check_client()

        try:
            belief_id = str(uuid.uuid4())
            belief = {
                "id": belief_id,
                "user_id": user_id,
                "category": belief_data.get("category", "general"),
                "statement": belief_data.get("statement", ""),
                "strength": belief_data.get("strength", 0.5),
                "user_confirmed": belief_data.get("user_confirmed", False),
                "metadata": {
                    k: v for k, v in belief_data.items()
                    if k not in ["category", "statement", "strength", "user_confirmed"]
                },
                "established_date": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            self._client.table("beliefs").insert(belief).execute()

            return belief_id
        except Exception as e:
            self._handle_error(e, "Save belief")

    async def get_beliefs(
        self,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get user beliefs.

        Args:
            user_id: User identifier
            category: Optional category filter
            limit: Maximum number of beliefs

        Returns:
            List of belief dicts
        """
        self._check_client()

        try:
            query = self._client.table("beliefs").select("*").eq("user_id", user_id)

            if category:
                query = query.eq("category", category)

            response = query.order("strength", desc=True).limit(limit).execute()

            return response.data
        except Exception as e:
            self._handle_error(e, "Get beliefs")

    # ===== Memory Management =====

    async def save_memory(
        self,
        user_id: str,
        memory_data: Dict[str, Any],
    ) -> str:
        """Save a core memory.

        Args:
            user_id: User identifier
            memory_data: Dict with memory properties

        Returns:
            str: Memory ID
        """
        self._check_client()

        try:
            memory_id = str(uuid.uuid4())
            memory = {
                "id": memory_id,
                "user_id": user_id,
                "content": memory_data.get("content", ""),
                "memory_type": memory_data.get("memory_type", "general"),
                "scope": memory_data.get("scope", "core"),
                "wonder_index": memory_data.get("wonder_index", 0.0),
                "metadata": {
                    k: v for k, v in memory_data.items()
                    if k not in ["content", "memory_type", "scope", "wonder_index"]
                },
                "timestamp": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            self._client.table("memories").insert(memory).execute()

            return memory_id
        except Exception as e:
            self._handle_error(e, "Save memory")

    async def search_memories(
        self,
        user_id: str,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search memories by content.

        Args:
            user_id: User identifier
            query: Search query (uses full-text search or ILIKE)
            memory_type: Optional type filter
            limit: Maximum number of results

        Returns:
            List of memory dicts
        """
        self._check_client()

        try:
            # Use ILIKE for case-insensitive search
            search_pattern = f"%{query}%"

            query_builder = (
                self._client.table("memories")
                .select("*")
                .eq("user_id", user_id)
                .ilike("content", search_pattern)
            )

            if memory_type:
                query_builder = query_builder.eq("memory_type", memory_type)

            response = (
                query_builder.order("wonder_index", desc=True)
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )

            return response.data
        except Exception as e:
            self._handle_error(e, "Search memories")

    # ===== Additional Supabase-specific Methods =====

    async def get_agent_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get agent preferences for a user.

        Args:
            user_id: User identifier

        Returns:
            Dict with agent preferences or None if not found
        """
        self._check_client()

        try:
            response = (
                self._client.table("agent_preferences")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if not response.data:
                return None

            return response.data[0]
        except Exception as e:
            self._handle_error(e, "Get agent preferences")

    async def save_agent_preferences(
        self,
        user_id: str,
        personality_settings: Optional[Dict[str, Any]] = None,
        context_settings: Optional[Dict[str, Any]] = None,
        tool_settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Save agent preferences for a user.

        Args:
            user_id: User identifier
            personality_settings: Personality configuration
            context_settings: Context/memory configuration
            tool_settings: Tool usage configuration

        Returns:
            Dict with saved preferences
        """
        self._check_client()

        try:
            # Check if preferences exist
            existing = await self.get_agent_preferences(user_id)

            preferences_data = {
                "user_id": user_id,
                "personality_settings": personality_settings or {},
                "context_settings": context_settings or {},
                "tool_settings": tool_settings or {},
                "updated_at": datetime.utcnow().isoformat(),
            }

            if existing:
                # Update existing preferences
                response = (
                    self._client.table("agent_preferences")
                    .update(preferences_data)
                    .eq("user_id", user_id)
                    .execute()
                )
            else:
                # Insert new preferences
                response = (
                    self._client.table("agent_preferences")
                    .insert(preferences_data)
                    .execute()
                )

            return response.data[0]
        except Exception as e:
            self._handle_error(e, "Save agent preferences")

    async def get_chat_sessions(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get user's chat sessions.

        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of session dicts
        """
        self._check_client()

        try:
            response = (
                self._client.table("chat_sessions")
                .select("*")
                .eq("user_id", user_id)
                .order("last_message_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            return response.data
        except Exception as e:
            self._handle_error(e, "Get chat sessions")

    async def update_chat_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Update a chat session.

        Args:
            session_id: Session identifier
            title: Optional session title
            **kwargs: Additional fields to update

        Returns:
            Dict with updated session data
        """
        self._check_client()

        try:
            update_data = {"updated_at": datetime.utcnow().isoformat()}

            if title:
                update_data["title"] = title

            update_data.update(kwargs)

            response = (
                self._client.table("chat_sessions")
                .update(update_data)
                .eq("session_id", session_id)
                .execute()
            )

            if not response.data:
                raise ValueError(f"Session {session_id} not found")

            return response.data[0]
        except Exception as e:
            self._handle_error(e, "Update chat session")
