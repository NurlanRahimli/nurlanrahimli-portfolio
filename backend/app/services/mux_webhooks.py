from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ProjectVideo

SUPPORTED_MUX_VIDEO_EVENTS = {
    "video.upload.asset_created",
    "video.upload.errored",
    "video.asset.ready",
    "video.asset.errored",
}


def _string_value(
    value: object,
) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _float_value(
    value: object,
) -> float | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, int | float):
        return float(value)

    return None


def _extract_playback_id(
    data: dict[str, Any],
) -> str | None:
    playback_ids = data.get("playback_ids")

    if not isinstance(playback_ids, list):
        return None

    for playback in playback_ids:
        if not isinstance(playback, dict):
            continue

        playback_id = _string_value(playback.get("id"))
        if playback_id is not None:
            return playback_id

    return None


def _extract_error_message(
    data: dict[str, Any],
) -> str | None:
    errors = data.get("errors")

    if isinstance(errors, dict):
        messages = errors.get("messages")

        if isinstance(messages, list):
            normalized = [
                str(message).strip() for message in messages if str(message).strip()
            ]
            if normalized:
                return "; ".join(normalized)

        message = _string_value(errors.get("message"))
        if message is not None:
            return message

    error = data.get("error")

    if isinstance(error, dict):
        messages = error.get("messages")

        if isinstance(messages, list):
            normalized = [
                str(message).strip() for message in messages if str(message).strip()
            ]
            if normalized:
                return "; ".join(normalized)

        message = _string_value(error.get("message"))
        if message is not None:
            return message

    message = _string_value(data.get("message"))
    if message is not None:
        return message

    return None


def _video_by_upload_id(
    db: Session,
    upload_id: str,
) -> ProjectVideo | None:
    return db.scalar(
        select(ProjectVideo).where(ProjectVideo.mux_upload_id == upload_id)
    )


def _video_by_asset_id(
    db: Session,
    asset_id: str,
) -> ProjectVideo | None:
    return db.scalar(select(ProjectVideo).where(ProjectVideo.mux_asset_id == asset_id))


def _handle_upload_asset_created(
    db: Session,
    data: dict[str, Any],
) -> bool:
    upload_id = _string_value(data.get("id"))
    asset_id = _string_value(data.get("asset_id"))

    if upload_id is None or asset_id is None:
        return False

    video = _video_by_upload_id(
        db,
        upload_id,
    )
    if video is None:
        return False

    # Never regress a video that has already reached ready.
    if video.status == "ready":
        return True

    video.mux_asset_id = asset_id
    video.status = "processing"
    video.error_message = None

    db.commit()
    return True


def _handle_upload_errored(
    db: Session,
    data: dict[str, Any],
) -> bool:
    upload_id = _string_value(data.get("id"))

    if upload_id is None:
        return False

    video = _video_by_upload_id(
        db,
        upload_id,
    )
    if video is None:
        return False

    if video.status == "ready":
        return True

    video.status = "error"
    video.error_message = (
        _extract_error_message(data) or "Mux could not process the video upload."
    )

    db.commit()
    return True


def _handle_asset_ready(
    db: Session,
    data: dict[str, Any],
) -> bool:
    asset_id = _string_value(data.get("id"))

    if asset_id is None:
        return False

    video = _video_by_asset_id(
        db,
        asset_id,
    )
    if video is None:
        return False

    video.status = "ready"

    playback_id = _extract_playback_id(data)
    if playback_id is not None:
        video.mux_playback_id = playback_id

    duration = _float_value(data.get("duration"))
    if duration is not None:
        video.duration_seconds = duration

    aspect_ratio = _string_value(data.get("aspect_ratio"))
    if aspect_ratio is not None:
        video.aspect_ratio = aspect_ratio

    video.error_message = None

    db.commit()
    return True


def _handle_asset_errored(
    db: Session,
    data: dict[str, Any],
) -> bool:
    asset_id = _string_value(data.get("id"))

    if asset_id is None:
        return False

    video = _video_by_asset_id(
        db,
        asset_id,
    )
    if video is None:
        return False

    # Duplicate/out-of-order failure events must never make
    # a successfully ready asset unusable again.
    if video.status == "ready":
        return True

    video.status = "error"
    video.error_message = (
        _extract_error_message(data) or "Mux could not process the video asset."
    )

    db.commit()
    return True


def process_mux_video_event(
    db: Session,
    payload: dict[str, Any],
) -> bool:
    event_type = _string_value(payload.get("type"))
    data = payload.get("data")

    if event_type not in SUPPORTED_MUX_VIDEO_EVENTS or not isinstance(data, dict):
        return False

    if event_type == "video.upload.asset_created":
        return _handle_upload_asset_created(
            db,
            data,
        )

    if event_type == "video.upload.errored":
        return _handle_upload_errored(
            db,
            data,
        )

    if event_type == "video.asset.ready":
        return _handle_asset_ready(
            db,
            data,
        )

    if event_type == "video.asset.errored":
        return _handle_asset_errored(
            db,
            data,
        )

    return False
