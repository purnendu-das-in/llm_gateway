from abc import ABC, abstractmethod

from pydantic import BaseModel

from app.schemas.chat import ChatCompletionRequest


class ProviderError(Exception):
    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.status_code = status_code


class ProviderResponse(BaseModel):
    content: str
    input_tokens: int
    output_tokens: int


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, request: ChatCompletionRequest, sanitized_prompt: str) -> ProviderResponse:
        """Return a provider response for the sanitized prompt."""
