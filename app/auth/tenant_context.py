from pydantic import BaseModel


class TenantContext(BaseModel):
    tenant_id: str
    name: str
    allowed_models: list[str]
    rpm_limit: int = 60
    tpm_limit: int = 20_000
