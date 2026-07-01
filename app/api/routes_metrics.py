from fastapi import APIRouter, Response

from app.observability.metrics import gateway_metrics
from app.resilience.circuit_breaker import circuit_breaker

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def metrics() -> Response:
    return Response(
        content=gateway_metrics.render_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.get("/health/circuits")
def circuit_health() -> dict[str, dict[str, object]]:
    return circuit_breaker.snapshot()
