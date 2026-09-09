"""
ANIMA Agent Server - FastAPI Application

Provides REST API and WebSocket endpoints for the ANIMA Agent.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

print("[SERVER] Starting ANIMA Agent Server...")
print(f"[SERVER] Python version: {sys.version}")
print(f"[SERVER] Working directory: {os.getcwd()}")

# Load environment variables from .env.local BEFORE importing anything else
from dotenv import load_dotenv

# Look for .env.local in project root
project_root = Path(__file__).parent.parent
env_file = project_root / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
    print(f"[SERVER] Loaded environment from {env_file}")
else:
    # Fallback to .env if .env.local doesn't exist
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"[SERVER] Loaded environment from {env_file}")
    else:
        print("[SERVER] No .env file found, using system environment variables")

# Log key environment variables (without exposing secrets)
print(f"[SERVER] MISTRAL_API_KEY set: {bool(os.getenv('MISTRAL_API_KEY'))}")
print(f"[SERVER] SYNAPSE_API_KEY set: {bool(os.getenv('SYNAPSE_API_KEY'))}")
print(f"[SERVER] ANIMA_LLM_PROVIDER: {os.getenv('ANIMA_LLM_PROVIDER', 'not set')}")
print(f"[SERVER] ANIMA_ENVIRONMENT: {os.getenv('ANIMA_ENVIRONMENT', 'not set')}")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add the server directory to path for middleware/services imports
sys.path.insert(0, os.path.dirname(__file__))

# Import middleware and services
from middleware.auth import validate_api_key, APIKeyInfo, validate_api_key_with_synapse
from services.billing import (
    get_billing_service,
    get_billing_config,
    BillingService,
    AgentKitMetric,
)

# Add the Python SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'python'))

print("[SERVER] Importing synapse_anima...")
from synapse_anima import NeuralAgent, AnimaConfig
from synapse_anima.config import ChatMode, ConversationStyle, PersonalityMode, ReasoningMode
print("[SERVER] synapse_anima imported successfully")


# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None
    chat_mode: Optional[str] = None  # ask_advice, set_goals, explore
    conversation_style: Optional[str] = None  # balanced, therapeutic, crisis, coaching, casual, analytical
    personality_mode: Optional[str] = None  # balanced, analytical, creative, supportive
    reasoning_mode: Optional[str] = None  # quick, deep


class ChatResponse(BaseModel):
    content: str
    emotion: Optional[dict] = None
    reasoning: Optional[str] = None
    context_metadata: Optional[dict] = None
    llm_usage: Optional[dict] = None
    pipeline_stages: Optional[list] = None
    session_id: str
    chat_mode: Optional[str] = None
    conversation_style: Optional[str] = None
    personality_mode: Optional[str] = None
    reasoning_mode: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str


# Global instances
agent: Optional[NeuralAgent] = None
billing_service: Optional[BillingService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global agent, billing_service

    print("[SERVER] Starting lifespan initialization...")

    # Initialize billing service on startup
    billing_service = get_billing_service()
    print("[SERVER] Billing service initialized")

    # Initialize agent on startup
    try:
        print("[SERVER] Creating AnimaConfig from environment...")
        config = AnimaConfig.from_env()
        print(f"[SERVER] Config created: LLM={config.llm_provider}, Storage={config.storage_provider}")

        print("[SERVER] Initializing NeuralAgent...")
        agent = NeuralAgent(config)
        print("[SERVER] ANIMA Agent initialized successfully")
    except Exception as e:
        print(f"[SERVER] Warning: Could not initialize agent: {e}")
        import traceback
        traceback.print_exc()
        agent = None

    print("[SERVER] Lifespan initialization complete, server ready for requests")
    yield

    # Cleanup on shutdown
    if billing_service:
        await billing_service.close()
    agent = None
    billing_service = None


# Create FastAPI app
print("[SERVER] Creating FastAPI app...")
app = FastAPI(
    title="ANIMA Agent API",
    description="Emotionally intelligent chat agent API",
    version="1.0.0",
    lifespan=lifespan,
)
print("[SERVER] FastAPI app created")

# CORS middleware - Configure from environment
cors_origins = os.getenv("ANIMA_CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    api_key: APIKeyInfo = Depends(validate_api_key),
):
    """Send a chat message and receive a response."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Log usage for this chat request
    if billing_service:
        await billing_service.log_usage(
            api_key_id=api_key.api_key_id,
            project_id=api_key.project_id,
            user_id=api_key.user_id,
            metric=AgentKitMetric.CHAT_REQUEST,
            end_user_id=request.user_id,
        )
        # Register the end user for monthly billing
        await billing_service.register_end_user(
            project_id=api_key.project_id,
            external_user_id=request.user_id,
        )

    try:
        # Parse mode enums from string values
        chat_mode = ChatMode(request.chat_mode) if request.chat_mode else None
        conversation_style = ConversationStyle(request.conversation_style) if request.conversation_style else None
        personality_mode = PersonalityMode(request.personality_mode) if request.personality_mode else None
        reasoning_mode = ReasoningMode(request.reasoning_mode) if request.reasoning_mode else ReasoningMode.QUICK

        response = await agent.chat(
            message=request.message,
            user_id=request.user_id,
            session_id=request.session_id,
            chat_mode=chat_mode,
            conversation_style=conversation_style,
            personality_mode=personality_mode,
            reasoning_mode=reasoning_mode,
        )

        return ChatResponse(
            content=response.content,
            emotion={
                "category": response.emotions.get("category") if response.emotions else None,
                "intensity": response.emotions.get("intensity") if response.emotions else None,
                "raw": response.emotions.get("raw") if response.emotions else None,
            } if response.emotions else None,
            reasoning=response.reasoning,
            context_metadata=response.context_metadata,
            llm_usage=response.llm_usage,
            pipeline_stages=None,  # Will be populated by streaming
            session_id=request.session_id or "default",
            chat_mode=request.chat_mode,
            conversation_style=request.conversation_style,
            personality_mode=request.personality_mode,
            reasoning_mode=request.reasoning_mode or "quick",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid mode value: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memories/{user_id}")
async def get_memories(
    user_id: str,
    type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    api_key: APIKeyInfo = Depends(validate_api_key),
):
    """Retrieve memories for a user."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Log usage
    if billing_service:
        await billing_service.log_usage(
            api_key_id=api_key.api_key_id,
            project_id=api_key.project_id,
            user_id=api_key.user_id,
            metric=AgentKitMetric.MEMORY_OPERATION,
            end_user_id=user_id,
        )

    try:
        memories = await agent.storage_provider.get_memories(
            user_id=user_id,
            memory_type=type,
            limit=limit,
        )

        return {
            "memories": memories if memories else [],
            "total": len(memories) if memories else 0,
            "has_more": len(memories) >= limit if memories else False,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memories/{user_id}/breakthroughs")
async def get_breakthroughs(
    user_id: str,
    api_key: APIKeyInfo = Depends(validate_api_key),
):
    """Retrieve breakthrough moments for a user."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Breakthroughs are stored in-memory in the ContextNexus
        # They are detected during chat and not persisted to storage yet
        return {
            "breakthroughs": [],
            "message": "Breakthroughs are detected during conversation",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class MemoryCreate(BaseModel):
    memory_type: str  # identity, interest, preference, fact
    content: str
    metadata: Optional[dict] = None


@app.post("/api/memories")
async def create_memory(
    user_id: str,
    memory: MemoryCreate,
    api_key: APIKeyInfo = Depends(validate_api_key),
):
    """Create a new memory manually."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Log usage
    if billing_service:
        await billing_service.log_usage(
            api_key_id=api_key.api_key_id,
            project_id=api_key.project_id,
            user_id=api_key.user_id,
            metric=AgentKitMetric.MEMORY_OPERATION,
            end_user_id=user_id,
        )

    try:
        memory_data = {
            "type": memory.memory_type,
            "content": memory.content,
            "metadata": memory.metadata or {},
            "source": "manual",
        }

        memory_id = await agent.storage_provider.save_memory(
            user_id=user_id,
            memory_data=memory_data,
        )

        return {
            "memory_id": memory_id,
            "message": "Memory created successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Goals API Endpoints =====

class GoalCreate(BaseModel):
    title: str
    description: str
    category: str
    priority: int = 3
    deadline: Optional[str] = None


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[float] = None
    priority: Optional[int] = None


class MilestoneCreate(BaseModel):
    title: str
    description: Optional[str] = None
    target_date: Optional[str] = None


@app.get("/api/goals/{user_id}")
async def get_goals(
    user_id: str,
    status: Optional[str] = None,
    api_key: APIKeyInfo = Depends(validate_api_key),
):
    """Retrieve goals for a user."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Log usage
    if billing_service:
        await billing_service.log_usage(
            api_key_id=api_key.api_key_id,
            project_id=api_key.project_id,
            user_id=api_key.user_id,
            metric=AgentKitMetric.GOAL_OPERATION,
            end_user_id=user_id,
        )

    try:
        goals = await agent.storage_provider.get_goals(user_id=user_id, status=status)

        return {
            "goals": goals,
            "total": len(goals),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/goals")
async def create_goal(
    user_id: str,
    goal: GoalCreate,
    api_key: APIKeyInfo = Depends(validate_api_key),
):
    """Create a new goal."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Log usage
    if billing_service:
        await billing_service.log_usage(
            api_key_id=api_key.api_key_id,
            project_id=api_key.project_id,
            user_id=api_key.user_id,
            metric=AgentKitMetric.GOAL_OPERATION,
            end_user_id=user_id,
        )

    try:
        goal_data = {
            "title": goal.title,
            "description": goal.description,
            "category": goal.category,
            "priority": goal.priority,
            "status": "not_started",
            "progress": 0.0,
            "milestones": [],
            "obstacles": [],
            "sub_goals": [],
        }
        if goal.deadline:
            goal_data["deadline"] = goal.deadline

        goal_id = await agent.storage_provider.save_goal(
            user_id=user_id,
            goal_data=goal_data,
        )

        return {
            "goal_id": goal_id,
            "message": "Goal created successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/goals/{goal_id}")
async def update_goal(
    goal_id: str,
    goal: GoalUpdate,
    api_key: APIKeyInfo = Depends(validate_api_key),
):
    """Update an existing goal."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Log usage
    if billing_service:
        await billing_service.log_usage(
            api_key_id=api_key.api_key_id,
            project_id=api_key.project_id,
            user_id=api_key.user_id,
            metric=AgentKitMetric.GOAL_OPERATION,
        )

    try:
        update_data = {}
        if goal.title is not None:
            update_data["title"] = goal.title
        if goal.description is not None:
            update_data["description"] = goal.description
        if goal.status is not None:
            update_data["status"] = goal.status
        if goal.progress is not None:
            update_data["progress"] = goal.progress
        if goal.priority is not None:
            update_data["priority"] = goal.priority

        await agent.storage_provider.update_goal_progress(
            goal_id=goal_id,
            progress=goal.progress or 0.0,
            status=goal.status,
        )

        return {
            "goal_id": goal_id,
            "message": "Goal updated successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/goals/{goal_id}")
async def delete_goal(
    goal_id: str,
    api_key: APIKeyInfo = Depends(validate_api_key),
):
    """Delete a goal."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Log usage
    if billing_service:
        await billing_service.log_usage(
            api_key_id=api_key.api_key_id,
            project_id=api_key.project_id,
            user_id=api_key.user_id,
            metric=AgentKitMetric.GOAL_OPERATION,
        )

    try:
        await agent.storage_provider.delete_goal(goal_id=goal_id)

        return {
            "goal_id": goal_id,
            "message": "Goal deleted successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/goals/{user_id}/statistics")
async def get_goal_statistics(
    user_id: str,
    api_key: APIKeyInfo = Depends(validate_api_key),
):
    """Get goal statistics for a user."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        goals = await agent.storage_provider.get_goals(user_id=user_id)

        if not goals:
            return {
                "total": 0,
                "by_status": {},
                "by_category": {},
                "average_progress": 0.0,
            }

        by_status: dict = {}
        by_category: dict = {}
        total_progress = 0.0

        for goal in goals:
            status = goal.get("status", "not_started")
            category = goal.get("category", "other")

            by_status[status] = by_status.get(status, 0) + 1
            by_category[category] = by_category.get(category, 0) + 1
            total_progress += goal.get("progress", 0.0)

        return {
            "total": len(goals),
            "by_status": by_status,
            "by_category": by_category,
            "average_progress": total_progress / len(goals) if goals else 0.0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Beliefs API Endpoints =====

class BeliefCreate(BaseModel):
    statement: str
    category: str
    strength: Optional[float] = 0.5
    emotional_signature: Optional[dict] = None


class BeliefUpdate(BaseModel):
    statement: Optional[str] = None
    strength: Optional[float] = None
    user_confirmed: Optional[bool] = None


@app.get("/api/beliefs/{user_id}")
async def get_beliefs(
    user_id: str,
    category: Optional[str] = None,
    limit: int = 50,
    api_key: APIKeyInfo = Depends(validate_api_key),
):
    """Retrieve beliefs for a user."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Log usage
    if billing_service:
        await billing_service.log_usage(
            api_key_id=api_key.api_key_id,
            project_id=api_key.project_id,
            user_id=api_key.user_id,
            metric=AgentKitMetric.BELIEF_OPERATION,
            end_user_id=user_id,
        )

    try:
        beliefs = await agent.storage_provider.get_beliefs(
            user_id=user_id,
            category=category,
            limit=limit,
        )

        return {
            "beliefs": beliefs,
            "total": len(beliefs),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/beliefs")
async def create_belief(
    user_id: str,
    belief: BeliefCreate,
    api_key: APIKeyInfo = Depends(validate_api_key),
):
    """Create a new belief."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Log usage
    if billing_service:
        await billing_service.log_usage(
            api_key_id=api_key.api_key_id,
            project_id=api_key.project_id,
            user_id=api_key.user_id,
            metric=AgentKitMetric.BELIEF_OPERATION,
            end_user_id=user_id,
        )

    try:
        belief_data = {
            "statement": belief.statement,
            "category": belief.category,
            "strength": belief.strength,
            "emotional_signature": belief.emotional_signature,
            "user_confirmed": False,
        }

        belief_id = await agent.storage_provider.save_belief(
            user_id=user_id,
            belief_data=belief_data,
        )

        return {
            "belief_id": belief_id,
            "message": "Belief created successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/beliefs/{belief_id}")
async def update_belief(
    belief_id: str,
    belief: BeliefUpdate,
    api_key: APIKeyInfo = Depends(validate_api_key),
):
    """Update an existing belief."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Log usage
    if billing_service:
        await billing_service.log_usage(
            api_key_id=api_key.api_key_id,
            project_id=api_key.project_id,
            user_id=api_key.user_id,
            metric=AgentKitMetric.BELIEF_OPERATION,
        )

    try:
        update_data = {}
        if belief.statement is not None:
            update_data["statement"] = belief.statement
        if belief.strength is not None:
            update_data["strength"] = belief.strength
        if belief.user_confirmed is not None:
            update_data["user_confirmed"] = belief.user_confirmed

        await agent.storage_provider.update_belief(
            belief_id=belief_id,
            belief_data=update_data,
        )

        return {
            "belief_id": belief_id,
            "message": "Belief updated successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/beliefs/{belief_id}")
async def delete_belief(
    belief_id: str,
    api_key: APIKeyInfo = Depends(validate_api_key),
):
    """Delete a belief."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Log usage
    if billing_service:
        await billing_service.log_usage(
            api_key_id=api_key.api_key_id,
            project_id=api_key.project_id,
            user_id=api_key.user_id,
            metric=AgentKitMetric.BELIEF_OPERATION,
        )

    try:
        await agent.storage_provider.delete_belief(belief_id=belief_id)

        return {
            "belief_id": belief_id,
            "message": "Belief deleted successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/beliefs/{belief_id}/confirm")
async def confirm_belief(
    belief_id: str,
    api_key: APIKeyInfo = Depends(validate_api_key),
):
    """Confirm a belief (user verification)."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Log usage
    if billing_service:
        await billing_service.log_usage(
            api_key_id=api_key.api_key_id,
            project_id=api_key.project_id,
            user_id=api_key.user_id,
            metric=AgentKitMetric.BELIEF_OPERATION,
        )

    try:
        await agent.storage_provider.update_belief(
            belief_id=belief_id,
            belief_data={"user_confirmed": True},
        )

        return {
            "belief_id": belief_id,
            "message": "Belief confirmed successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Interests API Endpoints =====

class InterestCreate(BaseModel):
    name: str
    domain: str  # technology, arts, science, sports, music, etc.
    weight: Optional[float] = 0.5
    proficiency: Optional[str] = "curious"  # curious, beginner, intermediate, advanced, expert
    keywords: Optional[list] = None


class InterestUpdate(BaseModel):
    weight: Optional[float] = None
    proficiency: Optional[str] = None
    keywords: Optional[list] = None


@app.get("/api/interests")
async def get_interests(
    user_id: str,
    domain: Optional[str] = None,
    min_weight: Optional[float] = None,
    limit: int = 50,
):
    """Retrieve interests for a user."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        interests = await agent.storage_provider.get_interests(
            user_id=user_id,
            domain=domain,
            min_weight=min_weight,
            limit=limit,
        )

        return interests if interests else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/interests")
async def create_interest(
    user_id: str,
    interest: InterestCreate,
):
    """Create a new interest."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        from datetime import datetime
        interest_data = {
            "name": interest.name,
            "domain": interest.domain,
            "weight": interest.weight or 0.5,
            "proficiency": interest.proficiency or "curious",
            "confidence": 1.0,  # Manual creation has full confidence
            "keywords": interest.keywords or [],
            "interaction_count": 1,
            "first_mentioned": datetime.utcnow().isoformat(),
            "last_mentioned": datetime.utcnow().isoformat(),
            "related_goals": [],
        }

        interest_id = await agent.storage_provider.save_interest(
            user_id=user_id,
            interest_data=interest_data,
        )

        # Return the full interest object
        return {
            "interest_id": interest_id,
            "user_id": user_id,
            **interest_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# NOTE: Statistics must be defined BEFORE {interest_id} routes for correct matching
@app.get("/api/interests/statistics")
async def get_interest_statistics(
    user_id: str,
):
    """Get interest statistics for a user."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        interests = await agent.storage_provider.get_interests(user_id=user_id)

        if not interests:
            return {
                "total_interests": 0,
                "by_domain": {},
                "by_proficiency": {},
                "average_weight": 0.0,
                "top_interests": [],
            }

        by_domain: dict = {}
        by_proficiency: dict = {}
        total_weight = 0.0

        for interest in interests:
            domain = interest.get("domain", "other")
            proficiency = interest.get("proficiency", "curious")

            by_domain[domain] = by_domain.get(domain, 0) + 1
            by_proficiency[proficiency] = by_proficiency.get(proficiency, 0) + 1
            total_weight += interest.get("weight", 0.5)

        # Get top interests by weight
        sorted_interests = sorted(interests, key=lambda x: x.get("weight", 0), reverse=True)
        top_interests = sorted_interests[:5]

        return {
            "total_interests": len(interests),
            "by_domain": by_domain,
            "by_proficiency": by_proficiency,
            "average_weight": total_weight / len(interests) if interests else 0.0,
            "top_interests": top_interests,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/interests/{interest_id}")
async def get_interest(
    interest_id: str,
    user_id: str,
):
    """Get a single interest by ID."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        interests = await agent.storage_provider.get_interests(user_id=user_id)
        for interest in interests:
            if interest.get("interest_id") == interest_id:
                return interest
        raise HTTPException(status_code=404, detail="Interest not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/interests/{interest_id}")
async def update_interest(
    interest_id: str,
    user_id: str,
    interest: InterestUpdate,
):
    """Update an existing interest."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        update_data = {}
        if interest.weight is not None:
            update_data["weight"] = max(0.0, min(1.0, interest.weight))
        if interest.proficiency is not None:
            update_data["proficiency"] = interest.proficiency
        if interest.keywords is not None:
            update_data["keywords"] = interest.keywords

        await agent.storage_provider.update_interest(
            interest_id=interest_id,
            interest_data=update_data,
        )

        # Return updated interest
        interests = await agent.storage_provider.get_interests(user_id=user_id)
        for i in interests:
            if i.get("interest_id") == interest_id:
                return i

        return {"interest_id": interest_id, "message": "Interest updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/interests/{interest_id}")
async def delete_interest(
    interest_id: str,
    user_id: str,
):
    """Delete an interest."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        await agent.storage_provider.delete_interest(interest_id=interest_id)

        return {
            "interest_id": interest_id,
            "message": "Interest deleted successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/interests/{interest_id}/link-goal")
async def link_interest_to_goal(
    interest_id: str,
    user_id: str,
    goal_id: str,
):
    """Link an interest to a goal."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        await agent.storage_provider.link_interest_to_goal(
            interest_id=interest_id,
            goal_id=goal_id,
        )

        return {
            "interest_id": interest_id,
            "goal_id": goal_id,
            "message": "Interest linked to goal successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Emotion Analytics Endpoints =====

@app.get("/api/emotions/{user_id}/trends")
async def get_emotion_trends(
    user_id: str,
    days: int = 7,
    limit: int = 100,
    api_key: APIKeyInfo = Depends(validate_api_key),
):
    """
    Retrieve emotional trajectory/trends for a user.

    Returns emotion data points over time for visualization.
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Get the user's context nexus
        nexus = agent._get_or_create_nexus(user_id)
        trajectory = nexus.get_emotional_trajectory(limit=limit)

        # Transform to serializable format
        data_points = []
        for point in trajectory:
            data_points.append({
                "emotion": point.emotion,
                "intensity": point.intensity,
                "complexity": point.complexity,
                "timestamp": point.timestamp.isoformat(),
                "wonder_index": point.wonder_index,
                "discovery_level": point.discovery_level,
            })

        return {
            "trends": data_points,
            "total_points": len(data_points),
            "period_days": days,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/emotions/{user_id}/summary")
async def get_emotion_summary(
    user_id: str,
    api_key: APIKeyInfo = Depends(validate_api_key),
):
    """
    Retrieve aggregated emotional analytics summary.

    Includes dominant emotions, average intensity, wonder index, etc.
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Log usage
    if billing_service:
        await billing_service.log_usage(
            api_key_id=api_key.api_key_id,
            project_id=api_key.project_id,
            user_id=api_key.user_id,
            metric=AgentKitMetric.EMOTION_ANALYSIS,
            end_user_id=user_id,
        )

    try:
        # Get the user's context nexus
        nexus = agent._get_or_create_nexus(user_id)
        trajectory = nexus.get_emotional_trajectory(limit=100)

        if not trajectory:
            return {
                "total_interactions": 0,
                "dominant_emotion": "neutral",
                "average_intensity": 0.5,
                "average_wonder_index": 0.0,
                "emotion_distribution": {},
                "recent_trend": "stable",
            }

        # Calculate aggregates
        emotion_counts: dict = {}
        total_intensity = 0.0
        total_wonder = 0.0

        for point in trajectory:
            emotion_counts[point.emotion] = emotion_counts.get(point.emotion, 0) + 1
            total_intensity += point.intensity
            total_wonder += point.wonder_index

        total_points = len(trajectory)

        # Find dominant emotion
        dominant_emotion = max(emotion_counts.keys(), key=lambda k: emotion_counts[k])

        # Calculate distribution percentages
        emotion_distribution = {
            emotion: {
                "count": count,
                "percentage": round(count / total_points * 100, 1),
            }
            for emotion, count in emotion_counts.items()
        }

        # Determine trend (compare first half vs second half intensity)
        if total_points >= 4:
            mid = total_points // 2
            first_half_avg = sum(p.intensity for p in trajectory[:mid]) / mid
            second_half_avg = sum(p.intensity for p in trajectory[mid:]) / (total_points - mid)
            if second_half_avg > first_half_avg + 0.1:
                trend = "increasing"
            elif second_half_avg < first_half_avg - 0.1:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "total_interactions": total_points,
            "dominant_emotion": dominant_emotion,
            "average_intensity": round(total_intensity / total_points, 3),
            "average_wonder_index": round(total_wonder / total_points, 3),
            "emotion_distribution": emotion_distribution,
            "recent_trend": trend,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)


manager = ConnectionManager()


@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat streaming."""
    # Extract userId and API key from query params
    user_id = websocket.query_params.get("userId", "anonymous")
    api_key_param = websocket.query_params.get("apiKey")

    # Validate API key if provided
    api_key_info: Optional[APIKeyInfo] = None
    if api_key_param:
        try:
            api_key_info = await validate_api_key_with_synapse(api_key_param)
        except Exception as e:
            # In development, allow connections without valid API key
            config = get_billing_config()
            if config["environment"] != "development":
                await websocket.close(code=4001, reason="Invalid API key")
                return

    await manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_json()

            # Accept both "message" and "chat" types for compatibility
            if data.get("type") in ("message", "chat"):
                payload = data.get("payload", {})
                # Accept both "content" and "message" field names for compatibility
                message = payload.get("content") or payload.get("message", "")
                user_id = payload.get("user_id") or payload.get("userId", user_id)

                # Extract mode parameters from payload
                chat_mode_str = payload.get("chat_mode")
                conversation_style_str = payload.get("conversation_style")
                personality_mode_str = payload.get("personality_mode")
                reasoning_mode_str = payload.get("reasoning_mode", "quick")

                if agent is None:
                    await manager.send_message(user_id, {
                        "type": "error",
                        "payload": {"code": "NOT_INITIALIZED", "message": "Agent not initialized"}
                    })
                    continue

                # Parse mode enums
                try:
                    chat_mode = ChatMode(chat_mode_str) if chat_mode_str else None
                    conversation_style = ConversationStyle(conversation_style_str) if conversation_style_str else None
                    personality_mode = PersonalityMode(personality_mode_str) if personality_mode_str else None
                    reasoning_mode = ReasoningMode(reasoning_mode_str) if reasoning_mode_str else ReasoningMode.QUICK
                except ValueError as e:
                    await manager.send_message(user_id, {
                        "type": "error",
                        "payload": {"code": "INVALID_MODE", "message": f"Invalid mode value: {str(e)}"}
                    })
                    continue

                # Status callback for pipeline stage updates
                async def status_callback(status_type: str, message_text: str):
                    """Send pipeline status and reasoning chain to frontend."""
                    try:
                        if status_type == "reasoning_chain":
                            await manager.send_message(user_id, {
                                "type": "reasoning_stream",
                                "payload": {"reasoning": message_text}
                            })
                        else:
                            await manager.send_message(user_id, {
                                "type": "status",
                                "payload": {"stage": status_type, "message": message_text}
                            })
                    except Exception as e:
                        print(f"[WS] Failed to send status: {e}")

                try:
                    response = await agent.chat(
                        message=message,
                        user_id=user_id,
                        chat_mode=chat_mode,
                        conversation_style=conversation_style,
                        personality_mode=personality_mode,
                        reasoning_mode=reasoning_mode,
                        status_callback=status_callback,
                    )

                    # Debug: Log response data
                    print(f"[WS DEBUG] Response emotions: {response.emotions}")
                    print(f"[WS DEBUG] Goals detected: {response.goals_detected}")
                    print(f"[WS DEBUG] Beliefs detected: {response.beliefs_detected}")

                    # Send stream_start to initialize assistant message
                    await manager.send_message(user_id, {
                        "type": "stream_start",
                        "payload": {}
                    })

                    # Stream the response in chunks
                    content = response.content
                    chunk_size = 20  # Slightly larger chunks for smoother streaming

                    for i in range(0, len(content), chunk_size):
                        chunk = content[i:i+chunk_size]
                        await manager.send_message(user_id, {
                            "type": "stream_chunk",
                            "payload": {"content": chunk}
                        })

                    # Log WebSocket message usage
                    if billing_service and api_key_info:
                        await billing_service.log_usage(
                            api_key_id=api_key_info.api_key_id,
                            project_id=api_key_info.project_id,
                            user_id=api_key_info.user_id,
                            metric=AgentKitMetric.WEBSOCKET_MESSAGE,
                            end_user_id=user_id,
                        )
                        # Register end user for monthly billing
                        await billing_service.register_end_user(
                            project_id=api_key_info.project_id,
                            external_user_id=user_id,
                        )

                    # Send stream_end with full response data including reasoning
                    stream_end_payload = {
                        "content": content,
                        "emotions": {
                            "category": response.emotions.get("category") if response.emotions else None,
                            "intensity": response.emotions.get("intensity") if response.emotions else None,
                            "complexity": "complex" if response.emotions and response.emotions.get("intensity", 0) > 0.7 else "simple",
                            "raw": response.emotions.get("raw") if response.emotions else None,
                        } if response.emotions else None,
                        "chatMode": chat_mode_str,
                        "conversationStyle": conversation_style_str,
                        "personalityMode": personality_mode_str,
                        "reasoningMode": reasoning_mode_str,
                        "wonderIndex": response.wonder_index,
                        "breakthroughDetected": response.breakthrough_detected,
                        "goalsDetected": [],
                        "beliefsDetected": [],
                    }

                    # Add reasoning chain if present (deep mode)
                    if response.reasoning:
                        stream_end_payload["reasoning"] = response.reasoning

                    # Add context metadata (goals, beliefs, memories used)
                    if response.context_metadata:
                        stream_end_payload["contextMetadata"] = response.context_metadata

                    # Add LLM usage stats
                    if response.llm_usage:
                        stream_end_payload["llmUsage"] = response.llm_usage

                    await manager.send_message(user_id, {
                        "type": "stream_end",
                        "payload": stream_end_payload,
                    })

                except Exception as e:
                    await manager.send_message(user_id, {
                        "type": "error",
                        "payload": {"code": "CHAT_ERROR", "message": str(e)}
                    })

    except WebSocketDisconnect:
        manager.disconnect(user_id)


# Print final status when module loads
print("[SERVER] All routes registered successfully")
print(f"[SERVER] Available routes: {[r.path for r in app.routes]}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
