"""
Neo4j graph database storage provider for Synapse Anima Agent Kit.

This module provides a full Neo4j implementation with relationship modeling
for beliefs, goals, memories, and emotional trajectories.
"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import Neo4jError

from .base import BaseStorageProvider


class Neo4jStorageProvider(BaseStorageProvider):
    """Neo4j graph database storage provider.

    This provider uses Neo4j to store user data with rich relationship modeling,
    including belief networks, goal hierarchies, and memory connections.

    Schema follows the specification with nodes for:
    - User, CoreBelief, Goal, SubGoal, Milestone, Obstacle
    - CoreMemory, EmotionalSignature, EmotionalTrajectoryPoint, Breakthrough

    Example:
        ```python
        async with Neo4jStorageProvider(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        ) as storage:
            await storage.create_user("user123", name="Alice")
            user = await storage.get_user("user123")
        ```
    """

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j",
        max_connection_lifetime: int = 3600,
        max_connection_pool_size: int = 50,
        connection_timeout: float = 30.0,
    ):
        """Initialize the Neo4j storage provider.

        Args:
            uri: Neo4j connection URI (e.g., "bolt://localhost:7687")
            user: Database username
            password: Database password
            database: Database name (default: "neo4j")
            max_connection_lifetime: Max connection lifetime in seconds
            max_connection_pool_size: Max connection pool size
            connection_timeout: Connection timeout in seconds
        """
        self._uri = uri
        self._user = user
        self._password = password
        self._database = database
        self._driver: Optional[AsyncDriver] = None
        self._max_connection_lifetime = max_connection_lifetime
        self._max_connection_pool_size = max_connection_pool_size
        self._connection_timeout = connection_timeout

    async def __aenter__(self):
        """Async context manager entry."""
        self._driver = AsyncGraphDatabase.driver(
            self._uri,
            auth=(self._user, self._password),
            max_connection_lifetime=self._max_connection_lifetime,
            max_connection_pool_size=self._max_connection_pool_size,
            connection_timeout=self._connection_timeout,
        )

        # Verify connectivity
        await self._driver.verify_connectivity()

        # Create constraints and indexes
        await self._create_constraints()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._driver:
            await self._driver.close()
            self._driver = None

    def _check_driver(self):
        """Check if driver is initialized."""
        if not self._driver:
            raise RuntimeError(
                "Neo4j driver not initialized. Use 'async with' context manager."
            )

    async def _create_constraints(self):
        """Create database constraints and indexes."""
        self._check_driver()

        constraints = [
            "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
            "CREATE CONSTRAINT belief_id IF NOT EXISTS FOR (b:CoreBelief) REQUIRE b.belief_id IS UNIQUE",
            "CREATE CONSTRAINT goal_id IF NOT EXISTS FOR (g:Goal) REQUIRE g.goal_id IS UNIQUE",
            "CREATE CONSTRAINT memory_id IF NOT EXISTS FOR (m:CoreMemory) REQUIRE m.memory_id IS UNIQUE",
            "CREATE INDEX user_created IF NOT EXISTS FOR (u:User) ON (u.created_at)",
            "CREATE INDEX goal_status IF NOT EXISTS FOR (g:Goal) ON (g.status)",
            "CREATE INDEX belief_category IF NOT EXISTS FOR (b:CoreBelief) ON (b.category)",
            "CREATE INDEX memory_type IF NOT EXISTS FOR (m:CoreMemory) ON (m.memory_type)",
        ]

        async with self._driver.session(database=self._database) as session:
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Neo4jError as e:
                    # Constraint may already exist, continue
                    if "EquivalentSchemaRuleAlreadyExists" not in str(e):
                        raise

    # ===== User Management =====

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data.

        Args:
            user_id: User identifier

        Returns:
            Dict with user data or None if not found
        """
        self._check_driver()

        query = """
        MATCH (u:User {user_id: $user_id})
        RETURN u
        """

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, user_id=user_id)
            record = await result.single()

            if not record:
                return None

            user_node = record["u"]
            return dict(user_node)

    async def create_user(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Create a new user.

        Args:
            user_id: User identifier
            **kwargs: Additional user properties

        Returns:
            Dict with created user data

        Raises:
            ValueError: If user already exists
        """
        self._check_driver()

        # Check if user exists
        existing = await self.get_user(user_id)
        if existing:
            raise ValueError(f"User {user_id} already exists")

        query = """
        CREATE (u:User {
            user_id: $user_id,
            created_at: datetime($created_at)
        })
        SET u += $properties
        RETURN u
        """

        created_at = datetime.utcnow().isoformat()
        async with self._driver.session(database=self._database) as session:
            result = await session.run(
                query,
                user_id=user_id,
                created_at=created_at,
                properties=kwargs,
            )
            record = await result.single()
            user_node = record["u"]
            return dict(user_node)

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
        self._check_driver()

        message_id = str(uuid.uuid4())
        ts = timestamp or datetime.utcnow()

        query = """
        MATCH (u:User {user_id: $user_id})
        MERGE (s:Session {session_id: $session_id, user_id: $user_id})
        CREATE (m:Message {
            message_id: $message_id,
            role: $role,
            content: $content,
            metadata: $metadata,
            timestamp: datetime($timestamp)
        })
        CREATE (u)-[:HAS_SESSION]->(s)
        CREATE (s)-[:CONTAINS_MESSAGE]->(m)
        RETURN m.message_id AS message_id
        """

        async with self._driver.session(database=self._database) as session:
            result = await session.run(
                query,
                user_id=user_id,
                session_id=session_id,
                message_id=message_id,
                role=role,
                content=content,
                metadata=metadata or {},
                timestamp=ts.isoformat(),
            )
            record = await result.single()
            return record["message_id"]

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
        self._check_driver()

        query = """
        MATCH (u:User {user_id: $user_id})-[:HAS_SESSION]->
              (s:Session {session_id: $session_id})-[:CONTAINS_MESSAGE]->(m:Message)
        RETURN m
        ORDER BY m.timestamp ASC
        SKIP $offset
        LIMIT $limit
        """

        async with self._driver.session(database=self._database) as session:
            result = await session.run(
                query,
                user_id=user_id,
                session_id=session_id,
                limit=limit,
                offset=offset,
            )

            messages = []
            async for record in result:
                message = dict(record["m"])
                messages.append(message)

            return messages

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
        self._check_driver()

        ts = timestamp or datetime.utcnow()

        query = """
        MATCH (u:User {user_id: $user_id})
        MERGE (s:Session {session_id: $session_id, user_id: $user_id})
        CREATE (et:EmotionalTrajectoryPoint {
            emotion: $emotion,
            intensity: $intensity,
            complexity: $complexity,
            wonder_index: $wonder_index,
            timestamp: datetime($timestamp)
        })
        SET et += $additional_data
        CREATE (u)-[:HAS_SESSION]->(s)
        CREATE (s)-[:HAS_EMOTIONAL_POINT]->(et)
        """

        async with self._driver.session(database=self._database) as session:
            await session.run(
                query,
                user_id=user_id,
                session_id=session_id,
                emotion=emotion_data.get("emotion", "unknown"),
                intensity=emotion_data.get("intensity", 0.0),
                complexity=emotion_data.get("complexity", 0.0),
                wonder_index=emotion_data.get("wonder_index", 0.0),
                timestamp=ts.isoformat(),
                additional_data={
                    k: v for k, v in emotion_data.items()
                    if k not in ["emotion", "intensity", "complexity", "wonder_index"]
                },
            )

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
        self._check_driver()

        if session_id:
            query = """
            MATCH (u:User {user_id: $user_id})-[:HAS_SESSION]->
                  (s:Session {session_id: $session_id})-[:HAS_EMOTIONAL_POINT]->(et:EmotionalTrajectoryPoint)
            RETURN et
            ORDER BY et.timestamp DESC
            LIMIT $limit
            """
            params = {"user_id": user_id, "session_id": session_id, "limit": limit}
        else:
            query = """
            MATCH (u:User {user_id: $user_id})-[:HAS_SESSION]->
                  (s:Session)-[:HAS_EMOTIONAL_POINT]->(et:EmotionalTrajectoryPoint)
            RETURN et
            ORDER BY et.timestamp DESC
            LIMIT $limit
            """
            params = {"user_id": user_id, "limit": limit}

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, **params)

            emotions = []
            async for record in result:
                emotion = dict(record["et"])
                emotions.append(emotion)

            # Return in chronological order (oldest first)
            return list(reversed(emotions))

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
        self._check_driver()

        goal_id = str(uuid.uuid4())

        query = """
        MATCH (u:User {user_id: $user_id})
        CREATE (g:Goal {
            goal_id: $goal_id,
            title: $title,
            description: $description,
            category: $category,
            priority: $priority,
            status: $status,
            progress: $progress,
            wonder_index: $wonder_index,
            emotional_intensity: $emotional_intensity
        })
        SET g += $additional_data
        CREATE (u)-[:PURSUES]->(g)
        RETURN g.goal_id AS goal_id
        """

        async with self._driver.session(database=self._database) as session:
            result = await session.run(
                query,
                user_id=user_id,
                goal_id=goal_id,
                title=goal_data.get("title", ""),
                description=goal_data.get("description", ""),
                category=goal_data.get("category", "general"),
                priority=goal_data.get("priority", 5),
                status=goal_data.get("status", "not_started"),
                progress=goal_data.get("progress", 0.0),
                wonder_index=goal_data.get("wonder_index", 0.0),
                emotional_intensity=goal_data.get("emotional_intensity", 0.0),
                additional_data={
                    k: v for k, v in goal_data.items()
                    if k not in ["title", "description", "category", "priority",
                                 "status", "progress", "wonder_index", "emotional_intensity"]
                },
            )
            record = await result.single()
            return record["goal_id"]

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
        self._check_driver()

        if status:
            query = """
            MATCH (u:User {user_id: $user_id})-[:PURSUES]->(g:Goal {status: $status})
            RETURN g
            ORDER BY g.priority DESC, g.created_at DESC
            LIMIT $limit
            """
            params = {"user_id": user_id, "status": status, "limit": limit}
        else:
            query = """
            MATCH (u:User {user_id: $user_id})-[:PURSUES]->(g:Goal)
            RETURN g
            ORDER BY g.priority DESC, g.created_at DESC
            LIMIT $limit
            """
            params = {"user_id": user_id, "limit": limit}

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, **params)

            goals = []
            async for record in result:
                goal = dict(record["g"])
                goals.append(goal)

            return goals

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
        self._check_driver()

        if not 0.0 <= progress <= 1.0:
            raise ValueError(f"Progress must be between 0.0 and 1.0, got {progress}")

        if status:
            query = """
            MATCH (g:Goal {goal_id: $goal_id})
            SET g.progress = $progress, g.status = $status, g.updated_at = datetime()
            RETURN g
            """
            params = {"goal_id": goal_id, "progress": progress, "status": status}
        else:
            query = """
            MATCH (g:Goal {goal_id: $goal_id})
            SET g.progress = $progress, g.updated_at = datetime()
            RETURN g
            """
            params = {"goal_id": goal_id, "progress": progress}

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, **params)
            record = await result.single()

            if not record:
                raise ValueError(f"Goal {goal_id} not found")

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
        self._check_driver()

        belief_id = str(uuid.uuid4())

        query = """
        MATCH (u:User {user_id: $user_id})
        CREATE (b:CoreBelief {
            belief_id: $belief_id,
            category: $category,
            statement: $statement,
            strength: $strength,
            established_date: datetime($established_date),
            user_confirmed: $user_confirmed
        })
        SET b += $additional_data
        CREATE (u)-[:HOLDS_BELIEF]->(b)
        RETURN b.belief_id AS belief_id
        """

        async with self._driver.session(database=self._database) as session:
            result = await session.run(
                query,
                user_id=user_id,
                belief_id=belief_id,
                category=belief_data.get("category", "general"),
                statement=belief_data.get("statement", ""),
                strength=belief_data.get("strength", 0.5),
                established_date=datetime.utcnow().isoformat(),
                user_confirmed=belief_data.get("user_confirmed", False),
                additional_data={
                    k: v for k, v in belief_data.items()
                    if k not in ["category", "statement", "strength", "user_confirmed"]
                },
            )
            record = await result.single()
            return record["belief_id"]

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
        self._check_driver()

        if category:
            query = """
            MATCH (u:User {user_id: $user_id})-[:HOLDS_BELIEF]->(b:CoreBelief {category: $category})
            RETURN b
            ORDER BY b.strength DESC
            LIMIT $limit
            """
            params = {"user_id": user_id, "category": category, "limit": limit}
        else:
            query = """
            MATCH (u:User {user_id: $user_id})-[:HOLDS_BELIEF]->(b:CoreBelief)
            RETURN b
            ORDER BY b.strength DESC
            LIMIT $limit
            """
            params = {"user_id": user_id, "limit": limit}

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, **params)

            beliefs = []
            async for record in result:
                belief = dict(record["b"])
                beliefs.append(belief)

            return beliefs

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
        self._check_driver()

        memory_id = str(uuid.uuid4())

        query = """
        MATCH (u:User {user_id: $user_id})
        CREATE (m:CoreMemory {
            memory_id: $memory_id,
            content: $content,
            memory_type: $memory_type,
            scope: $scope,
            timestamp: datetime($timestamp),
            wonder_index: $wonder_index
        })
        SET m += $additional_data
        CREATE (u)-[:HAS_CORE_MEMORY]->(m)
        RETURN m.memory_id AS memory_id
        """

        async with self._driver.session(database=self._database) as session:
            result = await session.run(
                query,
                user_id=user_id,
                memory_id=memory_id,
                content=memory_data.get("content", ""),
                memory_type=memory_data.get("memory_type", "general"),
                scope=memory_data.get("scope", "core"),
                timestamp=datetime.utcnow().isoformat(),
                wonder_index=memory_data.get("wonder_index", 0.0),
                additional_data={
                    k: v for k, v in memory_data.items()
                    if k not in ["content", "memory_type", "scope", "wonder_index"]
                },
            )
            record = await result.single()
            return record["memory_id"]

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
            query: Search query (uses case-insensitive CONTAINS)
            memory_type: Optional type filter
            limit: Maximum number of results

        Returns:
            List of memory dicts
        """
        self._check_driver()

        if memory_type:
            cypher_query = """
            MATCH (u:User {user_id: $user_id})-[:HAS_CORE_MEMORY]->(m:CoreMemory {memory_type: $memory_type})
            WHERE toLower(m.content) CONTAINS toLower($query)
            RETURN m
            ORDER BY m.wonder_index DESC, m.timestamp DESC
            LIMIT $limit
            """
            params = {"user_id": user_id, "query": query, "memory_type": memory_type, "limit": limit}
        else:
            cypher_query = """
            MATCH (u:User {user_id: $user_id})-[:HAS_CORE_MEMORY]->(m:CoreMemory)
            WHERE toLower(m.content) CONTAINS toLower($query)
            RETURN m
            ORDER BY m.wonder_index DESC, m.timestamp DESC
            LIMIT $limit
            """
            params = {"user_id": user_id, "query": query, "limit": limit}

        async with self._driver.session(database=self._database) as session:
            result = await session.run(cypher_query, **params)

            memories = []
            async for record in result:
                memory = dict(record["m"])
                memories.append(memory)

            return memories

    # ===== Additional Neo4j-specific Methods =====

    async def create_goal_relationship(
        self,
        goal_id: str,
        belief_id: str,
        relationship_type: str = "DRIVEN_BY_BELIEF",
    ) -> None:
        """Create a relationship between a goal and a belief.

        Args:
            goal_id: Goal identifier
            belief_id: Belief identifier
            relationship_type: Type of relationship (default: DRIVEN_BY_BELIEF)
        """
        self._check_driver()

        query = f"""
        MATCH (g:Goal {{goal_id: $goal_id}})
        MATCH (b:CoreBelief {{belief_id: $belief_id}})
        MERGE (g)-[:{relationship_type}]->(b)
        """

        async with self._driver.session(database=self._database) as session:
            await session.run(query, goal_id=goal_id, belief_id=belief_id)

    async def create_memory_relationship(
        self,
        memory_id: str,
        target_id: str,
        target_type: str,
        relationship_type: str,
    ) -> None:
        """Create a relationship between a memory and another entity.

        Args:
            memory_id: Memory identifier
            target_id: Target entity identifier
            target_type: Target entity type (CoreMemory, CoreBelief, Goal)
            relationship_type: Type of relationship (RELATES_TO, SUPPORTS, CONTRADICTS)
        """
        self._check_driver()

        query = f"""
        MATCH (m:CoreMemory {{memory_id: $memory_id}})
        MATCH (t:{target_type} {{
            {target_type.lower()}_id: $target_id
        }})
        MERGE (m)-[:{relationship_type}]->(t)
        """

        # Map target type to appropriate ID field
        id_field_map = {
            "CoreMemory": "memory_id",
            "CoreBelief": "belief_id",
            "Goal": "goal_id",
        }

        id_field = id_field_map.get(target_type)
        if not id_field:
            raise ValueError(f"Invalid target type: {target_type}")

        query = f"""
        MATCH (m:CoreMemory {{memory_id: $memory_id}})
        MATCH (t:{target_type} {{{id_field}: $target_id}})
        MERGE (m)-[:{relationship_type}]->(t)
        """

        async with self._driver.session(database=self._database) as session:
            await session.run(query, memory_id=memory_id, target_id=target_id)

    async def save_breakthrough(
        self,
        user_id: str,
        breakthrough_data: Dict[str, Any],
        related_goal_id: Optional[str] = None,
    ) -> str:
        """Save a breakthrough moment.

        Args:
            user_id: User identifier
            breakthrough_data: Dict with breakthrough properties
            related_goal_id: Optional goal that this breakthrough advances

        Returns:
            str: Breakthrough ID
        """
        self._check_driver()

        breakthrough_id = str(uuid.uuid4())

        if related_goal_id:
            query = """
            MATCH (u:User {user_id: $user_id})
            MATCH (g:Goal {goal_id: $goal_id})
            CREATE (br:Breakthrough {
                breakthrough_id: $breakthrough_id,
                type: $type,
                significance: $significance,
                timestamp: datetime($timestamp)
            })
            SET br += $additional_data
            CREATE (u)-[:EXPERIENCED]->(br)
            CREATE (br)-[:ADVANCES]->(g)
            RETURN br.breakthrough_id AS breakthrough_id
            """
            params = {
                "user_id": user_id,
                "goal_id": related_goal_id,
                "breakthrough_id": breakthrough_id,
                "type": breakthrough_data.get("type", "insight"),
                "significance": breakthrough_data.get("significance", 0.5),
                "timestamp": datetime.utcnow().isoformat(),
                "additional_data": {
                    k: v for k, v in breakthrough_data.items()
                    if k not in ["type", "significance"]
                },
            }
        else:
            query = """
            MATCH (u:User {user_id: $user_id})
            CREATE (br:Breakthrough {
                breakthrough_id: $breakthrough_id,
                type: $type,
                significance: $significance,
                timestamp: datetime($timestamp)
            })
            SET br += $additional_data
            CREATE (u)-[:EXPERIENCED]->(br)
            RETURN br.breakthrough_id AS breakthrough_id
            """
            params = {
                "user_id": user_id,
                "breakthrough_id": breakthrough_id,
                "type": breakthrough_data.get("type", "insight"),
                "significance": breakthrough_data.get("significance", 0.5),
                "timestamp": datetime.utcnow().isoformat(),
                "additional_data": {
                    k: v for k, v in breakthrough_data.items()
                    if k not in ["type", "significance"]
                },
            }

        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, **params)
            record = await result.single()
            return record["breakthrough_id"]
