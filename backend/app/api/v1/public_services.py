from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.service import PublicServiceList, PublicServiceRead
from app.services.services import list_active_services


router = APIRouter(
    prefix="/public/services",
    tags=["public-services"],
)


@router.get("", response_model=PublicServiceList)
def get_public_services(
    db: Annotated[Session, Depends(get_db)],
) -> PublicServiceList:
    services = list(list_active_services(db))

    return PublicServiceList(
        items=[
            PublicServiceRead(
                icon=service.icon,
                title=service.title,
                description=service.description,
            )
            for service in services
        ],
        total=len(services),
    )
