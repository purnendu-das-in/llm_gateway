from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.audit.audit_logger import usage_store
from app.auth.api_key_auth import authenticate_admin
from app.budgets.budget_service import budget_status_for_tenant
from app.budgets.budget_store import BudgetOverride, BudgetStatus, TenantBudget, budget_store

router = APIRouter(prefix="/v1/admin", tags=["admin"])


class TenantBudgetUpdate(BaseModel):
    monthly_budget_usd: float | None = Field(default=None, ge=0)
    daily_budget_usd: float | None = Field(default=None, ge=0)
    warning_threshold: float | None = Field(default=None, ge=0, le=1)
    hard_stop_threshold: float | None = Field(default=None, ge=0, le=1)
    budget_reset_day: int | None = Field(default=None, ge=1, le=28)
    budget_override: BudgetOverride | None = None
    model_spending_limits_usd: dict[str, float] | None = None


@router.put("/tenants/{tenant_id}/budget")
def update_tenant_budget(
    tenant_id: str,
    update: TenantBudgetUpdate,
    _: Annotated[str, Depends(authenticate_admin)],
) -> TenantBudget:
    return budget_store.upsert(
        tenant_id,
        update.model_dump(exclude_unset=True),
    )


@router.get("/tenants/{tenant_id}/budget")
def get_admin_tenant_budget(
    tenant_id: str,
    _: Annotated[str, Depends(authenticate_admin)],
) -> BudgetStatus:
    return budget_status_for_tenant(tenant_id)


@router.get("/tenants/{tenant_id}/usage")
def get_admin_tenant_usage(
    tenant_id: str,
    _: Annotated[str, Depends(authenticate_admin)],
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> dict[str, object]:
    records = usage_store.records_for_tenant(tenant_id, start_at=start_at, end_at=end_at)
    return {
        "tenant_id": tenant_id,
        "request_count": len(records),
        "total_cost_usd": usage_store.cost_for_tenant(
            tenant_id,
            start_at=start_at,
            end_at=end_at,
        ),
        "cost_by_model": usage_store.cost_by_model_for_tenant(
            tenant_id,
            start_at=start_at,
            end_at=end_at,
        ),
        "requests": [record.model_dump(mode="json") for record in records],
    }
