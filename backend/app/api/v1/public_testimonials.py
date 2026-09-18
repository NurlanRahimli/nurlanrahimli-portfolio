from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.projects import media_urls
from app.db.deps import get_db
from app.models import Testimonial
from app.schemas.testimonial import (
    PublicTestimonialList,
    PublicTestimonialRead,
)
from app.services.testimonials import list_active_testimonials

router = APIRouter(
    prefix="/public/testimonials",
    tags=["public-testimonials"],
)


def serialize_public_testimonial(
    testimonial: Testimonial,
) -> PublicTestimonialRead:
    profile_image_url, profile_thumbnail_url = media_urls(
        testimonial.profile_media_asset
    )

    return PublicTestimonialRead(
        person_name=testimonial.person_name,
        testimonial_text=testimonial.testimonial_text,
        profile_image_url=profile_image_url,
        profile_thumbnail_url=profile_thumbnail_url,
        linkedin_url=testimonial.linkedin_url,
    )


@router.get(
    "",
    response_model=PublicTestimonialList,
)
def get_public_testimonials(
    db: Annotated[Session, Depends(get_db)],
) -> PublicTestimonialList:
    testimonials = list(
        list_active_testimonials(
            db,
            limit=3,
        )
    )

    return PublicTestimonialList(
        items=[
            serialize_public_testimonial(testimonial) for testimonial in testimonials
        ],
        total=len(testimonials),
    )
