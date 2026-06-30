from fastapi import APIRouter

from app.routing.model_router import available_models

router = APIRouter(prefix="/v1", tags=["models"])


@router.get("/models")
def list_models() -> dict[str, list[dict[str, str]]]:
    return {"data": available_models()}
