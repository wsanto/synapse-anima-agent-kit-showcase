# Storage Providers

This directory contains storage provider implementations for the Synapse Anima Agent Kit.

## Available Providers

### 1. InMemoryStorageProvider

Dictionary-based in-memory storage for development and testing.

**Features:**
- No external dependencies
- Fast performance
- Data cleared on application exit
- Simple filtering and search
- UUID generation for IDs

**Use Cases:**
- Development and testing
- Temporary sessions
- Demo applications
- Unit tests

**Example:**
```python
from synapse_anima.storage import InMemoryStorageProvider

async def main():
    async with InMemoryStorageProvider() as storage:
        # Create user
        user = await storage.create_user("user123", name="Alice", email="alice@example.com")

        # Save message
        message_id = await storage.save_message(
            user_id="user123",
            session_id="session_1",
            role="user",
            content="Hello, how are you?",
        )

        # Get messages
        messages = await storage.get_messages("user123", "session_1")

        # Save goal
        goal_id = await storage.save_goal(
            user_id="user123",
            goal_data={
                "title": "Learn Python",
                "description": "Master Python programming",
                "category": "learning",
                "priority": 8,
            }
        )

        # Get goals
        goals = await storage.get_goals("user123")
```

### 2. Neo4jStorageProvider

Full Neo4j graph database implementation with relationship modeling.

**Features:**
- Rich relationship modeling
- Belief networks and goal hierarchies
- Emotional trajectory tracking
- Breakthrough moments
- Memory connections (RELATES_TO, SUPPORTS, CONTRADICTS)
- Connection pooling
- Comprehensive error handling

**Schema:**
- Nodes: User, CoreBelief, Goal, CoreMemory, EmotionalTrajectoryPoint, Breakthrough
- Relationships: HOLDS_BELIEF, PURSUES, HAS_CORE_MEMORY, DRIVEN_BY_BELIEF, ADVANCES, etc.

**Use Cases:**
- Production applications with complex data relationships
- Research and analysis of user patterns
- Graph-based queries and insights
- Relationship discovery

**Example:**
```python
from synapse_anima.storage import Neo4jStorageProvider

async def main():
    async with Neo4jStorageProvider(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="your_password",
        database="neo4j"
    ) as storage:
        # Create user
        user = await storage.create_user("user123", name="Alice")

        # Save belief
        belief_id = await storage.save_belief(
            user_id="user123",
            belief_data={
                "category": "values",
                "statement": "Learning is a lifelong journey",
                "strength": 0.9,
                "user_confirmed": True,
            }
        )

        # Save goal
        goal_id = await storage.save_goal(
            user_id="user123",
            goal_data={
                "title": "Master Machine Learning",
                "description": "Become proficient in ML algorithms",
                "category": "learning",
                "priority": 9,
            }
        )

        # Create relationship: goal driven by belief
        await storage.create_goal_relationship(
            goal_id=goal_id,
            belief_id=belief_id,
            relationship_type="DRIVEN_BY_BELIEF"
        )

        # Save breakthrough
        breakthrough_id = await storage.save_breakthrough(
            user_id="user123",
            breakthrough_data={
                "type": "insight",
                "significance": 0.8,
                "description": "Realized the connection between statistics and ML"
            },
            related_goal_id=goal_id
        )

        # Save memory with relationships
        memory_id = await storage.save_memory(
            user_id="user123",
            memory_data={
                "content": "First time understanding backpropagation deeply",
                "memory_type": "breakthrough",
                "scope": "core",
                "wonder_index": 0.85,
            }
        )

        # Create memory-belief relationship
        await storage.create_memory_relationship(
            memory_id=memory_id,
            target_id=belief_id,
            target_type="CoreBelief",
            relationship_type="SUPPORTS"
        )

        # Track emotions
        await storage.save_emotion(
            user_id="user123",
            session_id="session_1",
            emotion_data={
                "emotion": "excitement",
                "intensity": 0.8,
                "complexity": 0.6,
                "wonder_index": 0.75,
            }
        )

        # Get emotional trajectory
        trajectory = await storage.get_emotional_trajectory("user123", limit=20)
```

### 3. SupabaseStorageProvider

Supabase Postgres implementation with Row Level Security (RLS) support.

**Features:**
- Postgres database with Supabase SDK
- Row Level Security (RLS) for multi-tenant applications
- Real-time subscriptions (via Supabase)
- Built-in authentication integration
- JSONB for flexible metadata storage
- Agent preferences management
- Chat session management

**Schema:**
- Tables: profiles, chat_sessions, chat_messages, agent_preferences
- Additional: goals, beliefs, memories, emotions

**Use Cases:**
- Multi-tenant SaaS applications
- Applications requiring real-time updates
- Integration with Supabase Auth
- Cloud-hosted solutions

**Example:**
```python
from synapse_anima.storage import SupabaseStorageProvider

async def main():
    async with SupabaseStorageProvider(
        url="https://your-project.supabase.co",
        key="your-anon-key"
    ) as storage:
        # Create user profile
        user = await storage.create_user(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            display_name="Alice",
            avatar_url="https://example.com/avatar.jpg"
        )

        # Save message
        message_id = await storage.save_message(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            session_id="session_1",
            role="user",
            content="What's the weather like?",
            metadata={"location": "San Francisco"}
        )

        # Get chat sessions
        sessions = await storage.get_chat_sessions(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            limit=10
        )

        # Save agent preferences
        preferences = await storage.save_agent_preferences(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            personality_settings={
                "tone": "friendly",
                "verbosity": "concise",
            },
            context_settings={
                "memory_depth": 20,
                "emotion_tracking": True,
            },
            tool_settings={
                "web_search": True,
                "code_execution": False,
            }
        )

        # Get preferences
        prefs = await storage.get_agent_preferences(
            user_id="550e8400-e29b-41d4-a716-446655440000"
        )

        # Save goal
        goal_id = await storage.save_goal(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            goal_data={
                "title": "Improve fitness",
                "description": "Exercise 3 times per week",
                "category": "health",
                "priority": 7,
            }
        )

        # Update goal progress
        await storage.update_goal_progress(
            goal_id=goal_id,
            progress=0.3,
            status="in_progress"
        )

        # Search memories
        memories = await storage.search_memories(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            query="exercise",
            memory_type="goal",
            limit=5
        )
```

## Base Provider Interface

All storage providers implement the `BaseStorageProvider` abstract base class, which defines the following methods:

### User Management
- `get_user(user_id)` - Retrieve user data
- `create_user(user_id, **kwargs)` - Create new user

### Message Management
- `save_message(user_id, session_id, role, content, metadata, timestamp)` - Save chat message
- `get_messages(user_id, session_id, limit, offset)` - Retrieve messages

### Emotion Tracking
- `save_emotion(user_id, session_id, emotion_data, timestamp)` - Save emotional state
- `get_emotional_trajectory(user_id, session_id, limit)` - Get emotion history

### Goals Management
- `save_goal(user_id, goal_data)` - Save user goal
- `get_goals(user_id, status, limit)` - Retrieve goals
- `update_goal_progress(goal_id, progress, status)` - Update goal

### Beliefs Management
- `save_belief(user_id, belief_data)` - Save core belief
- `get_beliefs(user_id, category, limit)` - Retrieve beliefs

### Memory Management
- `save_memory(user_id, memory_data)` - Save core memory
- `search_memories(user_id, query, memory_type, limit)` - Search memories

## Choosing a Provider

| Provider | Best For | Pros | Cons |
|----------|----------|------|------|
| **InMemory** | Testing, Development | Fast, Simple, No setup | No persistence, Limited features |
| **Neo4j** | Complex relationships, Research | Rich graph modeling, Powerful queries | Requires Neo4j setup, Learning curve |
| **Supabase** | Production SaaS, Cloud | RLS, Real-time, Auth integration | Requires Supabase project, Network latency |

## Error Handling

All providers implement comprehensive error handling:

```python
from synapse_anima.storage import InMemoryStorageProvider

async with InMemoryStorageProvider() as storage:
    try:
        # This will raise ValueError if user exists
        await storage.create_user("user123")
        await storage.create_user("user123")  # Error!
    except ValueError as e:
        print(f"Error: {e}")

    try:
        # This will raise ValueError if goal not found
        await storage.update_goal_progress("invalid_id", 0.5)
    except ValueError as e:
        print(f"Error: {e}")
```

## Resource Cleanup

All providers use async context managers for proper resource cleanup:

```python
# Automatic cleanup
async with Neo4jStorageProvider(...) as storage:
    # Use storage
    pass
# Connection closed automatically

# Or manual management (not recommended)
storage = Neo4jStorageProvider(...)
await storage.__aenter__()
try:
    # Use storage
    pass
finally:
    await storage.__aexit__(None, None, None)
```

## Performance Considerations

### InMemory
- O(1) for most operations
- O(n) for search operations
- Limited by available RAM

### Neo4j
- O(1) for indexed lookups
- Efficient graph traversals
- Configurable connection pooling
- Best for relationship-heavy queries

### Supabase
- Network latency overhead
- Postgres query optimization
- JSONB indexing for metadata
- Connection pooling via Supabase SDK

## Testing

Each provider includes comprehensive docstrings and type hints. For unit testing:

```python
import pytest
from synapse_anima.storage import InMemoryStorageProvider

@pytest.mark.asyncio
async def test_create_and_get_user():
    async with InMemoryStorageProvider() as storage:
        # Create user
        user = await storage.create_user("test_user", name="Test")
        assert user["user_id"] == "test_user"
        assert user["name"] == "Test"

        # Get user
        retrieved = await storage.get_user("test_user")
        assert retrieved["user_id"] == "test_user"

        # Non-existent user
        missing = await storage.get_user("unknown")
        assert missing is None
```
