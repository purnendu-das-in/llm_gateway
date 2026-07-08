from fastapi.testclient import TestClient

from app.audit.audit_logger import audit_store, usage_store
from app.budgets.budget_store import budget_store
from app.main import app
from app.observability.metrics import gateway_metrics
from app.resilience.circuit_breaker import circuit_breaker
from app.resilience.rate_limiter import token_rate_limiter

client = TestClient(app)


def setup_function() -> None:
    usage_store.clear()
    audit_store.clear()
    circuit_breaker.clear()
    token_rate_limiter.clear()
    gateway_metrics.clear()
    budget_store.clear()


def test_tenant_budget_status_reports_warning_after_spend_crosses_threshold() -> None:
    update = client.put(
        "/v1/admin/tenants/acme-insurance/budget",
        headers={"Authorization": "Bearer demo-key-admin"},
        json={
            "monthly_budget_usd": 0.000003,
            "daily_budget_usd": 0.000003,
            "warning_threshold": 0.5,
        },
    )
    assert update.status_code == 200

    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer demo-key-acme"},
        json={
            "model": "auto",
            "messages": [{"role": "user", "content": "Hello gateway"}],
        },
    )
    assert response.status_code == 200

    budget = client.get("/v1/tenant/budget", headers={"Authorization": "Bearer demo-key-acme"})
    body = budget.json()
    assert budget.status_code == 200
    assert body["tenant_id"] == "acme-insurance"
    assert body["warning_threshold_crossed"] is True
    assert body["requests_allowed"] is True


def test_tenant_budget_hard_stop_blocks_next_request() -> None:
    client.put(
        "/v1/admin/tenants/acme-insurance/budget",
        headers={"Authorization": "Bearer demo-key-admin"},
        json={
            "monthly_budget_usd": 0.000001,
            "daily_budget_usd": 0.000001,
        },
    )
    first = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer demo-key-acme"},
        json={
            "model": "auto",
            "messages": [{"role": "user", "content": "Hello gateway"}],
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer demo-key-acme"},
        json={
            "model": "auto",
            "messages": [{"role": "user", "content": "Hello again"}],
        },
    )

    assert second.status_code == 402
    assert second.json()["detail"]["error"] == "tenant_budget_exceeded"


def test_budget_override_allows_requests_after_hard_stop() -> None:
    client.put(
        "/v1/admin/tenants/acme-insurance/budget",
        headers={"Authorization": "Bearer demo-key-admin"},
        json={"monthly_budget_usd": 0.000001},
    )
    first = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer demo-key-acme"},
        json={
            "model": "auto",
            "messages": [{"role": "user", "content": "Hello gateway"}],
        },
    )
    assert first.status_code == 200

    client.put(
        "/v1/admin/tenants/acme-insurance/budget",
        headers={"Authorization": "Bearer demo-key-admin"},
        json={"budget_override": {"enabled": True, "reason": "approved incident response"}},
    )
    second = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer demo-key-acme"},
        json={
            "model": "auto",
            "messages": [{"role": "user", "content": "Hello again"}],
        },
    )

    assert second.status_code == 200
    budget = client.get("/v1/tenant/budget", headers={"Authorization": "Bearer demo-key-acme"})
    assert budget.json()["override_active"] is True


def test_model_spending_limit_routes_to_fallback_model() -> None:
    client.put(
        "/v1/admin/tenants/acme-insurance/budget",
        headers={"Authorization": "Bearer demo-key-admin"},
        json={"model_spending_limits_usd": {"mock-fast": 0.0}},
    )

    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer demo-key-acme"},
        json={
            "model": "mock-fast",
            "messages": [{"role": "user", "content": "Summarize this renewal note."}],
        },
    )

    assert response.status_code == 200
    assert response.json()["model_used"] == "mock-quality"
    assert response.json()["fallback_used"] is True


def test_admin_usage_endpoint_requires_admin_key() -> None:
    forbidden = client.get(
        "/v1/admin/tenants/acme-insurance/usage",
        headers={"Authorization": "Bearer demo-key-acme"},
    )
    assert forbidden.status_code == 403

    allowed = client.get(
        "/v1/admin/tenants/acme-insurance/usage",
        headers={"Authorization": "Bearer demo-key-admin"},
    )
    assert allowed.status_code == 200
    assert allowed.json()["tenant_id"] == "acme-insurance"
