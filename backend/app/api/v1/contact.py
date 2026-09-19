from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.deps import get_db
from app.models.admin_user import AdminUser
from app.schemas.contact import ContactContentRead, ContactContentUpdate
from app.services.contact import get_contact_content, update_contact_content

router = APIRouter(
    prefix="/contact",
    tags=["contact"],
)


@router.get(
    "",
    response_model=ContactContentRead | None,
)
def get_contact(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> ContactContent | None:
    del current_admin
    return get_contact_content(db)


@router.put(
    "",
    response_model=ContactContentRead,
)
def update_contact(
    payload: ContactContentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        AdminUser,
        Depends(get_current_admin),
    ],
) -> ContactContent:
    del current_admin
    return update_contact_content(
        db,
        payload=payload,
    )
