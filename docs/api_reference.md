# API Reference

## `GET /health`

Returns service health.

## `GET /v1/models`

Lists available demo models.

## `GET /v1/tenant/usage`

Returns usage records for the authenticated tenant.

Requires:

```http
Authorization: Bearer demo-key-acme
```

## `GET /v1/tenant/budget`

Returns budget consumption for the authenticated tenant, including daily/monthly spend,
warning and hard-stop state, reset date, override state, and per-model spend.

Requires:

```http
Authorization: Bearer demo-key-acme
```

## `PUT /v1/admin/tenants/{tenant_id}/budget`

Creates or updates a tenant budget. The local demo admin key is `demo-key-admin`.

Body:

```json
{
  "monthly_budget_usd": 100,
  "daily_budget_usd": 10,
  "warning_threshold": 0.8,
  "hard_stop_threshold": 1.0,
  "budget_reset_day": 1,
  "budget_override": {
    "enabled": false,
    "expires_at": null,
    "reason": null
  },
  "model_spending_limits_usd": {
    "mock-fast": 25
  }
}
```

## `GET /v1/admin/tenants/{tenant_id}/usage`

Returns tenant usage records, total cost, and cost by model. Supports optional
`start_at` and `end_at` query parameters as ISO datetimes.

Requires:

```http
Authorization: Bearer demo-key-admin
```

## `POST /v1/chat/completions`

Creates a mock chat completion through the gateway.

Requires:

```http
Authorization: Bearer demo-key-acme
Content-Type: application/json
```

Body:

```json
{
  "model": "auto",
  "task_type": "summarization",
  "messages": [
    {
      "role": "user",
      "content": "Summarize this text."
    }
  ],
  "metadata": {
    "user_id": "demo-user"
  }
}
```

Budget failures return:

```json
{
  "detail": {
    "error": "tenant_budget_exceeded",
    "reason": "Tenant has reached its configured daily or monthly budget."
  }
}
```
