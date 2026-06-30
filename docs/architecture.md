# Architecture

`llm_gateway` sits between client applications and LLM providers.

```text
Client App
    |
    v
FastAPI Gateway
    |
    +--> API key authentication
    +--> Tenant context
    +--> Prompt validation
    +--> PII masking
    +--> Model routing
    +--> Mock provider
    +--> Usage and audit logging
    |
    v
LLM Provider
```

The current implementation uses in-memory tenant, usage, and audit stores so the API is easy to run locally. The next milestone will replace those stores with Postgres-backed repositories.
