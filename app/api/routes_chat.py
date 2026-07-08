from time import perf_counter, time
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.audit.audit_logger import audit_store, usage_store
from app.auth.api_key_auth import authenticate_tenant
from app.auth.tenant_context import TenantContext
from app.budgets.budget_service import check_budget_for_request
from app.budgets.cost_calculator import estimate_cost_usd
from app.evals.validators import run_basic_evals
from app.observability.metrics import gateway_metrics
from app.providers.base import ProviderError, ProviderResponse
from app.resilience.circuit_breaker import circuit_breaker
from app.resilience.rate_limiter import token_rate_limiter
from app.routing.model_router import estimate_tokens, fallback_candidates, route_model
from app.schemas.chat import (
    ChatChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    Usage,
)
from app.security.pii_masker import mask_pii
from app.security.prompt_validator import validate_prompt

router = APIRouter(prefix="/v1/chat", tags=["chat"])


@router.post("/completions")
def create_chat_completion(
    request: ChatCompletionRequest,
    tenant: Annotated[TenantContext, Depends(authenticate_tenant)],
) -> ChatCompletionResponse:
    request_id = f"req_{uuid4().hex[:12]}"
    prompt = request.combined_prompt()
    validation = validate_prompt(prompt, request.task_type)
    if not validation.allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "prompt_validation_failed", "reason": validation.reason},
        )

    masked = mask_pii(prompt)
    rate_limit = token_rate_limiter.check_and_consume(
        tenant_id=tenant.tenant_id,
        estimated_tokens=estimate_tokens(masked.text),
        rpm_limit=tenant.rpm_limit,
        tpm_limit=tenant.tpm_limit,
    )
    if not rate_limit.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "rate_limit_exceeded", "reason": rate_limit.reason},
            headers={"Retry-After": str(rate_limit.retry_after_seconds)},
        )

    try:
        selected = route_model(request, tenant)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"error": "context_window_exceeded", "reason": str(exc)},
        ) from exc
    budget_decision = check_budget_for_request(tenant.tenant_id)
    if not budget_decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"error": budget_decision.error, "reason": budget_decision.reason},
        )

    started = perf_counter()
    provider_response, model_used, fallback_used = _complete_with_fallbacks(
        request=request,
        tenant=tenant,
        sanitized_prompt=masked.text,
        selected_model=selected.model_name,
    )
    latency_ms = int((perf_counter() - started) * 1000)

    usage = Usage(
        input_tokens=provider_response.input_tokens,
        output_tokens=provider_response.output_tokens,
        prompt_tokens=provider_response.input_tokens,
        completion_tokens=provider_response.output_tokens,
        total_tokens=provider_response.input_tokens + provider_response.output_tokens,
        cost_usd=estimate_cost_usd(
            model_used,
            provider_response.input_tokens,
            provider_response.output_tokens,
        ),
    )
    evals = run_basic_evals(provider_response.content, request.task_type)
    status_label = "fallback" if fallback_used else "success"
    gateway_metrics.record_request(tenant.tenant_id, model_used, status_label)
    gateway_metrics.record_tokens(tenant.tenant_id, usage.input_tokens, usage.output_tokens)
    gateway_metrics.record_latency(model_used, latency_ms)

    usage_store.add(
        tenant_id=tenant.tenant_id,
        request_id=request_id,
        model_used=model_used,
        usage=usage,
        latency_ms=latency_ms,
        status="success",
    )
    audit_store.add(
        tenant_id=tenant.tenant_id,
        request_id=request_id,
        model_used=model_used,
        redacted_prompt=masked.text,
        pii_masked_count=masked.masked_count,
        fallback_used=fallback_used,
        metadata=request.metadata,
    )

    assistant_message = ChatMessage(role="assistant", content=provider_response.content)
    return ChatCompletionResponse(
        id=request_id,
        created=int(time()),
        model=model_used,
        choices=[ChatChoice(message=assistant_message)],
        request_id=request_id,
        model_used=model_used,
        fallback_used=fallback_used,
        usage=usage,
        evals=evals,
        response=assistant_message,
    )


def _complete_with_fallbacks(
    request: ChatCompletionRequest,
    tenant: TenantContext,
    sanitized_prompt: str,
    selected_model: str,
) -> tuple[ProviderResponse, str, bool]:
    last_error: ProviderError | None = None
    last_budget_error: str | None = None
    for candidate in fallback_candidates(selected_model, tenant):
        budget_decision = check_budget_for_request(tenant.tenant_id, candidate.model_name)
        if not budget_decision.allowed:
            if budget_decision.error == "tenant_budget_exceeded":
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={"error": budget_decision.error, "reason": budget_decision.reason},
                )
            last_budget_error = budget_decision.reason
            continue

        try:
            response = candidate.provider.complete(request, sanitized_prompt)
        except ProviderError as exc:
            last_error = exc
            circuit_breaker.record_failure(candidate.model_name)
            gateway_metrics.record_provider_error(candidate.model_name, exc.status_code)
            continue

        circuit_breaker.record_success(candidate.model_name)
        return response, candidate.model_name, candidate.model_name != selected_model

    if last_budget_error is not None and last_error is None:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"error": "model_budget_exceeded", "reason": last_budget_error},
        )

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "error": "all_providers_unavailable",
            "reason": str(last_error) if last_error else "No healthy fallback providers remain.",
        },
    )
