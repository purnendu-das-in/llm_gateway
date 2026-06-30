from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ChatCompletionRequest(BaseModel):
    model: str = "auto"
    task_type: str | None = None
    messages: list[ChatMessage] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("task_type")
    @classmethod
    def normalize_task_type(cls, value: str | None) -> str | None:
        return value.lower() if value else value

    def combined_prompt(self) -> str:
        return "\n".join(message.content for message in self.messages)


class Usage(BaseModel):
    input_tokens: int
    output_tokens: int
    cost_usd: float


class EvalResult(BaseModel):
    name: str
    passed: bool
    score: float


class ChatCompletionResponse(BaseModel):
    request_id: str
    model_used: str
    fallback_used: bool
    usage: Usage
    evals: list[EvalResult]
    response: ChatMessage
