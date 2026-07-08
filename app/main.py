from fastapi import FastAPI

from app.api.routes_admin import router as admin_router
from app.api.routes_chat import router as chat_router
from app.api.routes_health import router as health_router
from app.api.routes_metrics import router as metrics_router
from app.api.routes_models import router as models_router
from app.api.routes_usage import router as usage_router

app = FastAPI(
    title="llm_gateway",
    description="Production-style AI gateway for multi-tenant LLM applications.",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(models_router)
app.include_router(usage_router)
app.include_router(admin_router)
app.include_router(chat_router)
