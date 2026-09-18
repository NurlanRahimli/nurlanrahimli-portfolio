import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.deps import get_db
from app.services.mux_signature import (
    MuxWebhookSignatureError,
    verify_mux_webhook_signature,
)
from app.services.mux_webhooks import process_mux_video_event

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)


def parse_mux_webhook_payload(
    raw_body: bytes,
) -> dict[str, Any]:
    try:
        payload = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("Mux webhook body is not valid JSON.") from exc

    if not isinstance(payload, dict):
        raise ValueError("Mux webhook body must be a JSON object.")

    return payload


@router.post("/mux")
async def mux_webhook(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, bool]:
    secret = settings.mux_webhook_secret.strip()

    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mux webhook signing secret is not configured.",
        )

    signature = request.headers.get(
        "mux-signature",
        "",
    )

    raw_body = await request.body()

    try:
        verify_mux_webhook_signature(
            raw_body,
            signature,
            secret,
        )
    except MuxWebhookSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    try:
        payload = parse_mux_webhook_payload(raw_body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    handled = process_mux_video_event(
        db,
        payload,
    )

    return {
        "received": True,
        "handled": handled,
    }
