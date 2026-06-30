from time import perf_counter
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.audit.audit_logger import audit_store, usage_store
from app.auth.api_key_auth import authenticate_tenant
from app.auth.tenant_context import TenantContext
from app.budgets.cost_calculator import estimate_cost_usd
from app.evals.validators import run_basic_evals
from app.routing.model_router import route_model
from app.schemas.chat import ChatCompletionRequest, ChatCompletionResponse, ChatMessage, Usage
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
    selected = route_model(request, tenant)
    started = perf_counter()
    provider_response = selected.provider.complete(request, masked.text)
    latency_ms = int((perf_counter() - started) * 1000)

    usage = Usage(
        input_tokens=provider_response.input_tokens,
        output_tokens=provider_response.output_tokens,
        cost_usd=estimate_cost_usd(
            selected.model_name,
            provider_response.input_tokens,
            provider_response.output_tokens,
        ),
    )
    evals = run_basic_evals(provider_response.content, request.task_type)

    usage_store.add(
        tenant_id=tenant.tenant_id,
        request_id=request_id,
        model_used=selected.model_name,
        usage=usage,
        latency_ms=latency_ms,
        status="success",
    )
    audit_store.add(
        tenant_id=tenant.tenant_id,
        request_id=request_id,
        model_used=selected.model_name,
        redacted_prompt=masked.text,
        pii_masked_count=masked.masked_count,
        fallback_used=False,
        metadata=request.metadata,
    )

    return ChatCompletionResponse(
        request_id=request_id,
        model_used=selected.model_name,
        fallback_used=False,
        usage=usage,
        evals=evals,
        response=ChatMessage(role="assistant", content=provider_response.content),
    )
