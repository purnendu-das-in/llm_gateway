from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class BudgetOverride(BaseModel):
    enabled: bool = False
    expires_at: datetime | None = None
    reason: str | None = None

    def is_active(self, now: datetime | None = None) -> bool:
        if not self.enabled:
            return False
        checked_at = now or datetime.now(UTC)
        return self.expires_at is None or self.expires_at > checked_at


class TenantBudget(BaseModel):
    tenant_id: str
    monthly_budget_usd: float | None = Field(default=None, ge=0)
    daily_budget_usd: float | None = Field(default=None, ge=0)
    warning_threshold: float = Field(default=0.8, ge=0, le=1)
    hard_stop_threshold: float = Field(default=1.0, ge=0, le=1)
    budget_reset_day: int = Field(default=1, ge=1, le=28)
    budget_override: BudgetOverride = Field(default_factory=BudgetOverride)
    model_spending_limits_usd: dict[str, float] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def merge(self, patch: dict[str, Any]) -> "TenantBudget":
        data = self.model_dump()
        data.update({key: value for key, value in patch.items() if value is not None})
        data["updated_at"] = datetime.now(UTC)
        return TenantBudget(**data)


class BudgetDecision(BaseModel):
    allowed: bool
    error: str | None = None
    reason: str | None = None


class BudgetStatus(BaseModel):
    tenant_id: str
    daily_budget_usd: float | None
    monthly_budget_usd: float | None
    current_daily_spend_usd: float
    current_monthly_spend_usd: float
    daily_consumption_pct: float | None
    monthly_consumption_pct: float | None
    warning_threshold_crossed: bool
    hard_stop_threshold_crossed: bool
    requests_allowed: bool
    reason: str | None = None
    budget_reset_at: datetime
    override_active: bool
    model_spend_usd: dict[str, float]
    model_spending_limits_usd: dict[str, float]
    models_blocked: list[str]


class InMemoryBudgetStore:
    def __init__(self) -> None:
        self._budgets: dict[str, TenantBudget] = {}

    def get(self, tenant_id: str) -> TenantBudget:
        return self._budgets.get(tenant_id, TenantBudget(tenant_id=tenant_id))

    def upsert(self, tenant_id: str, patch: dict[str, Any]) -> TenantBudget:
        budget = self.get(tenant_id).merge({"tenant_id": tenant_id, **patch})
        self._budgets[tenant_id] = budget
        return budget

    def clear(self) -> None:
        self._budgets.clear()


budget_store = InMemoryBudgetStore()
