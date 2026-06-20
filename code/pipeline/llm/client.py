"""LLM provider strategies — Bedrock and direct Anthropic API.

All other modules depend on BaseLLMClient only. Never import a concrete
implementation outside this module. Use get_client() to obtain an instance.

Provider is selected by config.LLM_PROVIDER ("bedrock" or "anthropic").
"""

from __future__ import annotations
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

import anthropic
from dotenv import load_dotenv

load_dotenv()


@dataclass
class CompletionResult:
    """Text response plus token usage from a single LLM call."""
    text: str
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class BaseLLMClient(ABC):
    """Strategy interface for LLM providers."""

    @abstractmethod
    def complete(self, system: str, user: str, max_tokens: int = 1024) -> CompletionResult:
        """Send a prompt and return the response with token counts.

        Args:
            system: System prompt.
            user: User message.
            max_tokens: Maximum tokens in the response.

        Returns:
            CompletionResult with text and input/output token counts.

        Raises:
            anthropic.APIError: On API-level failures.
        """


class BedrockLLMClient(BaseLLMClient):
    """Anthropic via AWS Bedrock. Credentials from AWS_* env vars or IAM role."""

    def __init__(self, model: str) -> None:
        self._model = model
        self._client = anthropic.AnthropicBedrock(
            aws_region=os.environ["AWS_REGION"],
        )

    def complete(self, system: str, user: str, max_tokens: int = 1024) -> CompletionResult:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=0,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return CompletionResult(
            text=message.content[0].text,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )


class AnthropicLLMClient(BaseLLMClient):
    """Anthropic direct API. Credentials from ANTHROPIC_API_KEY env var."""

    def __init__(self, model: str) -> None:
        self._model = model
        self._client = anthropic.Anthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"],
        )

    def complete(self, system: str, user: str, max_tokens: int = 1024) -> CompletionResult:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=0,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return CompletionResult(
            text=message.content[0].text,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )


_PROVIDERS: dict[str, type[BaseLLMClient]] = {
    "bedrock": BedrockLLMClient,
    "anthropic": AnthropicLLMClient,
}


def get_client(model: str) -> BaseLLMClient:
    """Return the configured LLM client for the given model.

    Provider is read from config.LLM_PROVIDER. Raises KeyError for unknown providers.
    """
    import config
    provider = config.LLM_PROVIDER
    if provider not in _PROVIDERS:
        raise KeyError(f"Unknown LLM provider {provider!r}. Choose from: {list(_PROVIDERS)}")
    return _PROVIDERS[provider](model)
