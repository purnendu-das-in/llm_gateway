from datetime import UTC, datetime, timedelta

from pydantic import BaseModel


class RateLimitDecision(BaseModel):
    allowed: bool
    reason: str | None = None
    retry_after_seconds: int = 0


class UsageWindow(BaseModel):
    started_at: datetime
    request_count: int = 0
    token_count: int = 0


class InMemoryTokenRateLimiter:
    def __init__(self, window_seconds: int = 60) -> None:
        self.window = timedelta(seconds=window_seconds)
        self._windows: dict[str, UsageWindow] = {}

    def check_and_consume(
        self,
        tenant_id: str,
        estimated_tokens: int,
        rpm_limit: int,
        tpm_limit: int,
    ) -> RateLimitDecision:
        now = datetime.now(UTC)
        usage = self._windows.get(tenant_id)
        if usage is None or now - usage.started_at >= self.window:
            usage = UsageWindow(started_at=now)
            self._windows[tenant_id] = usage

        retry_after = max(1, int((usage.started_at + self.window - now).total_seconds()))
        if usage.request_count + 1 > rpm_limit:
            return RateLimitDecision(
                allowed=False,
                reason=f"RPM limit exceeded for tenant {tenant_id}.",
                retry_after_seconds=retry_after,
            )
        if usage.token_count + estimated_tokens > tpm_limit:
            return RateLimitDecision(
                allowed=False,
                reason=f"TPM limit exceeded for tenant {tenant_id}.",
                retry_after_seconds=retry_after,
            )

        usage.request_count += 1
        usage.token_count += estimated_tokens
        return RateLimitDecision(allowed=True)

    def clear(self) -> None:
        self._windows.clear()


token_rate_limiter = InMemoryTokenRateLimiter()
