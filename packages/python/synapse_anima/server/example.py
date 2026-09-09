"""
Example usage of Synapse Anima FastAPI Server.

This file demonstrates how to start and configure the server.
"""

import os
from synapse_anima import AnimaConfig
from synapse_anima.server import create_app, run_server


# ===== Example 1: Run server with environment variables =====

def example_1_env_config():
    """Run server with configuration from environment variables.

    Set these environment variables before running:
    - MISTRAL_API_KEY or NOUS_API_KEY
    - SYNAPSE_API_KEY (for emotion analysis)
    - ANIMA_LLM_PROVIDER (mistral or nous)
    - ANIMA_SERVER_PORT (default: 8000)
    """
    run_server()


# ===== Example 2: Run server with custom configuration =====

def example_2_custom_config():
    """Run server with custom configuration."""

    config = AnimaConfig(
        # Core settings
        app_name="My Anima Agent",
        app_version="1.0.0",

        # LLM settings
        llm_provider="mistral",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        llm_temperature=0.7,

        # Emotion analysis
        emotion_provider="synapse",
        synapse_api_key=os.getenv("SYNAPSE_API_KEY"),
        enable_emotion_analysis=True,

        # Storage
        storage_provider="memory",  # or "neo4j"
        enable_memory_persistence=True,

        # Server settings
        server_host="0.0.0.0",
        server_port=8080,
        cors_origins=["http://localhost:3000", "https://myapp.com"],
        log_level="INFO",

        # Features
        enable_crisis_detection=True,
        enable_breakthrough_detection=True,
    )

    run_server(config, reload=True)  # reload=True for development


# ===== Example 3: Create app instance for custom deployment =====

def example_3_custom_deployment():
    """Create app instance for deployment with uvicorn or gunicorn.

    Usage with uvicorn:
        uvicorn example:app --host 0.0.0.0 --port 8000 --workers 4

    Usage with gunicorn:
        gunicorn example:app -w 4 -k uvicorn.workers.UvicornWorker
    """

    config = AnimaConfig.from_env()
    app = create_app(config)

    return app


# ===== Example 4: Custom providers =====

def example_4_custom_providers():
    """Use custom provider implementations."""

    from synapse_anima.providers import MistralProvider
    from synapse_anima.emotion import SynapseEmotionProvider
    from synapse_anima.storage import InMemoryStorageProvider

    config = AnimaConfig.from_env()

    # Initialize custom providers
    llm_provider = MistralProvider(
        api_key=os.getenv("MISTRAL_API_KEY"),
        default_model="mistral-large-latest",
        temperature=0.8,
    )

    emotion_provider = SynapseEmotionProvider(
        api_key=os.getenv("SYNAPSE_API_KEY"),
        base_url="https://api.kaikostudios.xyz",
    )

    storage_provider = InMemoryStorageProvider()

    # Create app with custom providers
    app = create_app(
        config=config,
        llm_provider=llm_provider,
        emotion_provider=emotion_provider,
        storage_provider=storage_provider,
    )

    return app


# ===== Example 5: Production deployment with Neo4j =====

def example_5_production_neo4j():
    """Production configuration with Neo4j storage."""

    config = AnimaConfig(
        # LLM
        llm_provider="mistral",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),

        # Emotion
        emotion_provider="synapse",
        synapse_api_key=os.getenv("SYNAPSE_API_KEY"),

        # Neo4j Storage
        storage_provider="neo4j",
        storage_uri=os.getenv("NEO4J_URI"),  # e.g., "bolt://localhost:7687"
        neo4j_username=os.getenv("NEO4J_USERNAME"),
        neo4j_password=os.getenv("NEO4J_PASSWORD"),

        # Server
        server_host="0.0.0.0",
        server_port=8000,
        cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        log_level="INFO",

        # All features enabled
        enable_emotion_analysis=True,
        enable_memory_persistence=True,
        enable_crisis_detection=True,
        enable_breakthrough_detection=True,
    )

    app = create_app(config)
    return app


# ===== Main entry point =====

if __name__ == "__main__":
    # Choose which example to run

    # Option 1: Quick start with env config
    # example_1_env_config()

    # Option 2: Custom config with auto-reload
    example_2_custom_config()

    # Option 3: For deployment, create app instance
    # app = example_3_custom_deployment()
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)
