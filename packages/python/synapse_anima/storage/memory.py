"""
In-memory storage provider for Synapse Anima Agent Kit.

This module provides a dictionary-based in-memory storage implementation
for development and testing purposes. Data is not persisted between sessions.
"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

from .base import BaseStorageProvider


class InMemoryStorageProvider(BaseStorageProvider):
    """In-memory storage provider using Python dictionaries.

    This provider stores all data in memory using dictionaries. It's suitable for
    development, testing, and scenarios where persistence is not required.

    All data is lost when the application terminates.

    Example:
        ```python
        async with InMemoryStorageProvider() as storage:
            await storage.create_user("user123", name="Alice")
            user = await storage.get_user("user123")
        ```
    """

    def __init__(self):
        """Initialize the in-memory storage provider."""
        self._users: Dict[str, Dict[str, Any]] = {}
        self._messages: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._emotions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._goals: Dict[str, Dict[str, Any]] = {}
        self._user_goals: Dict[str, List[str]] = defaultdict(list)
        self._beliefs: Dict[str, Dict[str, Any]] = {}
        self._user_beliefs: Dict[str, List[str]] = defaultdict(list)
        self._memories: Dict[str, Dict[str, Any]] = {}
        self._user_memories: Dict[str, List[str]] = defaultdict(list)
        # Interest storage
        self._interests: Dict[str, Dict[str, Any]] = {}
        self._user_interests: Dict[str, List[str]] = defaultdict(list)
        self._initialized = True  # Auto-initialize for simplicity

    async def __aenter__(self):
        """Async context manager entry."""
        self._initialized = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self._initialized = False
        # Clear all data on exit
        self._users.clear()
        self._messages.clear()
        self._emotions.clear()
        self._goals.clear()
        self._user_goals.clear()
        self._beliefs.clear()
        self._user_beliefs.clear()
        self._memories.clear()
        self._user_memories.clear()
        self._interests.clear()
        self._user_interests.clear()

    def _check_initialized(self):
        """Check if the provider is initialized."""
        if not self._initialized:
            raise RuntimeError(
                "Storage provider not initialized. Use 'async with' context manager."
            )

    # ===== User Management =====

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data.

        Args:
            user_id: User identifier

        Returns:
            Dict with user data or None if not found
        """
        self._check_initialized()
        return self._users.get(user_id)

    async def create_user(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Create a new user.

        Args:
            user_id: User identifier
            **kwargs: Additional user properties (name, email, etc.)

        Returns:
            Dict with created user data

        Raises:
            ValueError: If user already exists
        """
        self._check_initialized()

        if user_id in self._users:
            raise ValueError(f"User {user_id} already exists")

        user_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            **kwargs
        }

        self._users[user_id] = user_data
        return user_data

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
        self._check_initialized()

        message_id = str(uuid.uuid4())
        message = {
            "message_id": message_id,
            "user_id": user_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": timestamp or datetime.utcnow(),
        }

        key = f"{user_id}:{session_id}"
        self._messages[key].append(message)

        return message_id

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
        self._check_initialized()

        key = f"{user_id}:{session_id}"
        messages = self._messages.get(key, [])

        # Sort by timestamp (most recent last)
        sorted_messages = sorted(messages, key=lambda m: m["timestamp"])

        # Apply offset and limit
        return sorted_messages[offset:offset + limit]

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
                (emotion, intensity, complexity, wonder_index, etc.)
            timestamp: Optional timestamp (defaults to now)
        """
        self._check_initialized()

        emotion_entry = {
            **emotion_data,
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": timestamp or datetime.utcnow(),
        }

        key = f"{user_id}:{session_id}"
        self._emotions[key].append(emotion_entry)

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
        self._check_initialized()

        if session_id:
            # Get emotions for specific session
            key = f"{user_id}:{session_id}"
            emotions = self._emotions.get(key, [])
        else:
            # Get emotions across all sessions for this user
            emotions = []
            for key, emotion_list in self._emotions.items():
                if key.startswith(f"{user_id}:"):
                    emotions.extend(emotion_list)

        # Sort by timestamp (most recent last)
        sorted_emotions = sorted(emotions, key=lambda e: e["timestamp"])

        # Return most recent emotions up to limit
        return sorted_emotions[-limit:] if len(sorted_emotions) > limit else sorted_emotions

    # ===== Goals Management =====

    async def save_goal(
        self,
        user_id: str,
        goal_data: Dict[str, Any],
    ) -> str:
        """Save a user goal.

        Args:
            user_id: User identifier
            goal_data: Dict with goal properties (title, description,
                category, priority, status, progress, etc.)

        Returns:
            str: Goal ID
        """
        self._check_initialized()

        # Check if updating existing goal or creating new one
        goal_id = goal_data.get("goal_id")
        if goal_id and goal_id in self._goals:
            # Update existing goal
            self._goals[goal_id].update(goal_data)
        else:
            # Create new goal
            if not goal_id:
                goal_id = str(uuid.uuid4())

            goal = {
                "goal_id": goal_id,
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "status": "not_started",
                "progress": 0.0,
                **goal_data,
            }

            self._goals[goal_id] = goal
            if goal_id not in self._user_goals[user_id]:
                self._user_goals[user_id].append(goal_id)

        return goal_id

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
        self._check_initialized()

        goal_ids = self._user_goals.get(user_id, [])
        goals = [self._goals[gid] for gid in goal_ids if gid in self._goals]

        # Filter by status if provided
        if status:
            goals = [g for g in goals if g.get("status") == status]

        # Sort by created_at (most recent first)
        goals.sort(key=lambda g: g.get("created_at", datetime.min), reverse=True)

        return goals[:limit]

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
        self._check_initialized()

        if goal_id not in self._goals:
            raise ValueError(f"Goal {goal_id} not found")

        if not 0.0 <= progress <= 1.0:
            raise ValueError(f"Progress must be between 0.0 and 1.0, got {progress}")

        self._goals[goal_id]["progress"] = progress
        self._goals[goal_id]["updated_at"] = datetime.utcnow()

        if status:
            self._goals[goal_id]["status"] = status

    # ===== Beliefs Management =====

    async def save_belief(
        self,
        user_id: str,
        belief_data: Dict[str, Any],
    ) -> str:
        """Save a user belief.

        Args:
            user_id: User identifier
            belief_data: Dict with belief properties (statement, category,
                strength, user_confirmed, etc.)

        Returns:
            str: Belief ID
        """
        self._check_initialized()

        # Check if updating existing belief or creating new one
        belief_id = belief_data.get("belief_id")
        if belief_id and belief_id in self._beliefs:
            # Update existing belief
            self._beliefs[belief_id].update(belief_data)
        else:
            # Create new belief
            if not belief_id:
                belief_id = str(uuid.uuid4())

            belief = {
                "belief_id": belief_id,
                "user_id": user_id,
                "established_date": datetime.utcnow(),
                "strength": 0.5,
                "user_confirmed": False,
                **belief_data,
            }

            self._beliefs[belief_id] = belief
            if belief_id not in self._user_beliefs[user_id]:
                self._user_beliefs[user_id].append(belief_id)

        return belief_id

    async def get_beliefs(
        self,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get user beliefs.

        Args:
            user_id: User identifier
            category: Optional category filter (values, identity, relationships, etc.)
            limit: Maximum number of beliefs

        Returns:
            List of belief dicts
        """
        self._check_initialized()

        belief_ids = self._user_beliefs.get(user_id, [])
        beliefs = [self._beliefs[bid] for bid in belief_ids if bid in self._beliefs]

        # Filter by category if provided
        if category:
            beliefs = [b for b in beliefs if b.get("category") == category]

        # Sort by strength (strongest first)
        beliefs.sort(key=lambda b: b.get("strength", 0.0), reverse=True)

        return beliefs[:limit]

    # ===== Memory Management =====

    async def save_memory(
        self,
        user_id: str,
        memory_data: Dict[str, Any],
    ) -> str:
        """Save a core memory.

        Args:
            user_id: User identifier
            memory_data: Dict with memory properties (content, type, scope,
                wonder_index, etc.)

        Returns:
            str: Memory ID
        """
        self._check_initialized()

        # Check if updating existing memory or creating new one
        memory_id = memory_data.get("memory_id")
        if memory_id and memory_id in self._memories:
            # Update existing memory
            self._memories[memory_id].update(memory_data)
        else:
            # Create new memory
            if not memory_id:
                memory_id = str(uuid.uuid4())

            memory = {
                "memory_id": memory_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow(),
                "scope": "core",
                **memory_data,
            }

            self._memories[memory_id] = memory
            if memory_id not in self._user_memories[user_id]:
                self._user_memories[user_id].append(memory_id)

        return memory_id

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
            query: Search query (simple substring match)
            memory_type: Optional type filter (goal, belief, identity,
                breakthrough, insight, etc.)
            limit: Maximum number of results

        Returns:
            List of memory dicts, sorted by relevance
        """
        self._check_initialized()

        memory_ids = self._user_memories.get(user_id, [])
        memories = [self._memories[mid] for mid in memory_ids if mid in self._memories]

        # Filter by type if provided
        if memory_type:
            memories = [m for m in memories if m.get("memory_type") == memory_type]

        # Simple substring search in content (case-insensitive)
        query_lower = query.lower()
        matching_memories = []

        for memory in memories:
            content = memory.get("content", "").lower()
            if query_lower in content:
                # Calculate simple relevance score based on position
                position = content.find(query_lower)
                relevance = 1.0 / (position + 1)  # Earlier matches score higher
                matching_memories.append((memory, relevance))

        # Sort by relevance (highest first)
        matching_memories.sort(key=lambda x: x[1], reverse=True)

        # Return just the memories (without scores), up to limit
        return [m for m, _ in matching_memories[:limit]]

    # ===== Optional Extended Methods =====

    async def update_belief(
        self,
        belief_id: str,
        belief_data: Dict[str, Any],
    ) -> None:
        """Update an existing belief.

        Args:
            belief_id: Belief identifier
            belief_data: Updated belief data
        """
        self._check_initialized()

        if belief_id not in self._beliefs:
            raise ValueError(f"Belief {belief_id} not found")

        self._beliefs[belief_id].update(belief_data)

    async def delete_belief(
        self,
        belief_id: str,
    ) -> None:
        """Delete a belief.

        Args:
            belief_id: Belief identifier
        """
        self._check_initialized()

        if belief_id not in self._beliefs:
            raise ValueError(f"Belief {belief_id} not found")

        # Get user_id before deleting
        user_id = self._beliefs[belief_id]["user_id"]

        # Remove from beliefs dict
        del self._beliefs[belief_id]

        # Remove from user's belief list
        if user_id in self._user_beliefs:
            self._user_beliefs[user_id] = [
                bid for bid in self._user_beliefs[user_id] if bid != belief_id
            ]

    async def delete_goal(
        self,
        goal_id: str,
    ) -> None:
        """Delete a goal.

        Args:
            goal_id: Goal identifier
        """
        self._check_initialized()

        if goal_id not in self._goals:
            raise ValueError(f"Goal {goal_id} not found")

        # Get user_id before deleting
        user_id = self._goals[goal_id]["user_id"]

        # Remove from goals dict
        del self._goals[goal_id]

        # Remove from user's goal list
        if user_id in self._user_goals:
            self._user_goals[user_id] = [
                gid for gid in self._user_goals[user_id] if gid != goal_id
            ]

    async def get_memories(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        scope: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get memories with filtering.

        Args:
            user_id: User identifier
            memory_type: Optional type filter
            scope: Optional scope filter
            limit: Maximum number of memories

        Returns:
            List of memory dicts
        """
        self._check_initialized()

        memory_ids = self._user_memories.get(user_id, [])
        memories = [self._memories[mid] for mid in memory_ids if mid in self._memories]

        # Filter by type if provided
        if memory_type:
            memories = [m for m in memories if m.get("memory_type") == memory_type]

        # Filter by scope if provided
        if scope:
            memories = [m for m in memories if m.get("scope") == scope]

        # Sort by timestamp (most recent first)
        memories.sort(key=lambda m: m.get("timestamp", datetime.min), reverse=True)

        return memories[:limit]

    async def delete_memory(
        self,
        memory_id: str,
    ) -> None:
        """Delete a memory.

        Args:
            memory_id: Memory identifier
        """
        self._check_initialized()

        if memory_id not in self._memories:
            raise ValueError(f"Memory {memory_id} not found")

        # Get user_id before deleting
        user_id = self._memories[memory_id]["user_id"]

        # Remove from memories dict
        del self._memories[memory_id]

        # Remove from user's memory list
        if user_id in self._user_memories:
            self._user_memories[user_id] = [
                mid for mid in self._user_memories[user_id] if mid != memory_id
            ]

    async def get_preferences(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get user preferences.

        Args:
            user_id: User identifier

        Returns:
            Dict with user preferences or empty dict if none set
        """
        self._check_initialized()

        # Store preferences in user data
        user = await self.get_user(user_id)
        if user and "preferences" in user:
            return user["preferences"]
        return {}

    async def save_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
    ) -> None:
        """Save user preferences.

        Args:
            user_id: User identifier
            preferences: Complete preference dict
        """
        self._check_initialized()

        # Create user if doesn't exist
        if user_id not in self._users:
            await self.create_user(user_id)

        # Update preferences in user data
        self._users[user_id]["preferences"] = preferences

    # ===== Interests Management =====

    async def save_interest(
        self,
        user_id: str,
        interest_data: Dict[str, Any],
    ) -> str:
        """Save a user interest.

        Args:
            user_id: User identifier
            interest_data: Dict with interest properties (name, domain,
                proficiency, weight, confidence, keywords, etc.)

        Returns:
            str: Interest ID
        """
        self._check_initialized()

        # Check if updating existing interest or creating new one
        interest_id = interest_data.get("interest_id")
        if interest_id and interest_id in self._interests:
            # Update existing interest
            self._interests[interest_id].update(interest_data)
            self._interests[interest_id]["last_mentioned"] = datetime.utcnow()
        else:
            # Create new interest
            if not interest_id:
                interest_id = str(uuid.uuid4())

            now = datetime.utcnow()
            interest = {
                "interest_id": interest_id,
                "user_id": user_id,
                "domain": "other",
                "proficiency": "curious",
                "weight": 0.5,
                "confidence": 0.5,
                "keywords": [],
                "interaction_count": 1,
                "first_mentioned": now,
                "last_mentioned": now,
                "related_goals": [],
                "related_memories": [],
                **interest_data,
            }

            self._interests[interest_id] = interest
            if interest_id not in self._user_interests[user_id]:
                self._user_interests[user_id].append(interest_id)

        return interest_id

    async def get_interests(
        self,
        user_id: str,
        domain: Optional[str] = None,
        min_weight: Optional[float] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get user interests.

        Args:
            user_id: User identifier
            domain: Optional domain filter
            min_weight: Optional minimum weight filter
            limit: Maximum number of interests

        Returns:
            List of interest dicts
        """
        self._check_initialized()

        interest_ids = self._user_interests.get(user_id, [])
        interests = [
            self._interests[iid] for iid in interest_ids if iid in self._interests
        ]

        # Filter by domain if provided
        if domain:
            interests = [i for i in interests if i.get("domain") == domain]

        # Filter by min_weight if provided
        if min_weight is not None:
            interests = [i for i in interests if i.get("weight", 0) >= min_weight]

        # Sort by weight (highest first)
        interests.sort(key=lambda i: i.get("weight", 0.0), reverse=True)

        return interests[:limit]

    async def update_interest(
        self,
        interest_id: str,
        interest_data: Dict[str, Any],
    ) -> None:
        """Update an existing interest.

        Args:
            interest_id: Interest identifier
            interest_data: Updated interest data
        """
        self._check_initialized()

        if interest_id not in self._interests:
            raise ValueError(f"Interest {interest_id} not found")

        self._interests[interest_id].update(interest_data)
        self._interests[interest_id]["last_mentioned"] = datetime.utcnow()

    async def delete_interest(
        self,
        interest_id: str,
    ) -> None:
        """Delete an interest.

        Args:
            interest_id: Interest identifier
        """
        self._check_initialized()

        if interest_id not in self._interests:
            raise ValueError(f"Interest {interest_id} not found")

        # Get user_id before deleting
        user_id = self._interests[interest_id]["user_id"]

        # Remove from interests dict
        del self._interests[interest_id]

        # Remove from user's interest list
        if user_id in self._user_interests:
            self._user_interests[user_id] = [
                iid for iid in self._user_interests[user_id] if iid != interest_id
            ]

    async def increment_interest_count(
        self,
        interest_id: str,
    ) -> Dict[str, Any]:
        """Increment interest interaction count and update last_mentioned.

        Args:
            interest_id: Interest identifier

        Returns:
            Updated interest dict
        """
        self._check_initialized()

        if interest_id not in self._interests:
            raise ValueError(f"Interest {interest_id} not found")

        self._interests[interest_id]["interaction_count"] += 1
        self._interests[interest_id]["last_mentioned"] = datetime.utcnow()

        return self._interests[interest_id]

    # ===== Enhanced Memory Methods =====

    async def graduate_memory(
        self,
        memory_id: str,
        new_category: str,
    ) -> None:
        """Promote memory to higher category.

        Categories: transient -> session -> important -> core

        Args:
            memory_id: Memory identifier
            new_category: New category (important, core)
        """
        self._check_initialized()

        if memory_id not in self._memories:
            raise ValueError(f"Memory {memory_id} not found")

        self._memories[memory_id]["category"] = new_category
        self._memories[memory_id]["graduation_eligible"] = False

    async def increment_memory_access(
        self,
        memory_id: str,
    ) -> Dict[str, Any]:
        """Increment memory access count and check graduation eligibility.

        Args:
            memory_id: Memory identifier

        Returns:
            Updated memory dict with graduation_eligible flag
        """
        self._check_initialized()

        if memory_id not in self._memories:
            raise ValueError(f"Memory {memory_id} not found")

        memory = self._memories[memory_id]
        memory["access_count"] = memory.get("access_count", 0) + 1
        memory["last_accessed"] = datetime.utcnow()

        # Check graduation eligibility based on access count
        current_category = memory.get("category", "session")
        access_count = memory["access_count"]

        if current_category == "transient" and access_count >= 3:
            memory["graduation_eligible"] = True
        elif current_category == "session" and access_count >= 5:
            memory["graduation_eligible"] = True
        elif current_category == "important" and access_count >= 10:
            memory["graduation_eligible"] = True
        else:
            memory["graduation_eligible"] = False

        return memory

    # ===== Cross-Entity Relationships =====

    async def link_memory_to_goal(
        self,
        memory_id: str,
        goal_id: str,
    ) -> None:
        """Link memory to goal.

        Args:
            memory_id: Memory identifier
            goal_id: Goal identifier
        """
        self._check_initialized()

        if memory_id not in self._memories:
            raise ValueError(f"Memory {memory_id} not found")
        if goal_id not in self._goals:
            raise ValueError(f"Goal {goal_id} not found")

        # Add relationship to memory
        relates_to_goals = self._memories[memory_id].get("relates_to_goals", [])
        if goal_id not in relates_to_goals:
            relates_to_goals.append(goal_id)
            self._memories[memory_id]["relates_to_goals"] = relates_to_goals
            self._memories[memory_id]["connection_count"] = \
                self._memories[memory_id].get("connection_count", 0) + 1

        # Add relationship to goal
        related_memories = self._goals[goal_id].get("related_memories", [])
        if memory_id not in related_memories:
            related_memories.append(memory_id)
            self._goals[goal_id]["related_memories"] = related_memories

    async def link_memory_to_interest(
        self,
        memory_id: str,
        interest_id: str,
    ) -> None:
        """Link memory to interest.

        Args:
            memory_id: Memory identifier
            interest_id: Interest identifier
        """
        self._check_initialized()

        if memory_id not in self._memories:
            raise ValueError(f"Memory {memory_id} not found")
        if interest_id not in self._interests:
            raise ValueError(f"Interest {interest_id} not found")

        # Add relationship to memory
        involves_interests = self._memories[memory_id].get("involves_interests", [])
        if interest_id not in involves_interests:
            involves_interests.append(interest_id)
            self._memories[memory_id]["involves_interests"] = involves_interests
            self._memories[memory_id]["connection_count"] = \
                self._memories[memory_id].get("connection_count", 0) + 1

        # Add relationship to interest
        related_memories = self._interests[interest_id].get("related_memories", [])
        if memory_id not in related_memories:
            related_memories.append(memory_id)
            self._interests[interest_id]["related_memories"] = related_memories

    async def link_memory_to_belief(
        self,
        memory_id: str,
        belief_id: str,
    ) -> None:
        """Link memory to belief.

        Args:
            memory_id: Memory identifier
            belief_id: Belief identifier
        """
        self._check_initialized()

        if memory_id not in self._memories:
            raise ValueError(f"Memory {memory_id} not found")
        if belief_id not in self._beliefs:
            raise ValueError(f"Belief {belief_id} not found")

        # Add relationship to memory
        aligns_with_beliefs = self._memories[memory_id].get("aligns_with_beliefs", [])
        if belief_id not in aligns_with_beliefs:
            aligns_with_beliefs.append(belief_id)
            self._memories[memory_id]["aligns_with_beliefs"] = aligns_with_beliefs
            self._memories[memory_id]["connection_count"] = \
                self._memories[memory_id].get("connection_count", 0) + 1

        # Add relationship to belief
        related_experiences = self._beliefs[belief_id].get("related_experiences", [])
        if memory_id not in related_experiences:
            related_experiences.append(memory_id)
            self._beliefs[belief_id]["related_experiences"] = related_experiences

    async def link_interest_to_goal(
        self,
        interest_id: str,
        goal_id: str,
    ) -> None:
        """Link interest to goal.

        Args:
            interest_id: Interest identifier
            goal_id: Goal identifier
        """
        self._check_initialized()

        if interest_id not in self._interests:
            raise ValueError(f"Interest {interest_id} not found")
        if goal_id not in self._goals:
            raise ValueError(f"Goal {goal_id} not found")

        # Add relationship to interest
        related_goals = self._interests[interest_id].get("related_goals", [])
        if goal_id not in related_goals:
            related_goals.append(goal_id)
            self._interests[interest_id]["related_goals"] = related_goals

        # Add relationship to goal
        related_interests = self._goals[goal_id].get("related_interests", [])
        if interest_id not in related_interests:
            related_interests.append(interest_id)
            self._goals[goal_id]["related_interests"] = related_interests

    async def link_belief_to_goal(
        self,
        belief_id: str,
        goal_id: str,
    ) -> None:
        """Link belief to goal.

        Args:
            belief_id: Belief identifier
            goal_id: Goal identifier
        """
        self._check_initialized()

        if belief_id not in self._beliefs:
            raise ValueError(f"Belief {belief_id} not found")
        if goal_id not in self._goals:
            raise ValueError(f"Goal {goal_id} not found")

        # Add relationship to belief
        related_goals = self._beliefs[belief_id].get("related_goals", [])
        if goal_id not in related_goals:
            related_goals.append(goal_id)
            self._beliefs[belief_id]["related_goals"] = related_goals

        # Add relationship to goal
        driven_by_beliefs = self._goals[goal_id].get("driven_by_beliefs", [])
        if belief_id not in driven_by_beliefs:
            driven_by_beliefs.append(belief_id)
            self._goals[goal_id]["driven_by_beliefs"] = driven_by_beliefs
