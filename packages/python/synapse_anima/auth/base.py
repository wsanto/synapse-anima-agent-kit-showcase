"""
Base interface for authentication providers in Synapse Anima Agent Kit.

This module defines the abstract base class for authentication systems.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAuthProvider(ABC):
    """Abstract base class for authentication providers.

    All auth providers (Supabase, JWT, None, etc.) must implement this interface.
    """

    @abstractmethod
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a token and return user info if valid.

        Args:
            token: Authentication token (JWT, API key, etc.)

        Returns:
            Dict with user info if valid:
                - user_id: User identifier (str)
                - email: Optional user email (str)
                - metadata: Optional additional user data (dict)
            None if token is invalid
        """
        pass

    @abstractmethod
    async def get_user_id(self, token: str) -> Optional[str]:
        """Extract user ID from token.

        Args:
            token: Authentication token

        Returns:
            str: User ID if token is valid, None otherwise
        """
        pass

    async def is_valid(self, token: str) -> bool:
        """Check if a token is valid.

        Args:
            token: Authentication token

        Returns:
            bool: True if token is valid, False otherwise
        """
        user_id = await self.get_user_id(token)
        return user_id is not None


class NoAuthProvider(BaseAuthProvider):
    """No-auth provider for development/testing.

    Always validates tokens and returns a default user ID.
    """

    def __init__(self, default_user_id: str = "default-user"):
        """Initialize no-auth provider.

        Args:
            default_user_id: User ID to return for all requests
        """
        self.default_user_id = default_user_id

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Always return default user info."""
        return {
            "user_id": self.default_user_id,
            "email": None,
            "metadata": {"auth_provider": "none"}
        }

    async def get_user_id(self, token: str) -> Optional[str]:
        """Always return default user ID."""
        return self.default_user_id
