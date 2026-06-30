from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.chat import Usage


class UsageRecord(BaseModel):
    tenant_id: str
    request_id: str
    model_used: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    status: str
    created_at: datetime


class AuditRecord(BaseModel):
    tenant_id: str
    request_id: str
    model_used: str
    redacted_prompt: str
    pii_masked_count: int
    fallback_used: bool
    metadata: dict[str, Any]
    created_at: datetime


class InMemoryUsageStore:
    def __init__(self) -> None:
        self._records: list[UsageRecord] = []

    def add(
        self,
        tenant_id: str,
        request_id: str,
        model_used: str,
        usage: Usage,
        latency_ms: int,
        status: str,
    ) -> None:
        self._records.append(
            UsageRecord(
                tenant_id=tenant_id,
                request_id=request_id,
                model_used=model_used,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cost_usd=usage.cost_usd,
                latency_ms=latency_ms,
                status=status,
                created_at=datetime.now(UTC),
            )
        )

    def for_tenant(self, tenant_id: str) -> list[dict[str, Any]]:
        return [
            record.model_dump(mode="json")
            for record in self._records
            if record.tenant_id == tenant_id
        ]

    def count_for_tenant(self, tenant_id: str) -> int:
        return len(self.for_tenant(tenant_id))

    def cost_for_tenant(self, tenant_id: str) -> float:
        return round(
            sum(record.cost_usd for record in self._records if record.tenant_id == tenant_id),
            6,
        )

    def clear(self) -> None:
        self._records.clear()


class InMemoryAuditStore:
    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def add(
        self,
        tenant_id: str,
        request_id: str,
        model_used: str,
        redacted_prompt: str,
        pii_masked_count: int,
        fallback_used: bool,
        metadata: dict[str, Any],
    ) -> None:
        self._records.append(
            AuditRecord(
                tenant_id=tenant_id,
                request_id=request_id,
                model_used=model_used,
                redacted_prompt=redacted_prompt,
                pii_masked_count=pii_masked_count,
                fallback_used=fallback_used,
                metadata=metadata,
                created_at=datetime.now(UTC),
            )
        )

    def clear(self) -> None:
        self._records.clear()


usage_store = InMemoryUsageStore()
audit_store = InMemoryAuditStore()
