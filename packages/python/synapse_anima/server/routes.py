"""
REST API Routes for Synapse Anima Agent Kit.

This module defines all HTTP REST endpoints for the API, including:
- Beliefs management (7 endpoints)
- Goals management (6 endpoints)
- Memory management (5 endpoints)
- Preferences management (4 endpoints)
- Chat endpoint (non-streaming)
- Health and status endpoints
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Request, status
from pydantic import BaseModel, Field, validator

from ..config import ReasoningMode, PersonalityMode
from ..types import BeliefCategory, GoalStatus, MemoryType, MemoryScope, InterestDomain, ProficiencyLevel


# ===== Pydantic Models for Request/Response =====

# === Chat Models ===

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., description="User message content", min_length=1)
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field("default", description="Session/context identifier")
    personality_mode: Optional[str] = Field(None, description="Personality mode override")
    reasoning_mode: str = Field("quick", description="Reasoning mode: quick or deep")

    @validator("personality_mode")
    def validate_personality_mode(cls, v):
        """Validate personality mode."""
        if v is not None:
            try:
                PersonalityMode(v)
            except ValueError:
                raise ValueError(f"Invalid personality_mode. Must be one of: {[m.value for m in PersonalityMode]}")
        return v

    @validator("reasoning_mode")
    def validate_reasoning_mode(cls, v):
        """Validate reasoning mode."""
        try:
            ReasoningMode(v)
        except ValueError:
            raise ValueError(f"Invalid reasoning_mode. Must be one of: {[m.value for m in ReasoningMode]}")
        return v


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    content: str = Field(..., description="Agent response content")
    emotions: Optional[Dict[str, Any]] = Field(None, description="Emotion analysis")
    reasoning: Optional[str] = Field(None, description="Reasoning chain (deep mode)")
    goals_detected: List[Dict[str, Any]] = Field(default_factory=list)
    beliefs_detected: List[Dict[str, Any]] = Field(default_factory=list)
    interests_detected: List[Dict[str, Any]] = Field(default_factory=list)
    memories_detected: List[Dict[str, Any]] = Field(default_factory=list)
    wonder_index: float = Field(0.0, description="Novelty/discovery measure")
    breakthrough_detected: bool = Field(False, description="Breakthrough detected")
    crisis_detected: bool = Field(False, description="Crisis detected")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# === Beliefs Models ===

class BeliefCreate(BaseModel):
    """Request model for creating a belief."""

    statement: str = Field(..., description="Belief statement", min_length=1)
    category: str = Field(..., description="Belief category")
    strength: float = Field(0.5, ge=0.0, le=1.0, description="Belief strength")
    emotional_signature: Optional[Dict[str, Any]] = Field(None)
    user_confirmed: bool = Field(False, description="User explicitly confirmed")

    @validator("category")
    def validate_category(cls, v):
        """Validate category."""
        try:
            BeliefCategory(v)
        except ValueError:
            raise ValueError(f"Invalid category. Must be one of: {[c.value for c in BeliefCategory]}")
        return v


class BeliefUpdate(BaseModel):
    """Request model for updating belief strength."""

    strength: float = Field(..., ge=0.0, le=1.0, description="New belief strength")


class BeliefLinkGoal(BaseModel):
    """Request model for linking belief to goal."""

    goal_id: str = Field(..., description="Goal ID to link")


class BeliefResponse(BaseModel):
    """Response model for belief."""

    belief_id: str
    user_id: str
    category: str
    statement: str
    strength: float
    established_date: str
    user_confirmed: bool
    emotional_signature: Optional[Dict[str, Any]]
    related_goals: List[str]
    related_experiences: List[str]


# === Goals Models ===

class GoalCreate(BaseModel):
    """Request model for creating a goal."""

    title: str = Field(..., description="Goal title", min_length=1)
    description: str = Field(..., description="Goal description", min_length=1)
    category: str = Field("personal", description="Goal category")
    priority: int = Field(3, ge=1, le=5, description="Priority 1-5")
    deadline: Optional[str] = Field(None, description="Deadline (ISO format)")
    wonder_index: float = Field(0.0, ge=0.0, le=1.0)
    emotional_intensity: float = Field(0.5, ge=0.0, le=1.0)


class GoalProgressUpdate(BaseModel):
    """Request model for updating goal progress."""

    progress: float = Field(..., ge=0.0, le=1.0, description="Progress 0.0-1.0")
    status: Optional[str] = Field(None, description="Optional status update")

    @validator("status")
    def validate_status(cls, v):
        """Validate status."""
        if v is not None:
            try:
                GoalStatus(v)
            except ValueError:
                raise ValueError(f"Invalid status. Must be one of: {[s.value for s in GoalStatus]}")
        return v


class MilestoneCreate(BaseModel):
    """Request model for adding milestone to goal."""

    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    target_date: Optional[str] = Field(None)
    completed: bool = Field(False)


class ObstacleCreate(BaseModel):
    """Request model for adding obstacle to goal."""

    description: str = Field(..., min_length=1)
    severity: str = Field("medium", description="low, medium, high, critical")
    mitigation: Optional[str] = Field(None)

    @validator("severity")
    def validate_severity(cls, v):
        """Validate severity."""
        if v not in ["low", "medium", "high", "critical"]:
            raise ValueError("Invalid severity. Must be one of: low, medium, high, critical")
        return v


class GoalResponse(BaseModel):
    """Response model for goal."""

    goal_id: str
    user_id: str
    title: str
    description: str
    category: str
    priority: int
    status: str
    progress: float
    deadline: Optional[str]
    wonder_index: float
    emotional_intensity: float
    created_at: str
    updated_at: str
    sub_goals: List[Any]
    milestones: List[Dict[str, Any]]
    obstacles: List[Dict[str, Any]]
    related_memories: List[str]


# === Memory Models ===

class MemoryCreate(BaseModel):
    """Request model for creating a memory."""

    content: str = Field(..., description="Memory content", min_length=1)
    memory_type: str = Field(..., description="Memory type")
    scope: str = Field("core", description="Memory scope")
    emotional_signature: Optional[Dict[str, Any]] = Field(None)
    wonder_index: float = Field(0.0, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = Field(None)

    @validator("memory_type")
    def validate_memory_type(cls, v):
        """Validate memory type."""
        try:
            MemoryType(v)
        except ValueError:
            raise ValueError(f"Invalid memory_type. Must be one of: {[t.value for t in MemoryType]}")
        return v

    @validator("scope")
    def validate_scope(cls, v):
        """Validate scope."""
        try:
            MemoryScope(v)
        except ValueError:
            raise ValueError(f"Invalid scope. Must be one of: {[s.value for s in MemoryScope]}")
        return v


class MemoryUpdate(BaseModel):
    """Request model for updating a memory."""

    content: Optional[str] = Field(None, min_length=1)
    emotional_signature: Optional[Dict[str, Any]] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)


class MemoryLinkGoal(BaseModel):
    """Request model for linking memory to goal."""

    goal_id: str = Field(..., description="Goal ID to link")


class MemoryResponse(BaseModel):
    """Response model for memory."""

    memory_id: str
    user_id: str
    content: str
    memory_type: str
    scope: str
    timestamp: str
    emotional_signature: Optional[Dict[str, Any]]
    wonder_index: float
    metadata: Dict[str, Any]
    thread_count: int


# === Interest Models ===

class InterestCreate(BaseModel):
    """Request model for creating an interest."""

    name: str = Field(..., description="Interest name", min_length=1)
    domain: str = Field("other", description="Interest domain")
    proficiency: str = Field("curious", description="Proficiency level")
    weight: float = Field(0.5, ge=0.0, le=1.0, description="Interest weight/engagement")
    keywords: List[str] = Field(default_factory=list, description="Related keywords")

    @validator("domain")
    def validate_domain(cls, v):
        """Validate domain."""
        try:
            InterestDomain(v)
        except ValueError:
            raise ValueError(f"Invalid domain. Must be one of: {[d.value for d in InterestDomain]}")
        return v

    @validator("proficiency")
    def validate_proficiency(cls, v):
        """Validate proficiency."""
        try:
            ProficiencyLevel(v)
        except ValueError:
            raise ValueError(f"Invalid proficiency. Must be one of: {[p.value for p in ProficiencyLevel]}")
        return v


class InterestUpdate(BaseModel):
    """Request model for updating an interest."""

    weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    proficiency: Optional[str] = Field(None)
    keywords: Optional[List[str]] = Field(None)

    @validator("proficiency")
    def validate_proficiency(cls, v):
        """Validate proficiency."""
        if v is not None:
            try:
                ProficiencyLevel(v)
            except ValueError:
                raise ValueError(f"Invalid proficiency. Must be one of: {[p.value for p in ProficiencyLevel]}")
        return v


class InterestLinkGoal(BaseModel):
    """Request model for linking interest to goal."""

    goal_id: str = Field(..., description="Goal ID to link")


class InterestResponse(BaseModel):
    """Response model for interest."""

    interest_id: str
    user_id: str
    name: str
    domain: str
    proficiency: str
    weight: float
    confidence: float = 0.5
    keywords: List[str]
    interaction_count: int
    first_mentioned: str
    last_mentioned: str
    related_goals: List[str]
    related_memories: List[str] = []


class InterestStatistics(BaseModel):
    """Response model for interest statistics."""

    total_interests: int
    by_domain: Dict[str, int]
    by_proficiency: Dict[str, int]
    average_weight: float
    top_interests: List[Dict[str, Any]]


# === Preferences Models ===

class PreferencesUpdate(BaseModel):
    """Request model for updating preferences."""

    # Personality settings
    communication_style: Optional[str] = Field(None)
    response_verbosity: Optional[str] = Field(None)
    energy_level: Optional[str] = Field(None)
    certainty_expression: Optional[str] = Field(None)
    emoji_usage: Optional[str] = Field(None)
    proactivity: Optional[str] = Field(None)

    # Context settings
    memory_inclusion: Optional[str] = Field(None)
    goal_visibility: Optional[str] = Field(None)
    belief_injection: Optional[str] = Field(None)
    emotional_tracking: Optional[str] = Field(None)
    conversation_history_depth: Optional[int] = Field(None, ge=1, le=100)

    # Tool settings
    auto_tool_execution: Optional[str] = Field(None)
    tool_verbosity: Optional[str] = Field(None)


# ===== Dependency Injection =====

def get_app_state(request: Request):
    """Dependency to get app state from request.

    Args:
        request: FastAPI request

    Returns:
        AppState instance

    Raises:
        HTTPException: If app state not initialized
    """
    if not hasattr(request.app.state, 'anima'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server not fully initialized",
        )
    return request.app.state.anima


# ===== Router Factory =====

def create_router() -> APIRouter:
    """Create and configure the API router with all endpoints.

    Returns:
        APIRouter: Configured router with all endpoints
    """
    router = APIRouter()

    # ===== Chat Endpoints =====

    @router.post("/chat", response_model=ChatResponse, tags=["Chat"])
    async def chat(
        request: ChatRequest,
        app_state=Depends(get_app_state),
    ):
        """Chat with the agent (non-streaming).

        For streaming responses, use the WebSocket endpoint instead.

        Args:
            request: Chat request with message and settings

        Returns:
            ChatResponse with agent response and metadata

        Raises:
            HTTPException: If chat processing fails
        """
        try:
            # Parse personality mode
            personality_mode = None
            if request.personality_mode:
                personality_mode = PersonalityMode(request.personality_mode)

            # Parse reasoning mode
            reasoning_mode = ReasoningMode(request.reasoning_mode)

            # Process through agent
            response = await app_state.agent.chat(
                message=request.message,
                user_id=request.user_id,
                session_id=request.session_id,
                personality_mode=personality_mode,
                reasoning_mode=reasoning_mode,
            )

            return ChatResponse(
                content=response.content,
                emotions=response.emotions,
                reasoning=response.reasoning,
                goals_detected=response.goals_detected,
                beliefs_detected=response.beliefs_detected,
                interests_detected=response.interests_detected,
                memories_detected=response.memories_detected,
                wonder_index=response.wonder_index,
                breakthrough_detected=response.breakthrough_detected,
                crisis_detected=response.crisis_detected,
                metadata=response.metadata,
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Chat failed: {str(e)}",
            )

    # ===== Beliefs Endpoints (7 endpoints) =====

    @router.post("/beliefs", response_model=BeliefResponse, status_code=status.HTTP_201_CREATED, tags=["Beliefs"])
    async def create_belief(
        user_id: str,
        belief: BeliefCreate,
        app_state=Depends(get_app_state),
    ):
        """Create a new user belief.

        Args:
            user_id: User identifier
            belief: Belief data

        Returns:
            Created belief

        Raises:
            HTTPException: If creation fails
        """
        try:
            result = await app_state.beliefs_api.create_belief(
                user_id=user_id,
                statement=belief.statement,
                category=belief.category,
                strength=belief.strength,
                emotional_signature=belief.emotional_signature,
                user_confirmed=belief.user_confirmed,
            )
            return result
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.get("/beliefs", response_model=List[BeliefResponse], tags=["Beliefs"])
    async def get_beliefs(
        user_id: str,
        category: Optional[str] = None,
        min_strength: Optional[float] = None,
        confirmed_only: bool = False,
        limit: int = 50,
        app_state=Depends(get_app_state),
    ):
        """Get user beliefs with optional filtering.

        Args:
            user_id: User identifier
            category: Optional category filter
            min_strength: Optional minimum strength filter
            confirmed_only: Only return user-confirmed beliefs
            limit: Maximum number of results

        Returns:
            List of beliefs
        """
        try:
            return await app_state.beliefs_api.get_beliefs(
                user_id=user_id,
                category=category,
                min_strength=min_strength,
                confirmed_only=confirmed_only,
                limit=limit,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.patch("/beliefs/{belief_id}/strength", response_model=Dict[str, Any], tags=["Beliefs"])
    async def update_belief_strength(
        belief_id: str,
        user_id: str,
        update: BeliefUpdate,
        app_state=Depends(get_app_state),
    ):
        """Update belief strength.

        Args:
            belief_id: Belief identifier
            user_id: User identifier
            update: Strength update

        Returns:
            Updated belief data
        """
        try:
            return await app_state.beliefs_api.update_strength(
                belief_id=belief_id,
                strength=update.strength,
                user_id=user_id,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.post("/beliefs/{belief_id}/confirm", response_model=BeliefResponse, tags=["Beliefs"])
    async def confirm_belief(
        belief_id: str,
        user_id: str,
        app_state=Depends(get_app_state),
    ):
        """Mark belief as user-confirmed.

        Args:
            belief_id: Belief identifier
            user_id: User identifier

        Returns:
            Updated belief
        """
        try:
            return await app_state.beliefs_api.confirm_belief(belief_id, user_id)
        except RuntimeError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.delete("/beliefs/{belief_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Beliefs"])
    async def delete_belief(
        belief_id: str,
        user_id: str,
        app_state=Depends(get_app_state),
    ):
        """Delete a belief.

        Args:
            belief_id: Belief identifier
            user_id: User identifier
        """
        try:
            await app_state.beliefs_api.delete_belief(belief_id, user_id)
        except RuntimeError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.post("/beliefs/{belief_id}/link-goal", response_model=BeliefResponse, tags=["Beliefs"])
    async def link_belief_to_goal(
        belief_id: str,
        user_id: str,
        link: BeliefLinkGoal,
        app_state=Depends(get_app_state),
    ):
        """Link belief to a goal.

        Args:
            belief_id: Belief identifier
            user_id: User identifier
            link: Goal link data

        Returns:
            Updated belief
        """
        try:
            return await app_state.beliefs_api.link_to_goal(belief_id, link.goal_id, user_id)
        except RuntimeError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.get("/beliefs/statistics", response_model=Dict[str, Any], tags=["Beliefs"])
    async def get_belief_statistics(
        user_id: str,
        app_state=Depends(get_app_state),
    ):
        """Get belief statistics for user.

        Args:
            user_id: User identifier

        Returns:
            Statistics dict
        """
        try:
            return await app_state.beliefs_api.get_belief_statistics(user_id)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # ===== Goals Endpoints (6 endpoints) =====

    @router.post("/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED, tags=["Goals"])
    async def create_goal(
        user_id: str,
        goal: GoalCreate,
        app_state=Depends(get_app_state),
    ):
        """Create a new goal.

        Args:
            user_id: User identifier
            goal: Goal data

        Returns:
            Created goal
        """
        try:
            # Parse deadline if provided
            deadline = None
            if goal.deadline:
                deadline = datetime.fromisoformat(goal.deadline)

            result = await app_state.goals_api.create_goal(
                user_id=user_id,
                title=goal.title,
                description=goal.description,
                category=goal.category,
                priority=goal.priority,
                deadline=deadline,
                wonder_index=goal.wonder_index,
                emotional_intensity=goal.emotional_intensity,
            )
            return result
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.get("/goals", response_model=List[GoalResponse], tags=["Goals"])
    async def get_goals(
        user_id: str,
        status_filter: Optional[str] = None,
        category: Optional[str] = None,
        min_priority: Optional[int] = None,
        limit: int = 50,
        app_state=Depends(get_app_state),
    ):
        """Get user goals with optional filtering.

        Args:
            user_id: User identifier
            status_filter: Optional status filter
            category: Optional category filter
            min_priority: Optional minimum priority
            limit: Maximum results

        Returns:
            List of goals
        """
        try:
            return await app_state.goals_api.get_goals(
                user_id=user_id,
                status=status_filter,
                category=category,
                min_priority=min_priority,
                limit=limit,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.get("/goals/{goal_id}", response_model=GoalResponse, tags=["Goals"])
    async def get_goal(
        goal_id: str,
        user_id: str,
        app_state=Depends(get_app_state),
    ):
        """Get a single goal by ID.

        Args:
            goal_id: Goal identifier
            user_id: User identifier

        Returns:
            Goal data
        """
        try:
            return await app_state.goals_api.get_goal(goal_id, user_id)
        except RuntimeError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.patch("/goals/{goal_id}/progress", response_model=GoalResponse, tags=["Goals"])
    async def update_goal_progress(
        goal_id: str,
        user_id: str,
        update: GoalProgressUpdate,
        app_state=Depends(get_app_state),
    ):
        """Update goal progress and status.

        Args:
            goal_id: Goal identifier
            user_id: User identifier
            update: Progress update

        Returns:
            Updated goal
        """
        try:
            return await app_state.goals_api.update_progress(
                goal_id=goal_id,
                user_id=user_id,
                progress=update.progress,
                status=update.status,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.get("/goals/statistics", response_model=Dict[str, Any], tags=["Goals"])
    async def get_goal_statistics(
        user_id: str,
        app_state=Depends(get_app_state),
    ):
        """Get goal statistics for user.

        Args:
            user_id: User identifier

        Returns:
            Statistics dict
        """
        try:
            return await app_state.goals_api.get_statistics(user_id)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Goals"])
    async def delete_goal(
        goal_id: str,
        user_id: str,
        app_state=Depends(get_app_state),
    ):
        """Delete a goal.

        Args:
            goal_id: Goal identifier
            user_id: User identifier
        """
        try:
            await app_state.goals_api.delete_goal(goal_id, user_id)
        except RuntimeError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # ===== Memory Endpoints (5 endpoints) =====

    @router.post("/memories", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED, tags=["Memory"])
    async def create_memory(
        user_id: str,
        memory: MemoryCreate,
        app_state=Depends(get_app_state),
    ):
        """Create a new memory.

        Args:
            user_id: User identifier
            memory: Memory data

        Returns:
            Created memory
        """
        try:
            result = await app_state.memory_api.create_memory(
                user_id=user_id,
                content=memory.content,
                memory_type=memory.memory_type,
                scope=memory.scope,
                emotional_signature=memory.emotional_signature,
                wonder_index=memory.wonder_index,
                metadata=memory.metadata,
            )
            return result
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.get("/memories", response_model=List[MemoryResponse], tags=["Memory"])
    async def get_memories(
        user_id: str,
        memory_type: Optional[str] = None,
        scope: Optional[str] = None,
        min_wonder_index: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
        app_state=Depends(get_app_state),
    ):
        """Get user memories with optional filtering.

        Args:
            user_id: User identifier
            memory_type: Optional type filter
            scope: Optional scope filter
            min_wonder_index: Optional minimum wonder index
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of memories
        """
        try:
            return await app_state.memory_api.get_memories(
                user_id=user_id,
                memory_type=memory_type,
                scope=scope,
                min_wonder_index=min_wonder_index,
                limit=limit,
                offset=offset,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.get("/memories/search", response_model=List[MemoryResponse], tags=["Memory"])
    async def search_memories(
        user_id: str,
        query: str,
        memory_type: Optional[str] = None,
        scope: Optional[str] = None,
        limit: int = 10,
        app_state=Depends(get_app_state),
    ):
        """Search memories by content.

        Args:
            user_id: User identifier
            query: Search query
            memory_type: Optional type filter
            scope: Optional scope filter
            limit: Maximum results

        Returns:
            List of matching memories
        """
        try:
            return await app_state.memory_api.search_memories(
                user_id=user_id,
                query=query,
                memory_type=memory_type,
                scope=scope,
                limit=limit,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.get("/memories/breakthroughs", response_model=List[MemoryResponse], tags=["Memory"])
    async def get_breakthroughs(
        user_id: str,
        min_significance: float = 0.7,
        limit: int = 20,
        app_state=Depends(get_app_state),
    ):
        """Get breakthrough moments.

        Args:
            user_id: User identifier
            min_significance: Minimum significance threshold
            limit: Maximum results

        Returns:
            List of breakthrough memories
        """
        try:
            return await app_state.memory_api.get_breakthroughs(
                user_id=user_id,
                min_significance=min_significance,
                limit=limit,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.get("/memories/statistics", response_model=Dict[str, Any], tags=["Memory"])
    async def get_memory_statistics(
        user_id: str,
        app_state=Depends(get_app_state),
    ):
        """Get memory statistics for user.

        Args:
            user_id: User identifier

        Returns:
            Statistics dict
        """
        try:
            return await app_state.memory_api.get_memory_statistics(user_id)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # ===== Interest Endpoints (7 endpoints) =====

    @router.post("/interests", response_model=InterestResponse, status_code=status.HTTP_201_CREATED, tags=["Interests"])
    async def create_interest(
        user_id: str,
        interest: InterestCreate,
        app_state=Depends(get_app_state),
    ):
        """Create a new user interest.

        Args:
            user_id: User identifier
            interest: Interest data

        Returns:
            Created interest

        Raises:
            HTTPException: If creation fails
        """
        try:
            # Check if storage provider supports interests
            if not hasattr(app_state.storage, 'save_interest'):
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Storage provider does not support interests",
                )

            import uuid
            from datetime import datetime

            interest_id = str(uuid.uuid4())
            now = datetime.utcnow()

            interest_data = {
                "interest_id": interest_id,
                "user_id": user_id,
                "name": interest.name,
                "domain": interest.domain,
                "proficiency": interest.proficiency,
                "weight": interest.weight,
                "confidence": interest.weight,  # Use weight as initial confidence
                "keywords": interest.keywords,
                "interaction_count": 1,
                "first_mentioned": now.isoformat(),
                "last_mentioned": now.isoformat(),
                "related_goals": [],
                "related_memories": [],
            }

            await app_state.storage.save_interest(user_id, interest_data)

            return interest_data
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.get("/interests", response_model=List[InterestResponse], tags=["Interests"])
    async def get_interests(
        user_id: str,
        domain: Optional[str] = None,
        min_weight: Optional[float] = None,
        limit: int = 50,
        app_state=Depends(get_app_state),
    ):
        """Get user interests with filtering.

        Args:
            user_id: User identifier
            domain: Optional domain filter
            min_weight: Optional minimum weight filter
            limit: Maximum results

        Returns:
            List of interests
        """
        try:
            if not hasattr(app_state.storage, 'get_interests'):
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Storage provider does not support interests",
                )

            return await app_state.storage.get_interests(
                user_id=user_id,
                domain=domain,
                min_weight=min_weight,
                limit=limit,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.get("/interests/{interest_id}", response_model=InterestResponse, tags=["Interests"])
    async def get_interest(
        interest_id: str,
        user_id: str,
        app_state=Depends(get_app_state),
    ):
        """Get a specific interest.

        Args:
            interest_id: Interest identifier
            user_id: User identifier

        Returns:
            Interest data

        Raises:
            HTTPException: If not found
        """
        try:
            if not hasattr(app_state.storage, 'get_interests'):
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Storage provider does not support interests",
                )

            interests = await app_state.storage.get_interests(user_id=user_id, limit=1000)
            interest = next((i for i in interests if i.get("interest_id") == interest_id), None)

            if not interest:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Interest {interest_id} not found",
                )

            return interest
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.patch("/interests/{interest_id}", response_model=InterestResponse, tags=["Interests"])
    async def update_interest(
        interest_id: str,
        user_id: str,
        interest: InterestUpdate,
        app_state=Depends(get_app_state),
    ):
        """Update an interest.

        Args:
            interest_id: Interest identifier
            user_id: User identifier
            interest: Update data

        Returns:
            Updated interest
        """
        try:
            if not hasattr(app_state.storage, 'update_interest'):
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Storage provider does not support interest updates",
                )

            # Build update dict with non-None values
            update_data = {k: v for k, v in interest.dict().items() if v is not None}

            await app_state.storage.update_interest(interest_id, update_data)

            # Return updated interest
            interests = await app_state.storage.get_interests(user_id=user_id, limit=1000)
            updated = next((i for i in interests if i.get("interest_id") == interest_id), None)

            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Interest {interest_id} not found",
                )

            return updated
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.delete("/interests/{interest_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Interests"])
    async def delete_interest(
        interest_id: str,
        user_id: str,
        app_state=Depends(get_app_state),
    ):
        """Delete an interest.

        Args:
            interest_id: Interest identifier
            user_id: User identifier
        """
        try:
            if not hasattr(app_state.storage, 'delete_interest'):
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Storage provider does not support interest deletion",
                )

            await app_state.storage.delete_interest(interest_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.post("/interests/{interest_id}/link-goal", status_code=status.HTTP_200_OK, tags=["Interests"])
    async def link_interest_to_goal(
        interest_id: str,
        user_id: str,
        link: InterestLinkGoal,
        app_state=Depends(get_app_state),
    ):
        """Link interest to a goal.

        Args:
            interest_id: Interest identifier
            user_id: User identifier
            link: Link data with goal_id

        Returns:
            Success message
        """
        try:
            if not hasattr(app_state.storage, 'link_interest_to_goal'):
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Storage provider does not support interest-goal linking",
                )

            await app_state.storage.link_interest_to_goal(interest_id, link.goal_id)

            return {"message": "Interest linked to goal successfully"}
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.get("/interests/statistics", response_model=InterestStatistics, tags=["Interests"])
    async def get_interest_statistics(
        user_id: str,
        app_state=Depends(get_app_state),
    ):
        """Get interest statistics for user.

        Args:
            user_id: User identifier

        Returns:
            Statistics including counts by domain, proficiency, and top interests
        """
        try:
            if not hasattr(app_state.storage, 'get_interests'):
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Storage provider does not support interests",
                )

            interests = await app_state.storage.get_interests(user_id=user_id, limit=1000)

            # Calculate statistics
            by_domain = {}
            by_proficiency = {}
            total_weight = 0.0

            for interest in interests:
                domain = interest.get("domain", "other")
                proficiency = interest.get("proficiency", "curious")
                weight = interest.get("weight", 0.5)

                by_domain[domain] = by_domain.get(domain, 0) + 1
                by_proficiency[proficiency] = by_proficiency.get(proficiency, 0) + 1
                total_weight += weight

            # Sort by weight for top interests
            sorted_interests = sorted(interests, key=lambda i: i.get("weight", 0), reverse=True)

            return {
                "total_interests": len(interests),
                "by_domain": by_domain,
                "by_proficiency": by_proficiency,
                "average_weight": total_weight / len(interests) if interests else 0.0,
                "top_interests": sorted_interests[:5],
            }
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # ===== Preferences Endpoints (4 endpoints) =====

    @router.get("/preferences", response_model=Dict[str, Any], tags=["Preferences"])
    async def get_preferences(
        user_id: str,
        app_state=Depends(get_app_state),
    ):
        """Get user's agent preferences.

        Args:
            user_id: User identifier

        Returns:
            Complete preferences dict
        """
        try:
            return await app_state.preferences_api.get_preferences(user_id)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.patch("/preferences", response_model=Dict[str, Any], tags=["Preferences"])
    async def update_preferences(
        user_id: str,
        preferences: PreferencesUpdate,
        app_state=Depends(get_app_state),
    ):
        """Update user's agent preferences.

        Args:
            user_id: User identifier
            preferences: Preference updates (partial)

        Returns:
            Updated complete preferences
        """
        try:
            # Convert to dict, removing None values
            prefs_dict = {k: v for k, v in preferences.dict().items() if v is not None}

            return await app_state.preferences_api.update_preferences(user_id, prefs_dict)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.post("/preferences/reset", response_model=Dict[str, Any], tags=["Preferences"])
    async def reset_preferences(
        user_id: str,
        category: Optional[str] = None,
        app_state=Depends(get_app_state),
    ):
        """Reset preferences to defaults.

        Args:
            user_id: User identifier
            category: Optional category to reset (personality, context, tools)

        Returns:
            Reset preferences
        """
        try:
            return await app_state.preferences_api.reset_to_defaults(user_id, category)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.get("/preferences/schema", response_model=Dict[str, Any], tags=["Preferences"])
    async def get_preferences_schema(
        app_state=Depends(get_app_state),
    ):
        """Get preference schema with valid values.

        Returns:
            Preference schema dict
        """
        try:
            return app_state.preferences_api.get_preference_schema()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return router
