"""
Mistral AI Provider

LLM provider implementation for Mistral AI models.
"""

import json
import os
from typing import AsyncGenerator, List, Dict, Any, Optional
import httpx
from .base import BaseLLMProvider


class MistralProvider(BaseLLMProvider):
    """Mistral AI LLM provider implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.mistral.ai/v1",
        default_model: Optional[str] = None,
        quick_model_name: str = "mistral-small-latest",
        deep_model_name: str = "mistral-large-latest",
        temperature: float = 0.7,
        timeout: int = 120,
    ):
        """
        Initialize Mistral provider.

        Args:
            api_key: Mistral API key (defaults to MISTRAL_API_KEY env var)
            base_url: API base URL
            default_model: Default model to use (defaults to quick_model_name)
            quick_model_name: Model for quick, simple tasks
            deep_model_name: Model for complex reasoning
            temperature: Default sampling temperature
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("Mistral API key is required")

        self.base_url = base_url
        self._quick_model = quick_model_name
        self._deep_model = deep_model_name
        self._default_model = default_model or quick_model_name
        self._temperature = temperature
        self.timeout = timeout

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout),
        )

    @property
    def default_model(self) -> str:
        """Return the default model."""
        return self._default_model

    @property
    def quick_model(self) -> str:
        """Return the quick/fast model."""
        return self._quick_model

    @property
    def deep_model(self) -> str:
        """Return the deep/powerful model."""
        return self._deep_model

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = 2000,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (defaults to default_model)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters

        Returns:
            Response dict with 'content', 'model', 'usage', etc.
        """
        model = model or self._default_model
        temperature = temperature if temperature is not None else self._temperature

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }

        if stream:
            raise ValueError("Use stream_completion for streaming responses")

        response = await self.client.post("/chat/completions", json=payload)
        response.raise_for_status()

        data = response.json()

        return {
            "content": data["choices"][0]["message"]["content"],
            "model": data["model"],
            "usage": data.get("usage", {}),
            "finish_reason": data["choices"][0].get("finish_reason"),
        }

    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream a chat completion token by token.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (defaults to default_model)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Yields:
            Content chunks as they arrive
        """
        model = model or self._default_model
        temperature = temperature if temperature is not None else self._temperature

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **kwargs
        }

        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.strip() or line == "data: [DONE]":
                    continue

                if line.startswith("data: "):
                    try:
                        chunk_data = json.loads(line[6:])
                        delta = chunk_data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
