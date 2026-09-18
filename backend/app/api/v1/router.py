from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.media import router as media_router
from app.api.v1.mux_webhooks import router as mux_webhooks_router
from app.api.v1.projects import router as projects_router
from app.api.v1.public_projects import router as public_projects_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(media_router)
api_router.include_router(mux_webhooks_router)
api_router.include_router(projects_router)
api_router.include_router(public_projects_router)
