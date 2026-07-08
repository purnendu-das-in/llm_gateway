from typing import Annotated

from fastapi import APIRouter, Depends

from app.audit.audit_logger import usage_store
from app.auth.api_key_auth import authenticate_tenant
from app.auth.tenant_context import TenantContext
from app.budgets.budget_service import budget_status_for_tenant

router = APIRouter(prefix="/v1/tenant", tags=["usage"])


@router.get("/usage")
def get_tenant_usage(
    tenant: Annotated[TenantContext, Depends(authenticate_tenant)],
) -> dict[str, object]:
    return {
        "tenant_id": tenant.tenant_id,
        "request_count": usage_store.count_for_tenant(tenant.tenant_id),
        "total_cost_usd": usage_store.cost_for_tenant(tenant.tenant_id),
        "requests": usage_store.for_tenant(tenant.tenant_id),
    }


@router.get("/budget")
def get_tenant_budget(
    tenant: Annotated[TenantContext, Depends(authenticate_tenant)],
) -> dict[str, object]:
    return budget_status_for_tenant(tenant.tenant_id).model_dump(mode="json")
