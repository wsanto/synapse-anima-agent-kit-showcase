"""
Synapse SDK API Key Authentication Middleware

Validates API keys against the Synapse SDK API and extracts
project/user information for billing and access control.
"""

import os
from dataclasses import dataclass
from typing import Optional
from functools import lru_cache

import httpx
from fastapi import Header, HTTPException, Request


class AuthError(Exception):
    """Authentication error."""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@dataclass
class APIKeyInfo:
    """Information extracted from a validated API key."""
    api_key_id: str
    project_id: str
    user_id: str
    key_type: str
    is_active: bool
    project_name: Optional[str] = None


@lru_cache()
def get_synapse_config():
    """Get Synapse SDK configuration from environment."""
    return {
        "base_url": os.getenv("SYNAPSE_BASE_URL", "https://api.kaikostudios.xyz"),
        "internal_key": os.getenv("SYNAPSE_INTERNAL_KEY", ""),
        "environment": os.getenv("ANIMA_ENVIRONMENT", "development"),
    }


async def validate_api_key_with_synapse(api_key: str) -> APIKeyInfo:
    """
    Validate an API key against the Synapse SDK API.

    Args:
        api_key: The API key to validate (format: sk_{env}_{random})

    Returns:
        APIKeyInfo with key details if valid

    Raises:
        AuthError if the key is invalid or validation fails
    """
    config = get_synapse_config()

    # Skip validation in development if no internal key is configured
    if config["environment"] == "development" and not config["internal_key"]:
        # Return mock data for local development
        return APIKeyInfo(
            api_key_id="dev-key-id",
            project_id="dev-project-id",
            user_id="dev-user-id",
            key_type="synapse",
            is_active=True,
            project_name="Development Project",
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{config['base_url']}/v1/billing/internal/agent-kit/verify-key",
                headers={
                    "x-internal-key": config["internal_key"],
                    "Content-Type": "application/json",
                },
                json={"apiKey": api_key}
            )

            if response.status_code == 401:
                raise AuthError("Invalid API key", 401)
            elif response.status_code == 403:
                raise AuthError("API key is not active", 403)
            elif response.status_code != 200:
                raise AuthError(f"API key validation failed: {response.text}", response.status_code)

            result = response.json()
            data = result.get("data", result)

            return APIKeyInfo(
                api_key_id=data.get("apiKeyId", ""),
                project_id=data.get("projectId", ""),
                user_id=data.get("userId", ""),
                key_type=data.get("keyType", "synapse"),
                is_active=data.get("isActive", True),
                project_name=data.get("projectName"),
            )

    except httpx.RequestError as e:
        raise AuthError(f"Failed to validate API key: {str(e)}", 503)


async def validate_api_key(
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    authorization: Optional[str] = Header(None),
) -> APIKeyInfo:
    """
    FastAPI dependency for validating API keys.

    Accepts API key via:
    - x-api-key header
    - Authorization: Bearer <key> header

    Args:
        x_api_key: API key from x-api-key header
        authorization: API key from Authorization header

    Returns:
        APIKeyInfo with validated key details

    Raises:
        HTTPException if no key provided or key is invalid
    """
    # Extract API key from headers
    api_key = x_api_key

    if not api_key and authorization:
        # Try to extract from Bearer token
        if authorization.startswith("Bearer "):
            api_key = authorization[7:]
        else:
            api_key = authorization

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide via x-api-key header or Authorization: Bearer <key>",
        )

    try:
        return await validate_api_key_with_synapse(api_key)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


def get_current_api_key(request: Request) -> Optional[APIKeyInfo]:
    """
    Get the current API key info from the request state.

    This is set by the authentication middleware after validation.

    Args:
        request: The FastAPI request object

    Returns:
        APIKeyInfo if authenticated, None otherwise
    """
    return getattr(request.state, "api_key_info", None)
