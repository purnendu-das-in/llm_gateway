# Tenant Budgets

The gateway supports tenant-level monetary budgets in addition to RPM and TPM limits.

Budget settings include:

- `monthly_budget_usd`
- `daily_budget_usd`
- `warning_threshold`
- `hard_stop_threshold`
- `budget_reset_day`
- `budget_override`
- `model_spending_limits_usd`

The current implementation keeps budget configuration in memory, matching the rest of the MVP
stores. The service boundary is intentionally separate from FastAPI routes so a Postgres-backed
budget repository can replace the in-memory store later.

## Enforcement

The chat API checks the tenant budget before calling a provider. If daily or monthly spend has
already crossed the hard-stop threshold, the request returns `402 Payment Required` with
`tenant_budget_exceeded`.

Per-model limits are checked while selecting provider candidates. If the selected model has
exhausted its cap, fallback can continue to the next allowed model.

Budget overrides bypass hard stops until disabled or until their optional `expires_at` timestamp
passes.

## Status

Tenants can inspect their own budget state with:

```http
GET /v1/tenant/budget
```

Admins can configure and inspect tenant budgets with:

```http
PUT /v1/admin/tenants/{tenant_id}/budget
GET /v1/admin/tenants/{tenant_id}/budget
GET /v1/admin/tenants/{tenant_id}/usage
```
