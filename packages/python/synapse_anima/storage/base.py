"""
Base interface for storage providers in Synapse Anima Agent Kit.

This module defines the abstract base class for storage/persistence systems.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime


class BaseStorageProvider(ABC):
    """Abstract base class for storage providers.

    All storage providers (Neo4j, SQLite, in-memory, etc.) must implement this interface.
    """

    # ===== User Management =====

    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data.

        Args:
            user_id: User identifier

        Returns:
            Dict with user data or None if not found
        """
        pass

    @abstractmethod
    async def create_user(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Create a new user.

        Args:
            user_id: User identifier
            **kwargs: Additional user properties

        Returns:
            Dict with created user data
        """
        pass

    # ===== Message Management =====

    @abstractmethod
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
        pass

    @abstractmethod
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
            List of message dicts with keys:
                - message_id, role, content, timestamp, metadata
        """
        pass

    # ===== Emotion Tracking =====

    @abstractmethod
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
        pass

    @abstractmethod
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
            List of emotion dicts with keys:
                - emotion, intensity, complexity, timestamp, wonder_index
        """
        pass

    # ===== Goals Management =====

    @abstractmethod
    async def save_goal(
        self,
        user_id: str,
        goal_data: Dict[str, Any],
    ) -> str:
        """Save a user goal.

        Args:
            user_id: User identifier
            goal_data: Dict with goal properties (title, description, etc.)

        Returns:
            str: Goal ID
        """
        pass

    @abstractmethod
    async def get_goals(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get user goals.

        Args:
            user_id: User identifier
            status: Optional status filter (not_started, in_progress, completed)
            limit: Maximum number of goals

        Returns:
            List of goal dicts
        """
        pass

    @abstractmethod
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
        """
        pass

    # ===== Beliefs Management =====

    @abstractmethod
    async def save_belief(
        self,
        user_id: str,
        belief_data: Dict[str, Any],
    ) -> str:
        """Save a user belief.

        Args:
            user_id: User identifier
            belief_data: Dict with belief properties (statement, category, etc.)

        Returns:
            str: Belief ID
        """
        pass

    @abstractmethod
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
        pass

    # ===== Memory Management =====

    @abstractmethod
    async def save_memory(
        self,
        user_id: str,
        memory_data: Dict[str, Any],
    ) -> str:
        """Save a core memory.

        Args:
            user_id: User identifier
            memory_data: Dict with memory properties (content, type, scope, etc.)

        Returns:
            str: Memory ID
        """
        pass

    @abstractmethod
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
            query: Search query
            memory_type: Optional type filter (goal, belief, identity, etc.)
            limit: Maximum number of results

        Returns:
            List of memory dicts
        """
        pass

    # ===== Optional Extended Methods =====
    # These methods are optional and not all providers need to implement them.
    # The API classes check for their existence with hasattr() before calling.

    async def update_belief(
        self,
        belief_id: str,
        belief_data: Dict[str, Any],
    ) -> None:
        """Update an existing belief (optional).

        Args:
            belief_id: Belief identifier
            belief_data: Updated belief data
        """
        raise NotImplementedError("update_belief not implemented by this provider")

    async def delete_belief(
        self,
        belief_id: str,
    ) -> None:
        """Delete a belief (optional).

        Args:
            belief_id: Belief identifier
        """
        raise NotImplementedError("delete_belief not implemented by this provider")

    async def delete_goal(
        self,
        goal_id: str,
    ) -> None:
        """Delete a goal (optional).

        Args:
            goal_id: Goal identifier
        """
        raise NotImplementedError("delete_goal not implemented by this provider")

    async def get_memories(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        scope: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get memories with filtering (optional).

        Args:
            user_id: User identifier
            memory_type: Optional type filter
            scope: Optional scope filter
            limit: Maximum number of memories

        Returns:
            List of memory dicts
        """
        # Default implementation using search_memories
        return await self.search_memories(
            user_id=user_id,
            query="",
            memory_type=memory_type,
            limit=limit,
        )

    async def delete_memory(
        self,
        memory_id: str,
    ) -> None:
        """Delete a memory (optional).

        Args:
            memory_id: Memory identifier
        """
        raise NotImplementedError("delete_memory not implemented by this provider")

    async def get_preferences(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get user preferences (optional).

        Args:
            user_id: User identifier

        Returns:
            Dict with user preferences
        """
        raise NotImplementedError("get_preferences not implemented by this provider")

    async def save_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
    ) -> None:
        """Save user preferences (optional).

        Args:
            user_id: User identifier
            preferences: Complete preference dict
        """
        raise NotImplementedError("save_preferences not implemented by this provider")

    # ===== Interests Management (Optional) =====
    # These methods support the user traits/interests system.

    async def save_interest(
        self,
        user_id: str,
        interest_data: Dict[str, Any],
    ) -> str:
        """Save a user interest (optional).

        Args:
            user_id: User identifier
            interest_data: Dict with interest properties:
                - name: Interest name
                - domain: Interest domain (technology, arts, etc.)
                - proficiency: User proficiency level
                - weight: Importance/engagement level 0.0-1.0
                - confidence: Detection confidence 0.0-1.0
                - keywords: Related keywords

        Returns:
            str: Interest ID
        """
        raise NotImplementedError("save_interest not implemented by this provider")

    async def get_interests(
        self,
        user_id: str,
        domain: Optional[str] = None,
        min_weight: Optional[float] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get user interests (optional).

        Args:
            user_id: User identifier
            domain: Optional domain filter
            min_weight: Optional minimum weight filter
            limit: Maximum number of interests

        Returns:
            List of interest dicts
        """
        raise NotImplementedError("get_interests not implemented by this provider")

    async def update_interest(
        self,
        interest_id: str,
        interest_data: Dict[str, Any],
    ) -> None:
        """Update an interest (optional).

        Args:
            interest_id: Interest identifier
            interest_data: Updated interest data
        """
        raise NotImplementedError("update_interest not implemented by this provider")

    async def delete_interest(
        self,
        interest_id: str,
    ) -> None:
        """Delete an interest (optional).

        Args:
            interest_id: Interest identifier
        """
        raise NotImplementedError("delete_interest not implemented by this provider")

    async def increment_interest_count(
        self,
        interest_id: str,
    ) -> Dict[str, Any]:
        """Increment interest interaction count and update last_mentioned (optional).

        Args:
            interest_id: Interest identifier

        Returns:
            Updated interest dict
        """
        raise NotImplementedError("increment_interest_count not implemented by this provider")

    # ===== Enhanced Memory Methods (Optional) =====
    # These methods support memory graduation and relationship tracking.

    async def graduate_memory(
        self,
        memory_id: str,
        new_category: str,
    ) -> None:
        """Promote memory to higher category (optional).

        Categories: transient -> session -> important -> core

        Args:
            memory_id: Memory identifier
            new_category: New category (important, core)
        """
        raise NotImplementedError("graduate_memory not implemented by this provider")

    async def increment_memory_access(
        self,
        memory_id: str,
    ) -> Dict[str, Any]:
        """Increment memory access count and check graduation eligibility (optional).

        Args:
            memory_id: Memory identifier

        Returns:
            Updated memory dict with graduation_eligible flag
        """
        raise NotImplementedError("increment_memory_access not implemented by this provider")

    # ===== Cross-Entity Relationships (Optional) =====
    # These methods support relationship discovery between entities.

    async def link_memory_to_goal(
        self,
        memory_id: str,
        goal_id: str,
    ) -> None:
        """Link memory to goal (optional).

        Args:
            memory_id: Memory identifier
            goal_id: Goal identifier
        """
        raise NotImplementedError("link_memory_to_goal not implemented by this provider")

    async def link_memory_to_interest(
        self,
        memory_id: str,
        interest_id: str,
    ) -> None:
        """Link memory to interest (optional).

        Args:
            memory_id: Memory identifier
            interest_id: Interest identifier
        """
        raise NotImplementedError("link_memory_to_interest not implemented by this provider")

    async def link_memory_to_belief(
        self,
        memory_id: str,
        belief_id: str,
    ) -> None:
        """Link memory to belief (optional).

        Args:
            memory_id: Memory identifier
            belief_id: Belief identifier
        """
        raise NotImplementedError("link_memory_to_belief not implemented by this provider")

    async def link_interest_to_goal(
        self,
        interest_id: str,
        goal_id: str,
    ) -> None:
        """Link interest to goal (optional).

        Args:
            interest_id: Interest identifier
            goal_id: Goal identifier
        """
        raise NotImplementedError("link_interest_to_goal not implemented by this provider")

    async def link_belief_to_goal(
        self,
        belief_id: str,
        goal_id: str,
    ) -> None:
        """Link belief to goal (optional).

        Args:
            belief_id: Belief identifier
            goal_id: Goal identifier
        """
        raise NotImplementedError("link_belief_to_goal not implemented by this provider")
