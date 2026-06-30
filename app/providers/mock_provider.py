from app.providers.base import LLMProvider, ProviderResponse
from app.schemas.chat import ChatCompletionRequest


class MockProvider(LLMProvider):
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def complete(self, request: ChatCompletionRequest, sanitized_prompt: str) -> ProviderResponse:
        task = request.task_type or "general"
        if task == "document_extraction":
            content = '{"status":"ok","summary":"Mock extraction completed."}'
        else:
            content = (
                f"[{self.model_name}] Mock {task} response. "
                f"Processed {len(sanitized_prompt)} sanitized characters."
            )
        return ProviderResponse(
            content=content,
            input_tokens=_estimate_tokens(sanitized_prompt),
            output_tokens=_estimate_tokens(content),
        )


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))
