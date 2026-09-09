"""
FastAPI Application Factory for Synapse Anima Agent Kit.

This module provides the create_app() factory function to initialize the FastAPI
application with all routers, middleware, CORS, and dependency injection.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from ..config import AnimaConfig
from ..agent import NeuralAgent
from ..providers.base import BaseLLMProvider
from ..emotion.base import BaseEmotionProvider
from ..storage.base import BaseStorageProvider
from ..auth.base import BaseAuthProvider

# Import API classes
from ..api.beliefs_api import BeliefsAPI
from ..api.goals_api import GoalsAPI
from ..api.memory_api import MemoryAPI
from ..api.preferences_api import PreferencesAPI

# Import server components
from .routes import create_router
from .websocket import WebSocketHandler


class AppState:
    """Application state container for dependency injection.

    This class holds all the initialized components that need to be shared
    across request handlers via dependency injection.

    Attributes:
        config: AnimaConfig instance with all configuration
        agent: NeuralAgent instance for chat operations
        beliefs_api: BeliefsAPI instance for beliefs management
        goals_api: GoalsAPI instance for goals management
        memory_api: MemoryAPI instance for memory management
        preferences_api: PreferencesAPI instance for preferences management
        websocket_handler: WebSocketHandler for WebSocket connections
    """

    def __init__(
        self,
        config: AnimaConfig,
        agent: NeuralAgent,
        beliefs_api: BeliefsAPI,
        goals_api: GoalsAPI,
        memory_api: MemoryAPI,
        preferences_api: PreferencesAPI,
        websocket_handler: WebSocketHandler,
    ):
        """Initialize application state.

        Args:
            config: Configuration instance
            agent: NeuralAgent instance
            beliefs_api: BeliefsAPI instance
            goals_api: GoalsAPI instance
            memory_api: MemoryAPI instance
            preferences_api: PreferencesAPI instance
            websocket_handler: WebSocketHandler instance
        """
        self.config = config
        self.agent = agent
        self.beliefs_api = beliefs_api
        self.goals_api = goals_api
        self.memory_api = memory_api
        self.preferences_api = preferences_api
        self.websocket_handler = websocket_handler


def create_app(
    config: Optional[AnimaConfig] = None,
    llm_provider: Optional[BaseLLMProvider] = None,
    emotion_provider: Optional[BaseEmotionProvider] = None,
    storage_provider: Optional[BaseStorageProvider] = None,
    auth_provider: Optional[BaseAuthProvider] = None,
) -> FastAPI:
    """Create and configure FastAPI application.

    This factory function initializes all components and sets up the FastAPI
    application with CORS, middleware, routers, and lifespan management.

    Args:
        config: Optional AnimaConfig instance (loads from env if None)
        llm_provider: Optional custom LLM provider
        emotion_provider: Optional custom emotion provider
        storage_provider: Optional custom storage provider
        auth_provider: Optional custom auth provider

    Returns:
        FastAPI: Configured FastAPI application instance

    Example:
        ```python
        from synapse_anima import AnimaConfig
        from synapse_anima.server import create_app

        # Create app with default config from environment
        app = create_app()

        # Or with custom config
        config = AnimaConfig(
            llm_provider="mistral",
            mistral_api_key="xxx",
            server_port=8080,
        )
        app = create_app(config)

        # Run with uvicorn
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
        ```
    """

    # Load config from environment if not provided
    if config is None:
        config = AnimaConfig.from_env()

    # Configure logging
    _configure_logging(config.log_level)

    # ===== Lifespan Context Manager =====

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Lifespan context manager for startup and shutdown.

        Handles initialization and cleanup of resources like storage connections,
        websocket handlers, and the neural agent.

        Args:
            app: FastAPI application instance
        """
        logger.info("🚀 Starting Synapse Anima Agent Server...")
        logger.info(f"📝 Config: LLM={config.llm_provider}, Storage={config.storage_provider}")

        # Startup: Initialize all components
        try:
            # Initialize NeuralAgent
            agent = NeuralAgent(
                config=config,
                llm_provider=llm_provider,
                emotion_provider=emotion_provider,
                storage_provider=storage_provider,
                auth_provider=auth_provider,
            )

            # Initialize API classes
            beliefs_api = BeliefsAPI(storage=agent.storage_provider)
            goals_api = GoalsAPI(storage=agent.storage_provider)
            memory_api = MemoryAPI(storage=agent.storage_provider)
            preferences_api = PreferencesAPI(storage=agent.storage_provider)

            # Initialize WebSocket handler
            websocket_handler = WebSocketHandler(
                agent=agent,
                config=config,
            )

            # Create app state
            app.state.anima = AppState(
                config=config,
                agent=agent,
                beliefs_api=beliefs_api,
                goals_api=goals_api,
                memory_api=memory_api,
                preferences_api=preferences_api,
                websocket_handler=websocket_handler,
            )

            logger.info("✅ All components initialized successfully")
            logger.info(f"🌐 Server ready on {config.server_host}:{config.server_port}")

            yield  # Server is running

        except Exception as e:
            logger.error(f"❌ Failed to initialize server: {e}")
            raise

        # Shutdown: Cleanup resources
        logger.info("🛑 Shutting down Synapse Anima Agent Server...")

        try:
            # Close agent and storage connections
            if hasattr(app.state, 'anima'):
                await app.state.anima.agent.close()

                # Close websocket handler
                await app.state.anima.websocket_handler.close()

            logger.info("✅ Server shutdown complete")

        except Exception as e:
            logger.error(f"⚠️ Error during shutdown: {e}")

    # ===== Create FastAPI App =====

    app = FastAPI(
        title=config.app_name,
        version=config.app_version,
        description="Emotionally Intelligent AI Agent with Beliefs, Goals, and Memory",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ===== CORS Middleware =====

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # ===== GZip Compression Middleware =====

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # ===== Request Logging Middleware =====

    @app.middleware("http")
    async def log_requests(request, call_next):
        """Log all HTTP requests with timing information.

        Args:
            request: Incoming request
            call_next: Next middleware in chain

        Returns:
            Response from downstream handlers
        """
        import time

        start_time = time.time()

        # Log request
        logger.info(f"➡️ {request.method} {request.url.path}")

        try:
            response = await call_next(request)

            # Log response
            duration = (time.time() - start_time) * 1000
            logger.info(
                f"⬅️ {request.method} {request.url.path} "
                f"[{response.status_code}] {duration:.2f}ms"
            )

            return response

        except Exception as e:
            logger.error(f"❌ {request.method} {request.url.path} failed: {e}")
            raise

    # ===== Error Handlers =====

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler for unhandled errors.

        Args:
            request: The request that caused the error
            exc: The exception that was raised

        Returns:
            JSONResponse with error details
        """
        logger.error(f"Unhandled exception: {exc}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "detail": str(exc) if config.log_level == "DEBUG" else None,
            },
        )

    # ===== Health Check Endpoint =====

    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint.

        Returns basic health status and component availability.

        Returns:
            dict: Health status information
        """
        return {
            "status": "healthy",
            "service": config.app_name,
            "version": config.app_version,
            "components": {
                "llm": config.llm_provider,
                "emotion": config.emotion_provider if config.enable_emotion_analysis else "disabled",
                "storage": config.storage_provider,
                "auth": config.auth_provider,
            },
        }

    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information.

        Returns:
            dict: API metadata and available endpoints
        """
        return {
            "service": config.app_name,
            "version": config.app_version,
            "description": "Emotionally Intelligent AI Agent API",
            "docs": "/docs",
            "health": "/health",
            "websocket": config.websocket_path,
            "api_version": "v1",
        }

    # ===== Mount API Router =====

    api_router = create_router()
    app.include_router(api_router, prefix="/api/v1")

    # ===== WebSocket Endpoint =====

    from fastapi import WebSocket, WebSocketDisconnect

    @app.websocket(config.websocket_path)
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time chat.

        Args:
            websocket: WebSocket connection instance
        """
        # Get user_id from query parameters
        user_id = websocket.query_params.get("user_id", "anonymous")
        session_id = websocket.query_params.get("session_id", "default")

        handler = app.state.anima.websocket_handler

        try:
            await handler.handle_connection(
                websocket=websocket,
                user_id=user_id,
                session_id=session_id,
            )
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: user={user_id}, session={session_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}", exc_info=True)

    logger.info("✅ FastAPI application created successfully")

    return app


def _configure_logging(log_level: str = "INFO") -> None:
    """Configure logging for the application.

    Sets up loguru logger with appropriate formatting and level.
    Also configures standard logging to redirect to loguru.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Remove default logger
    logger.remove()

    # Add custom logger with formatting
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # Redirect standard logging to loguru
    class InterceptHandler(logging.Handler):
        """Handler to intercept standard logging and redirect to loguru."""

        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    # Replace handlers for standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Silence noisy loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


# ===== Convenience Functions =====

def run_server(
    config: Optional[AnimaConfig] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    reload: bool = False,
) -> None:
    """Run the FastAPI server with uvicorn.

    Convenience function to start the server without manually configuring uvicorn.

    Args:
        config: Optional AnimaConfig instance
        host: Optional host override (defaults to config.server_host)
        port: Optional port override (defaults to config.server_port)
        reload: Enable auto-reload for development

    Example:
        ```python
        from synapse_anima.server import run_server

        # Run with defaults from environment
        run_server()

        # Run with custom settings
        from synapse_anima import AnimaConfig
        config = AnimaConfig.from_env()
        run_server(config, host="127.0.0.1", port=8080, reload=True)
        ```
    """
    import uvicorn

    if config is None:
        config = AnimaConfig.from_env()

    server_host = host or config.server_host
    server_port = port or config.server_port

    logger.info(f"🚀 Starting server on {server_host}:{server_port}")

    # Create app
    app = create_app(config)

    # Run with uvicorn
    uvicorn.run(
        app,
        host=server_host,
        port=server_port,
        reload=reload,
        log_level=config.log_level.lower(),
    )
