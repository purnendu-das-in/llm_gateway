from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.tenant_context import TenantContext

security = HTTPBearer(auto_error=False)
ADMIN_API_KEYS = {"demo-key-admin"}

DEMO_TENANTS = {
    "demo-key-acme": TenantContext(
        tenant_id="acme-insurance",
        name="Acme Insurance",
        allowed_models=["mock-fast", "mock-quality", "mock-long-context"],
        rpm_limit=120,
        tpm_limit=50_000,
    ),
    "demo-key-globex": TenantContext(
        tenant_id="globex-finance",
        name="Globex Finance",
        allowed_models=["mock-fast"],
        rpm_limit=30,
        tpm_limit=5_000,
    ),
}


def authenticate_tenant(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> TenantContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "missing_api_key", "message": "Bearer API key is required."},
        )

    tenant = DEMO_TENANTS.get(credentials.credentials)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_api_key", "message": "API key is not recognized."},
        )
    return tenant


def authenticate_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "missing_api_key", "message": "Bearer admin API key is required."},
        )

    if credentials.credentials not in ADMIN_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "Admin API key is required."},
        )
    return "admin"
