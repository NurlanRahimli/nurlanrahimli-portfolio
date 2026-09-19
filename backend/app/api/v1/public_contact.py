from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.contact import PublicContactContentRead
from app.services.contact import get_contact_content

router = APIRouter(
    prefix="/public/contact",
    tags=["public-contact"],
)


@router.get(
    "",
    response_model=PublicContactContentRead | None,
)
def get_public_contact(
    db: Annotated[Session, Depends(get_db)],
) -> PublicContactContentRead | None:
    contact = get_contact_content(db)

    if contact is None:
        return None

    return PublicContactContentRead(
        projects_built=contact.projects_built,
        email=contact.email,
        phone_number=contact.phone_number,
    )
