"""
ANIMA Agent Server - Entry Point

Uses the SDK's built-in server with create_app() factory.
This provides full API routes, WebSocket handling, and proper dependency injection.

Usage:
    python main.py
    # OR
    uvicorn main:app --reload --port 8000
"""

import os
import sys

# Add the Python SDK to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'python'))

from synapse_anima.server import create_app, run_server

# Create the FastAPI app using SDK's factory function
app = create_app()

if __name__ == "__main__":
    run_server(reload=True)
