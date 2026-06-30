from pydantic import BaseModel

from app.auth.tenant_context import TenantContext
from app.providers.base import LLMProvider
from app.providers.mock_provider import MockProvider
from app.schemas.chat import ChatCompletionRequest


class RoutedModel(BaseModel):
    model_name: str
    provider: LLMProvider

    model_config = {"arbitrary_types_allowed": True}


MODEL_REGISTRY = {
    "mock-fast": MockProvider("mock-fast"),
    "mock-quality": MockProvider("mock-quality"),
}


def available_models() -> list[dict[str, str]]:
    return [
        {"id": "mock-fast", "provider": "mock", "description": "Low-cost demo model"},
        {"id": "mock-quality", "provider": "mock", "description": "Higher-quality demo model"},
    ]


def route_model(request: ChatCompletionRequest, tenant: TenantContext) -> RoutedModel:
    requested_model = request.model
    if requested_model and requested_model != "auto" and requested_model in tenant.allowed_models:
        return RoutedModel(model_name=requested_model, provider=MODEL_REGISTRY[requested_model])

    if (
        request.task_type in {"reasoning", "code_generation"}
        and "mock-quality" in tenant.allowed_models
    ):
        return RoutedModel(model_name="mock-quality", provider=MODEL_REGISTRY["mock-quality"])

    default_model = tenant.allowed_models[0]
    return RoutedModel(model_name=default_model, provider=MODEL_REGISTRY[default_model])
