# llm_gateway

A production-style AI gateway for enterprise GenAI applications.

`llm_gateway` demonstrates how to build a secure, multi-tenant, cost-aware, and observable gateway between client applications and multiple LLM providers. The first version runs entirely locally with a mock provider so the API, tests, and demo flow work without paid credentials.

## Why This Project?

Most GenAI applications start by calling an LLM provider directly. That works for prototypes, but production systems need:

- Tenant-level budgets
- Model routing
- Prompt validation
- PII masking
- Retries and fallbacks
- Audit logs
- Evals
- Cost and latency dashboards

This repo is structured to grow into that gateway layer while keeping the first milestone small and runnable.

## Current Features

- FastAPI backend
- `POST /v1/chat/completions`
- `GET /health`
- `GET /v1/models`
- `GET /v1/tenant/usage`
- API key authentication with demo tenant lookup
- OpenAI-compatible request shape
- Mock LLM provider
- Prompt validation for empty and risky prompts
- PII masking for emails, phone numbers, credit-card-like numbers, PAN-like IDs, and Aadhaar-like IDs
- Basic usage and audit logging in memory
- Pytest coverage for the gateway path

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open the API docs at `http://127.0.0.1:8000/docs`.

## Example Request

```powershell
$body = @{
  model = "auto"
  task_type = "summarization"
  messages = @(
    @{
      role = "user"
      content = "Summarize this customer email: rahul@example.com needs a renewal call at 9876543210."
    }
  )
  metadata = @{
    user_id = "demo-user"
    trace_id = "trace-local"
  }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/v1/chat/completions" `
  -Method Post `
  -Headers @{ Authorization = "Bearer demo-key-acme" } `
  -ContentType "application/json" `
  -Body $body
```

## Demo API Keys

| Tenant | API key |
| --- | --- |
| Acme Insurance | `demo-key-acme` |
| Globex Finance | `demo-key-globex` |

## Tests

```powershell
pytest
```

## What This Project Demonstrates

- Production GenAI architecture
- FastAPI backend development
- Multi-tenant SaaS design
- Prompt security and PII masking
- LLM routing foundation
- Audit and usage tracking
- Testable API design

## Roadmap

1. Persistent Postgres storage with SQLAlchemy and Alembic
2. Tenant budgets and cost enforcement
3. Multi-provider routing for OpenAI, Gemini, and Anthropic
4. Retry and fallback engine
5. Eval runners and reports
6. Streamlit dashboard
7. Docker, CI, and Cloud Run deployment guides
