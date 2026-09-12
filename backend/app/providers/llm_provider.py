"""
LLM provider abstraction — Groq implementation with grounding.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional

import structlog

from app.core.config import settings

logger = structlog.get_logger()

_llm_provider = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> dict:
        """Generate a response."""
        ...
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Generate a streaming response."""
        ...


class GroqProvider(LLMProvider):
    """Groq API LLM provider."""
    
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        from groq import AsyncGroq
        
        if not api_key:
            logger.warning("GROQ_API_KEY not set — LLM features will fail")
        
        self.client = AsyncGroq(api_key=api_key) if api_key else None
        self.model = model
        logger.info("Groq provider initialized", model=model)
    
    async def generate(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> dict:
        if not self.client:
            raise RuntimeError("GROQ_API_KEY not configured")
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        
        choice = response.choices[0]
        return {
            "content": choice.message.content,
            "usage": {
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            "model": response.model,
        }
    
    async def generate_stream(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        if not self.client:
            raise RuntimeError("GROQ_API_KEY not configured")
        
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


def get_llm_provider() -> LLMProvider:
    """Factory — returns configured LLM provider (singleton)."""
    global _llm_provider
    
    if _llm_provider is None:
        _llm_provider = GroqProvider(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
        )
    
    return _llm_provider
