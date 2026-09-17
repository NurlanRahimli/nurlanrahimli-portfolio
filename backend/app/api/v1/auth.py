from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentAdmin, DatabaseSession
from app.core.security import create_access_token, verify_password
from app.models import AdminUser
from app.schemas import AdminUserRead, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: DatabaseSession,
) -> TokenResponse:
    email = str(credentials.email).strip().lower()

    admin = db.scalar(select(AdminUser).where(AdminUser.email == email))

    if admin is None or not verify_password(
        credentials.password,
        admin.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive",
        )

    admin.last_login_at = datetime.now(UTC)
    db.commit()

    return TokenResponse(
        access_token=create_access_token(str(admin.id)),
    )


@router.get("/me", response_model=AdminUserRead)
def get_me(
    current_admin: CurrentAdmin,
) -> AdminUser:
    return current_admin
