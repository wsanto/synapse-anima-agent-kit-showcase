"""
Synapse Anima Agent Kit - FastAPI Server

Server implementation with WebSocket streaming and REST endpoints.
"""

from .app import create_app, run_server, AppState
from .websocket import WebSocketHandler
from .routes import create_router

__all__ = [
    "create_app",
    "run_server",
    "AppState",
    "WebSocketHandler",
    "create_router",
]
