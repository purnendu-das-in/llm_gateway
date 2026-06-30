from pydantic import BaseModel


class TenantContext(BaseModel):
    tenant_id: str
    name: str
    allowed_models: list[str]
