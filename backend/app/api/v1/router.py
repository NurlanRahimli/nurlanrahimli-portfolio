from app.api.v1.experiences import router as experiences_router
from app.api.v1.educations import router as educations_router
from app.api.v1.public_experiences import router as public_experiences_router
from app.api.v1.public_educations import router as public_educations_router
from app.api.v1.contact import router as contact_router
from app.api.v1.public_contact import router as public_contact_router
from app.api.v1.services import router as services_router
from app.api.v1.skills import router as skills_router
from app.api.v1.public_services import router as public_services_router
from app.api.v1.public_skills import router as public_skills_router
from app.api.v1.about import router as about_router
from app.api.v1.public_about import router as public_about_router
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.media import router as media_router
from app.api.v1.mux_webhooks import router as mux_webhooks_router
from app.api.v1.projects import router as projects_router
from app.api.v1.public_projects import router as public_projects_router
from app.api.v1.public_testimonials import router as public_testimonials_router
from app.api.v1.testimonials import router as testimonials_router

api_router = APIRouter()
api_router.include_router(about_router)
api_router.include_router(public_about_router)
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(media_router)
api_router.include_router(mux_webhooks_router)
api_router.include_router(projects_router)
api_router.include_router(public_projects_router)
api_router.include_router(testimonials_router)
api_router.include_router(public_testimonials_router)
api_router.include_router(services_router)
api_router.include_router(skills_router)
api_router.include_router(public_services_router)
api_router.include_router(public_skills_router)

api_router.include_router(contact_router)
api_router.include_router(public_contact_router)

api_router.include_router(experiences_router)
api_router.include_router(educations_router)
api_router.include_router(public_experiences_router)
api_router.include_router(public_educations_router)
