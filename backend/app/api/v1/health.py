from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.deps import get_db

router = APIRouter(tags=["Health"])

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/health")
def health_check(
    db: DatabaseSession,
) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    return {
        "status": "ok",
        "database": "ok",
    }
