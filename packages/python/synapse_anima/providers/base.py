"""
Base interface for LLM providers in Synapse Anima Agent Kit.

This module defines the abstract base class that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Any, Optional


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM providers (Mistral, Nous, etc.) must implement this interface
    to be compatible with the Synapse Anima Agent Kit.
    """

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            model: Model identifier (e.g., "mistral-large-latest")
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Provider-specific parameters

        Returns:
            Dict containing the completion response with keys:
                - content: The generated text
                - model: Model used
                - usage: Token usage statistics (optional)
                - finish_reason: Reason for completion
        """
        pass

    @abstractmethod
    def stream_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a chat completion token by token.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            model: Model identifier
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Yields:
            str: Individual tokens or chunks of the response
        """
        yield  # type: ignore

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model for this provider.

        Returns:
            str: Default model identifier
        """
        pass

    @property
    @abstractmethod
    def quick_model(self) -> str:
        """Return the quick/fast model for this provider.

        Used for rapid responses and simple queries.

        Returns:
            str: Quick model identifier
        """
        pass

    @property
    @abstractmethod
    def deep_model(self) -> str:
        """Return the deep/powerful model for this provider.

        Used for complex reasoning and detailed responses.

        Returns:
            str: Deep model identifier
        """
        pass
