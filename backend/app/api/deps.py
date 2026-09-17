from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.deps import get_db
from app.models import AdminUser

bearer_scheme = HTTPBearer(auto_error=False)

DatabaseSession = Annotated[Session, Depends(get_db)]
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


def credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_admin(
    db: DatabaseSession,
    credentials: BearerCredentials,
) -> AdminUser:
    if credentials is None:
        raise credentials_exception()

    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")

        if not isinstance(subject, str):
            raise credentials_exception()

        admin_id = int(subject)
    except (jwt.InvalidTokenError, TypeError, ValueError) as exc:
        raise credentials_exception() from exc

    admin = db.get(AdminUser, admin_id)

    if admin is None or not admin.is_active:
        raise credentials_exception()

    return admin


CurrentAdmin = Annotated[AdminUser, Depends(get_current_admin)]
