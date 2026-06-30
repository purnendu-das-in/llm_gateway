from pydantic import BaseModel


class PromptValidationResult(BaseModel):
    allowed: bool
    reason: str | None = None
    risk_level: str = "low"


RISKY_PATTERNS = [
    "ignore previous instructions",
    "reveal your system prompt",
    "bypass policy",
    "act as unrestricted",
    "delete all logs",
]

SUPPORTED_TASK_TYPES = {
    None,
    "classification",
    "summarization",
    "document_extraction",
    "question_answering",
    "code_generation",
    "reasoning",
}


def validate_prompt(prompt: str, task_type: str | None) -> PromptValidationResult:
    if not prompt.strip():
        return PromptValidationResult(allowed=False, reason="Prompt is empty.", risk_level="medium")

    if len(prompt) > 20_000:
        return PromptValidationResult(
            allowed=False,
            reason="Prompt is too long.",
            risk_level="medium",
        )

    if task_type not in SUPPORTED_TASK_TYPES:
        return PromptValidationResult(
            allowed=False,
            reason=f"Unsupported task type: {task_type}",
            risk_level="low",
        )

    lower_prompt = prompt.lower()
    for pattern in RISKY_PATTERNS:
        if pattern in lower_prompt:
            return PromptValidationResult(
                allowed=False,
                reason=f"Prompt contains possible injection pattern: {pattern}",
                risk_level="high",
            )

    return PromptValidationResult(allowed=True)
