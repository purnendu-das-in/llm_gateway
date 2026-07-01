from pydantic import BaseModel

from app.auth.tenant_context import TenantContext
from app.providers.base import LLMProvider
from app.providers.mock_provider import MockProvider
from app.resilience.circuit_breaker import circuit_breaker
from app.schemas.chat import ChatCompletionRequest


class RoutedModel(BaseModel):
    model_name: str
    provider: LLMProvider

    model_config = {"arbitrary_types_allowed": True}


MODEL_REGISTRY = {
    "mock-fast": MockProvider("mock-fast"),
    "mock-quality": MockProvider("mock-quality"),
    "mock-long-context": MockProvider("mock-long-context"),
}

MODEL_CONTEXT_WINDOWS = {
    "mock-fast": 4_000,
    "mock-quality": 8_000,
    "mock-long-context": 32_000,
}

FALLBACK_MATRIX = {
    "mock-fast": ["mock-quality", "mock-long-context"],
    "mock-quality": ["mock-fast", "mock-long-context"],
    "mock-long-context": ["mock-quality", "mock-fast"],
}


def available_models() -> list[dict[str, str]]:
    return [
        {
            "id": "mock-fast",
            "provider": "mock",
            "description": "Low-cost demo model",
            "context_window": str(MODEL_CONTEXT_WINDOWS["mock-fast"]),
        },
        {
            "id": "mock-quality",
            "provider": "mock",
            "description": "Higher-quality demo model",
            "context_window": str(MODEL_CONTEXT_WINDOWS["mock-quality"]),
        },
        {
            "id": "mock-long-context",
            "provider": "mock",
            "description": "Long-context fallback model",
            "context_window": str(MODEL_CONTEXT_WINDOWS["mock-long-context"]),
        },
    ]


def route_model(request: ChatCompletionRequest, tenant: TenantContext) -> RoutedModel:
    prompt_tokens = estimate_tokens(request.combined_prompt())
    requested_model = request.model
    if requested_model and requested_model != "auto" and requested_model in tenant.allowed_models:
        return _first_healthy_model([requested_model], tenant, prompt_tokens)

    candidates = _semantic_candidates(request, tenant)
    return _first_healthy_model(candidates, tenant, prompt_tokens)


def fallback_candidates(model_name: str, tenant: TenantContext) -> list[RoutedModel]:
    candidates = [model_name, *FALLBACK_MATRIX.get(model_name, [])]
    return [
        RoutedModel(model_name=candidate, provider=MODEL_REGISTRY[candidate])
        for candidate in candidates
        if candidate in tenant.allowed_models and not circuit_breaker.is_open(candidate)
    ]


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def _semantic_candidates(request: ChatCompletionRequest, tenant: TenantContext) -> list[str]:
    prompt = request.combined_prompt().strip().lower()
    if (
        request.task_type in {"reasoning", "code_generation"}
        or "debug" in prompt
        or "architecture" in prompt
    ) and "mock-quality" in tenant.allowed_models:
        return ["mock-quality", *FALLBACK_MATRIX["mock-quality"]]

    if (
        len(prompt.split()) > MODEL_CONTEXT_WINDOWS["mock-fast"]
        and "mock-long-context" in tenant.allowed_models
    ):
        return ["mock-long-context", *FALLBACK_MATRIX["mock-long-context"]]

    return [tenant.allowed_models[0], *FALLBACK_MATRIX.get(tenant.allowed_models[0], [])]


def _first_healthy_model(
    candidates: list[str],
    tenant: TenantContext,
    prompt_tokens: int,
) -> RoutedModel:
    for model_name in candidates:
        if model_name not in tenant.allowed_models:
            continue
        if circuit_breaker.is_open(model_name):
            continue
        if prompt_tokens > MODEL_CONTEXT_WINDOWS[model_name]:
            continue
        return RoutedModel(model_name=model_name, provider=MODEL_REGISTRY[model_name])

    raise ValueError("No available model can satisfy this request.")
