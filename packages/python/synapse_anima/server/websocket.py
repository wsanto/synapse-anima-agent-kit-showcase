"""
WebSocket Handler for Real-Time Chat with Synapse Anima Agent.

This module provides the WebSocketHandler class for managing WebSocket connections,
streaming chat responses, and real-time emotion analysis.
"""

import asyncio
import json
from typing import Dict, Optional, Set, Any
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from ..agent import NeuralAgent
from ..config import AnimaConfig, ReasoningMode, PersonalityMode
from ..types import MessageRole


class ConnectionInfo:
    """Information about an active WebSocket connection.

    Attributes:
        user_id: User identifier
        session_id: Session/context identifier
        connected_at: Timestamp when connection was established
        message_count: Number of messages sent in this connection
        last_activity: Timestamp of last activity
    """

    def __init__(self, user_id: str, session_id: str):
        """Initialize connection info.

        Args:
            user_id: User identifier
            session_id: Session identifier
        """
        self.user_id = user_id
        self.session_id = session_id
        self.connected_at = datetime.now()
        self.message_count = 0
        self.last_activity = datetime.now()

    def update_activity(self) -> None:
        """Update last activity timestamp and increment message count."""
        self.last_activity = datetime.now()
        self.message_count += 1


class WebSocketHandler:
    """Handler for WebSocket connections and streaming chat.

    Manages WebSocket lifecycle, message handling, streaming responses,
    and real-time emotion analysis. Supports heartbeat/keep-alive,
    connection tracking, and graceful error handling.

    Attributes:
        agent: NeuralAgent instance for chat operations
        config: AnimaConfig instance with server settings
        active_connections: Set of active WebSocket connections
        connection_info: Dict mapping websocket to connection metadata
        heartbeat_interval: Seconds between heartbeat pings
        heartbeat_tasks: Dict of running heartbeat tasks
    """

    def __init__(
        self,
        agent: NeuralAgent,
        config: AnimaConfig,
        heartbeat_interval: int = 30,
    ):
        """Initialize WebSocket handler.

        Args:
            agent: NeuralAgent instance for processing messages
            config: Configuration instance
            heartbeat_interval: Seconds between heartbeat pings (default: 30)
        """
        self.agent = agent
        self.config = config
        self.heartbeat_interval = heartbeat_interval

        # Connection tracking
        self.active_connections: Set[WebSocket] = set()
        self.connection_info: Dict[WebSocket, ConnectionInfo] = {}
        self.heartbeat_tasks: Dict[WebSocket, asyncio.Task] = {}

        logger.info(f"✅ WebSocketHandler initialized (heartbeat: {heartbeat_interval}s)")

    async def handle_connection(
        self,
        websocket: WebSocket,
        user_id: str,
        session_id: str = "default",
    ) -> None:
        """Handle a WebSocket connection lifecycle.

        Accepts connection, manages message loop, and handles cleanup.

        Args:
            websocket: WebSocket connection instance
            user_id: User identifier
            session_id: Session/context identifier

        Raises:
            WebSocketDisconnect: When client disconnects
        """
        # Accept connection
        await websocket.accept()

        # Track connection
        self.active_connections.add(websocket)
        self.connection_info[websocket] = ConnectionInfo(user_id, session_id)

        logger.info(
            f"🔌 WebSocket connected: user={user_id}, session={session_id}, "
            f"total_connections={len(self.active_connections)}"
        )

        # Send welcome message
        await self._send_message(
            websocket,
            {
                "type": "system",
                "event": "connected",
                "data": {
                    "message": "Connected to Synapse Anima Agent",
                    "user_id": user_id,
                    "session_id": session_id,
                    "features": {
                        "emotion_analysis": self.config.enable_emotion_analysis,
                        "memory_persistence": self.config.enable_memory_persistence,
                        "streaming": True,
                    },
                },
            },
        )

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(websocket)
        )
        self.heartbeat_tasks[websocket] = heartbeat_task

        try:
            # Message handling loop
            while True:
                # Receive message
                data = await websocket.receive_text()

                # Update activity
                self.connection_info[websocket].update_activity()

                # Parse and handle message
                await self._handle_message(websocket, data, user_id, session_id)

        except WebSocketDisconnect:
            logger.info(f"🔌 WebSocket disconnected: user={user_id}, session={session_id}")
            raise

        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}", exc_info=True)

            # Send error to client
            await self._send_error(websocket, "internal_error", str(e))

        finally:
            # Cleanup
            await self._cleanup_connection(websocket)

    async def _handle_message(
        self,
        websocket: WebSocket,
        data: str,
        user_id: str,
        session_id: str,
    ) -> None:
        """Handle incoming WebSocket message.

        Parses message, routes to appropriate handler, and sends response.

        Args:
            websocket: WebSocket connection
            data: Raw message data (JSON string)
            user_id: User identifier
            session_id: Session identifier
        """
        try:
            # Parse JSON
            message = json.loads(data)

            # Validate message format
            if not isinstance(message, dict) or "type" not in message:
                await self._send_error(
                    websocket,
                    "invalid_format",
                    "Message must be JSON object with 'type' field",
                )
                return

            msg_type = message.get("type")

            # Route to handler based on type
            if msg_type == "chat":
                await self._handle_chat(websocket, message, user_id, session_id)

            elif msg_type == "ping":
                # Respond to ping with pong
                await self._send_message(websocket, {"type": "pong"})

            elif msg_type == "status":
                # Send connection status
                await self._send_status(websocket, user_id, session_id)

            else:
                await self._send_error(
                    websocket,
                    "unknown_type",
                    f"Unknown message type: {msg_type}",
                )

        except json.JSONDecodeError as e:
            await self._send_error(
                websocket,
                "invalid_json",
                f"Failed to parse JSON: {e}",
            )

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await self._send_error(websocket, "processing_error", str(e))

    async def _handle_chat(
        self,
        websocket: WebSocket,
        message: Dict[str, Any],
        user_id: str,
        session_id: str,
    ) -> None:
        """Handle chat message with streaming response.

        Processes user message through agent and streams response chunks,
        emotion analysis, and metadata in real-time.

        Args:
            websocket: WebSocket connection
            message: Parsed message dict with 'content' and optional settings
            user_id: User identifier
            session_id: Session identifier
        """
        # Extract message content
        content = message.get("content", "").strip()

        if not content:
            await self._send_error(websocket, "empty_message", "Message content is required")
            return

        # Extract optional parameters
        personality_mode = message.get("personality_mode")
        reasoning_mode = message.get("reasoning_mode", "quick")

        # Convert to enums
        try:
            if personality_mode:
                personality_mode = PersonalityMode(personality_mode)
            reasoning_mode = ReasoningMode(reasoning_mode)
        except ValueError as e:
            await self._send_error(websocket, "invalid_parameter", str(e))
            return

        logger.info(f"💬 Chat message from {user_id}: {content[:50]}...")

        # Send acknowledgment
        await self._send_message(
            websocket,
            {
                "type": "message_received",
                "message_id": message.get("id", "unknown"),
            },
        )

        # Create status callback for pipeline stages
        async def status_callback(status_type: str, status_message: str):
            """Send status updates during processing."""
            await self._send_message(
                websocket,
                {
                    "type": "status",
                    "status": status_type,
                    "message": status_message,
                },
            )

        try:
            # ===== STREAMING APPROACH =====
            # For now, use non-streaming chat and send complete response
            # TODO: Implement true token-by-token streaming via agent.stream_chat()

            # Process message through agent
            response = await self.agent.chat(
                message=content,
                user_id=user_id,
                session_id=session_id,
                personality_mode=personality_mode,
                reasoning_mode=reasoning_mode,
                status_callback=status_callback,
            )

            # Send emotion analysis if available
            if response.emotions:
                await self._send_message(
                    websocket,
                    {
                        "type": "emotion",
                        "data": response.emotions,
                    },
                )

            # Send response content in chunks (simulate streaming)
            # Split by sentences for better UX
            chunks = self._split_into_chunks(response.content)

            for chunk in chunks:
                await self._send_message(
                    websocket,
                    {
                        "type": "chunk",
                        "content": chunk,
                    },
                )
                # Small delay to simulate streaming
                await asyncio.sleep(0.05)

            # Send completion with metadata
            await self._send_message(
                websocket,
                {
                    "type": "complete",
                    "metadata": {
                        "reasoning": response.reasoning,
                        "goals_detected": response.goals_detected,
                        "beliefs_detected": response.beliefs_detected,
                        "wonder_index": response.wonder_index,
                        "breakthrough_detected": response.breakthrough_detected,
                        "crisis_detected": response.crisis_detected,
                        **response.metadata,
                    },
                },
            )

            logger.info(f"✅ Chat response sent to {user_id}")

        except Exception as e:
            logger.error(f"Error processing chat: {e}", exc_info=True)
            await self._send_error(
                websocket,
                "chat_error",
                f"Failed to process message: {str(e)}",
            )

    def _split_into_chunks(self, text: str, chunk_size: int = 100) -> list:
        """Split text into chunks for streaming.

        Splits by sentences where possible, falling back to character chunks.

        Args:
            text: Text to split
            chunk_size: Approximate characters per chunk

        Returns:
            List of text chunks
        """
        if not text:
            return []

        # Split by sentences
        import re
        sentences = re.split(r'([.!?]+\s+)', text)

        chunks = []
        current_chunk = ""

        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]  # Add punctuation

            # If adding sentence exceeds chunk size, flush current chunk
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence

        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks if chunks else [text]

    async def _send_status(
        self,
        websocket: WebSocket,
        user_id: str,
        session_id: str,
    ) -> None:
        """Send connection status information.

        Args:
            websocket: WebSocket connection
            user_id: User identifier
            session_id: Session identifier
        """
        conn_info = self.connection_info.get(websocket)

        if conn_info:
            await self._send_message(
                websocket,
                {
                    "type": "status",
                    "data": {
                        "user_id": user_id,
                        "session_id": session_id,
                        "connected_at": conn_info.connected_at.isoformat(),
                        "message_count": conn_info.message_count,
                        "last_activity": conn_info.last_activity.isoformat(),
                        "total_connections": len(self.active_connections),
                    },
                },
            )

    async def _heartbeat_loop(self, websocket: WebSocket) -> None:
        """Heartbeat loop to keep connection alive.

        Sends periodic ping messages to detect disconnections.

        Args:
            websocket: WebSocket connection
        """
        try:
            while websocket in self.active_connections:
                await asyncio.sleep(self.heartbeat_interval)

                # Send heartbeat ping
                try:
                    await self._send_message(
                        websocket,
                        {"type": "heartbeat", "timestamp": datetime.now().isoformat()},
                    )
                except Exception:
                    # Connection likely closed
                    break

        except asyncio.CancelledError:
            # Task was cancelled during cleanup
            pass
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")

    async def _send_message(
        self,
        websocket: WebSocket,
        data: Dict[str, Any],
    ) -> None:
        """Send JSON message to WebSocket client.

        Args:
            websocket: WebSocket connection
            data: Data to send (will be JSON-encoded)
        """
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise

    async def _send_error(
        self,
        websocket: WebSocket,
        error_code: str,
        error_message: str,
    ) -> None:
        """Send error message to client.

        Args:
            websocket: WebSocket connection
            error_code: Error code identifier
            error_message: Human-readable error message
        """
        await self._send_message(
            websocket,
            {
                "type": "error",
                "error": {
                    "code": error_code,
                    "message": error_message,
                },
            },
        )

    async def _cleanup_connection(self, websocket: WebSocket) -> None:
        """Clean up connection resources.

        Removes connection from tracking, cancels heartbeat task.

        Args:
            websocket: WebSocket connection to clean up
        """
        # Cancel heartbeat task
        if websocket in self.heartbeat_tasks:
            task = self.heartbeat_tasks[websocket]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.heartbeat_tasks[websocket]

        # Remove from tracking
        self.active_connections.discard(websocket)
        self.connection_info.pop(websocket, None)

        logger.info(
            f"🔌 Connection cleaned up, remaining: {len(self.active_connections)}"
        )

    async def broadcast(self, message: Dict[str, Any], exclude: Optional[WebSocket] = None) -> None:
        """Broadcast message to all connected clients.

        Useful for notifications, system messages, etc.

        Args:
            message: Message to broadcast
            exclude: Optional WebSocket to exclude from broadcast
        """
        disconnected = set()

        for connection in self.active_connections:
            if connection == exclude:
                continue

            try:
                await self._send_message(connection, message)
            except Exception:
                # Connection likely closed
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            await self._cleanup_connection(connection)

    async def close(self) -> None:
        """Close all active WebSocket connections.

        Called during server shutdown.
        """
        logger.info(f"Closing {len(self.active_connections)} WebSocket connections...")

        # Send shutdown notice
        shutdown_message = {
            "type": "system",
            "event": "shutdown",
            "data": {"message": "Server is shutting down"},
        }

        # Notify all clients
        for connection in list(self.active_connections):
            try:
                await self._send_message(connection, shutdown_message)
                await connection.close(code=1000, reason="Server shutdown")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")

            # Cleanup
            await self._cleanup_connection(connection)

        logger.info("✅ All WebSocket connections closed")

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket handler statistics.

        Returns:
            Dict with connection statistics
        """
        total_messages = sum(
            info.message_count for info in self.connection_info.values()
        )

        return {
            "active_connections": len(self.active_connections),
            "total_messages": total_messages,
            "heartbeat_interval": self.heartbeat_interval,
            "connections": [
                {
                    "user_id": info.user_id,
                    "session_id": info.session_id,
                    "connected_at": info.connected_at.isoformat(),
                    "message_count": info.message_count,
                    "last_activity": info.last_activity.isoformat(),
                }
                for info in self.connection_info.values()
            ],
        }
