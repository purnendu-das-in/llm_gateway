from datetime import UTC, datetime, timedelta

from app.audit.audit_logger import usage_store
from app.budgets.budget_store import BudgetDecision, BudgetStatus, TenantBudget, budget_store


def budget_status_for_tenant(tenant_id: str) -> BudgetStatus:
    budget = budget_store.get(tenant_id)
    now = datetime.now(UTC)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = _monthly_budget_start(budget, now)
    budget_reset_at = _next_monthly_budget_reset(budget, now)

    daily_spend = usage_store.cost_for_tenant(tenant_id, start_at=day_start)
    monthly_spend = usage_store.cost_for_tenant(tenant_id, start_at=month_start)
    model_spend = usage_store.cost_by_model_for_tenant(tenant_id, start_at=month_start)
    override_active = budget.budget_override.is_active(now)

    tenant_hard_stop = (
        _threshold_crossed(daily_spend, budget.daily_budget_usd, budget.hard_stop_threshold)
        or _threshold_crossed(monthly_spend, budget.monthly_budget_usd, budget.hard_stop_threshold)
    )
    models_blocked = [
        model_name
        for model_name, limit in budget.model_spending_limits_usd.items()
        if model_spend.get(model_name, 0) >= limit
    ]
    hard_stop_crossed = tenant_hard_stop or bool(models_blocked)
    warning_crossed = (
        _threshold_crossed(daily_spend, budget.daily_budget_usd, budget.warning_threshold)
        or _threshold_crossed(monthly_spend, budget.monthly_budget_usd, budget.warning_threshold)
        or any(
            model_spend.get(model_name, 0) >= limit * budget.warning_threshold
            for model_name, limit in budget.model_spending_limits_usd.items()
        )
    )
    requests_allowed = override_active or not tenant_hard_stop
    reason = None
    if tenant_hard_stop and not override_active:
        reason = "tenant_budget_exceeded"

    return BudgetStatus(
        tenant_id=tenant_id,
        daily_budget_usd=budget.daily_budget_usd,
        monthly_budget_usd=budget.monthly_budget_usd,
        current_daily_spend_usd=daily_spend,
        current_monthly_spend_usd=monthly_spend,
        daily_consumption_pct=_consumption_pct(daily_spend, budget.daily_budget_usd),
        monthly_consumption_pct=_consumption_pct(monthly_spend, budget.monthly_budget_usd),
        warning_threshold_crossed=warning_crossed,
        hard_stop_threshold_crossed=hard_stop_crossed,
        requests_allowed=requests_allowed,
        reason=reason,
        budget_reset_at=budget_reset_at,
        override_active=override_active,
        model_spend_usd=model_spend,
        model_spending_limits_usd=budget.model_spending_limits_usd,
        models_blocked=models_blocked,
    )


def check_budget_for_request(tenant_id: str, model_name: str | None = None) -> BudgetDecision:
    budget = budget_store.get(tenant_id)
    status = budget_status_for_tenant(tenant_id)
    if status.override_active:
        return BudgetDecision(allowed=True)

    if not status.requests_allowed:
        return BudgetDecision(
            allowed=False,
            error="tenant_budget_exceeded",
            reason="Tenant has reached its configured daily or monthly budget.",
        )

    if model_name is not None:
        limit = budget.model_spending_limits_usd.get(model_name)
        model_spend = status.model_spend_usd.get(model_name, 0)
        if limit is not None and model_spend >= limit:
            return BudgetDecision(
                allowed=False,
                error="model_budget_exceeded",
                reason=f"Model {model_name} has reached its tenant spending limit.",
            )

    return BudgetDecision(allowed=True)


def _threshold_crossed(spend: float, limit: float | None, threshold: float) -> bool:
    return limit is not None and spend >= limit * threshold


def _consumption_pct(spend: float, limit: float | None) -> float | None:
    if limit is None or limit == 0:
        return None
    return round((spend / limit) * 100, 2)


def _monthly_budget_start(budget: TenantBudget, now: datetime) -> datetime:
    reset_this_month = now.replace(
        day=budget.budget_reset_day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    if now >= reset_this_month:
        return reset_this_month

    previous_month_last_day = reset_this_month.replace(day=1) - timedelta(days=1)
    return previous_month_last_day.replace(
        day=budget.budget_reset_day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def _next_monthly_budget_reset(budget: TenantBudget, now: datetime) -> datetime:
    reset_this_month = now.replace(
        day=budget.budget_reset_day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    if now < reset_this_month:
        return reset_this_month

    first_next_month = reset_this_month.replace(day=28) + timedelta(days=4)
    return first_next_month.replace(
        day=budget.budget_reset_day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
