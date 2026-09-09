# Synapse Anima FastAPI Server

Production-ready FastAPI server implementation for the Synapse Anima Agent Kit with WebSocket streaming, REST API endpoints, and comprehensive emotion intelligence.

## Features

- **FastAPI Application**: Modern, async Python web framework
- **WebSocket Streaming**: Real-time chat with streaming responses
- **REST API**: Complete CRUD operations for beliefs, goals, memories, and preferences
- **Emotion Analysis**: Real-time emotion tracking via SYNAPSE API
- **Dependency Injection**: Clean architecture with app state management
- **CORS Support**: Configurable cross-origin resource sharing
- **Error Handling**: Comprehensive error responses with proper HTTP status codes
- **Logging**: Structured logging with loguru
- **Health Checks**: Built-in health and status endpoints
- **Heartbeat/Keep-Alive**: WebSocket connection management
- **Lifespan Management**: Proper startup and shutdown handling

## Architecture

### Components

1. **app.py** - Application factory and configuration
   - `create_app()` - FastAPI app factory function
   - `run_server()` - Convenience function to start server
   - `AppState` - Dependency injection container
   - Lifespan management for resources
   - CORS and middleware configuration

2. **websocket.py** - WebSocket handler for streaming chat
   - `WebSocketHandler` - Manages WebSocket connections
   - Real-time chat with streaming responses
   - Connection tracking and heartbeat
   - Status callbacks for processing stages

3. **routes.py** - REST API endpoint definitions
   - Beliefs API (7 endpoints)
   - Goals API (6 endpoints)
   - Memory API (5 endpoints)
   - Preferences API (4 endpoints)
   - Chat endpoint (non-streaming)
   - Pydantic models for request/response validation

## Quick Start

### 1. Basic Usage

```python
from synapse_anima.server import run_server

# Run with environment variables
run_server()
```

### 2. Custom Configuration

```python
from synapse_anima import AnimaConfig
from synapse_anima.server import create_app

config = AnimaConfig(
    llm_provider="mistral",
    mistral_api_key="your-api-key",
    synapse_api_key="your-synapse-key",
    server_port=8080,
    cors_origins=["http://localhost:3000"],
)

app = create_app(config)
```

### 3. Run with Uvicorn

```bash
# Using the run_server() function
python -m synapse_anima.server.example

# Or directly with uvicorn
uvicorn synapse_anima.server.example:app --reload
```

## API Endpoints

### Health & Status

- `GET /health` - Health check
- `GET /` - API information

### Chat

- `POST /api/v1/chat` - Chat with agent (non-streaming)
- `WebSocket /ws/chat` - Real-time streaming chat

### Beliefs API

- `POST /api/v1/beliefs` - Create belief
- `GET /api/v1/beliefs` - Get beliefs with filters
- `PATCH /api/v1/beliefs/{belief_id}/strength` - Update strength
- `POST /api/v1/beliefs/{belief_id}/confirm` - Confirm belief
- `DELETE /api/v1/beliefs/{belief_id}` - Delete belief
- `POST /api/v1/beliefs/{belief_id}/link-goal` - Link to goal
- `GET /api/v1/beliefs/statistics` - Get statistics

### Goals API

- `POST /api/v1/goals` - Create goal
- `GET /api/v1/goals` - Get goals with filters
- `GET /api/v1/goals/{goal_id}` - Get single goal
- `PATCH /api/v1/goals/{goal_id}/progress` - Update progress
- `GET /api/v1/goals/statistics` - Get statistics
- `DELETE /api/v1/goals/{goal_id}` - Delete goal

### Memory API

- `POST /api/v1/memories` - Create memory
- `GET /api/v1/memories` - Get memories with filters
- `GET /api/v1/memories/search` - Search memories
- `GET /api/v1/memories/breakthroughs` - Get breakthroughs
- `GET /api/v1/memories/statistics` - Get statistics

### Preferences API

- `GET /api/v1/preferences` - Get preferences
- `PATCH /api/v1/preferences` - Update preferences
- `POST /api/v1/preferences/reset` - Reset to defaults
- `GET /api/v1/preferences/schema` - Get preference schema

## WebSocket Protocol

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat?user_id=user123&session_id=default');
```

### Message Types

#### Client → Server

**Chat Message:**
```json
{
  "type": "chat",
  "content": "Hello, how are you?",
  "personality_mode": "balanced",
  "reasoning_mode": "quick"
}
```

**Ping:**
```json
{
  "type": "ping"
}
```

**Status Request:**
```json
{
  "type": "status"
}
```

#### Server → Client

**Welcome:**
```json
{
  "type": "system",
  "event": "connected",
  "data": {
    "message": "Connected to Synapse Anima Agent",
    "user_id": "user123",
    "session_id": "default"
  }
}
```

**Status Update:**
```json
{
  "type": "status",
  "status": "analyzing_emotions",
  "message": "Analyzing emotions..."
}
```

**Emotion Analysis:**
```json
{
  "type": "emotion",
  "data": {
    "category": "joy",
    "intensity": 0.8,
    "raw": { "joy": 0.8, "trust": 0.3 }
  }
}
```

**Response Chunk:**
```json
{
  "type": "chunk",
  "content": "Hello! "
}
```

**Completion:**
```json
{
  "type": "complete",
  "metadata": {
    "model": "mistral-large-latest",
    "reasoning_mode": "quick",
    "wonder_index": 0.5
  }
}
```

**Error:**
```json
{
  "type": "error",
  "error": {
    "code": "invalid_format",
    "message": "Message must be JSON object with 'type' field"
  }
}
```

## Configuration

### Environment Variables

```bash
# Core
ANIMA_APP_NAME="Synapse Anima Agent"
ANIMA_APP_VERSION="1.0.0"

# LLM
ANIMA_LLM_PROVIDER="mistral"  # or "nous"
MISTRAL_API_KEY="your-key"
NOUS_API_KEY="your-key"

# Emotion Analysis
ANIMA_EMOTION_PROVIDER="synapse"  # or "local"
SYNAPSE_API_KEY="your-key"
SYNAPSE_BASE_URL="https://api.kaikostudios.xyz"

# Storage
ANIMA_STORAGE_PROVIDER="memory"  # or "neo4j"
NEO4J_URI="bolt://localhost:7687"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="password"

# Server
ANIMA_SERVER_HOST="0.0.0.0"
ANIMA_SERVER_PORT="8000"
ANIMA_CORS_ORIGINS="*"  # comma-separated
ANIMA_LOG_LEVEL="INFO"

# Features
ANIMA_ENABLE_EMOTIONS="true"
ANIMA_ENABLE_MEMORY="true"
ANIMA_ENABLE_CRISIS="true"
```

### Programmatic Configuration

```python
from synapse_anima import AnimaConfig

config = AnimaConfig(
    # Core
    app_name="My Agent",
    app_version="1.0.0",

    # LLM
    llm_provider="mistral",
    mistral_api_key="xxx",
    llm_temperature=0.7,
    llm_max_tokens=4096,

    # Emotion
    emotion_provider="synapse",
    synapse_api_key="xxx",
    enable_emotion_analysis=True,

    # Storage
    storage_provider="neo4j",
    storage_uri="bolt://localhost:7687",
    neo4j_username="neo4j",
    neo4j_password="password",

    # Server
    server_host="0.0.0.0",
    server_port=8080,
    cors_origins=["http://localhost:3000"],
    log_level="DEBUG",

    # Features
    enable_crisis_detection=True,
    enable_breakthrough_detection=True,
)
```

## Deployment

### Development

```bash
# With auto-reload
python -m synapse_anima.server.example

# Or
uvicorn synapse_anima.server.example:app --reload --port 8000
```

### Production with Uvicorn

```bash
uvicorn synapse_anima.server.example:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

### Production with Gunicorn

```bash
gunicorn synapse_anima.server.example:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --log-level info
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY synapse_anima synapse_anima/

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "synapse_anima.server.example:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Error Handling

All endpoints return proper HTTP status codes:

- `200 OK` - Successful GET/PATCH
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid input/validation error
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Server not initialized

Error Response Format:
```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "detail": "Additional details (debug mode only)"
}
```

## Logging

The server uses loguru for structured logging:

```python
# Logs include:
# - Request/response with timing
# - WebSocket connections/disconnections
# - Error traces
# - Component initialization

# Example output:
2024-02-04 21:00:00 | INFO     | server.app:create_app:123 | 🚀 Starting Synapse Anima Agent Server...
2024-02-04 21:00:01 | INFO     | server.app:create_app:145 | ✅ All components initialized successfully
2024-02-04 21:00:02 | INFO     | server.app:log_requests:201 | ➡️ POST /api/v1/chat
2024-02-04 21:00:03 | INFO     | server.app:log_requests:211 | ⬅️ POST /api/v1/chat [200] 1234.56ms
```

## Security Considerations

1. **CORS**: Configure `cors_origins` for production
2. **Authentication**: Implement auth_provider for user verification
3. **Rate Limiting**: Add rate limiting middleware (not included)
4. **API Keys**: Never commit API keys to version control
5. **HTTPS**: Use reverse proxy (nginx/traefik) for SSL/TLS
6. **Input Validation**: All inputs validated via Pydantic models

## Testing

```python
from fastapi.testclient import TestClient
from synapse_anima.server import create_app
from synapse_anima import AnimaConfig

def test_health_check():
    config = AnimaConfig.from_env()
    app = create_app(config)
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

## Performance

- **Async/Await**: All operations are asynchronous
- **Connection Pooling**: Storage providers use connection pools
- **Streaming**: WebSocket streaming reduces latency
- **Compression**: GZip middleware for response compression
- **Caching**: Consider adding Redis for response caching

## Monitoring

Recommended monitoring setup:

1. **Prometheus**: Export metrics
2. **Grafana**: Visualize metrics
3. **Sentry**: Error tracking
4. **DataDog/New Relic**: APM monitoring

## License

Part of Synapse Anima Agent Kit - See main project LICENSE.
