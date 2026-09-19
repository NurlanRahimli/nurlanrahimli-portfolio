from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.contact import ContactContent
from app.schemas.contact import ContactContentUpdate


def get_contact_content(db: Session) -> ContactContent | None:
    statement = select(ContactContent).where(ContactContent.id == 1)
    return db.scalar(statement)


def update_contact_content(
    db: Session,
    *,
    payload: ContactContentUpdate,
) -> ContactContent:
    contact = get_contact_content(db)

    if contact is None:
        contact = ContactContent(
            id=1,
            projects_built=payload.projects_built,
            email=str(payload.email),
            phone_number=payload.phone_number,
        )
        db.add(contact)
    else:
        contact.projects_built = payload.projects_built
        contact.email = str(payload.email)
        contact.phone_number = payload.phone_number

    db.commit()
    db.refresh(contact)
    return contact
