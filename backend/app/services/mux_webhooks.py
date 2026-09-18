from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import ProjectVideo
from app.services.mux_video import (
    MuxAPIError,
    MuxConfigurationError,
    cleanup_project_video,
)


SUPPORTED_MUX_VIDEO_EVENTS = {
    "video.upload.asset_created",
    "video.upload.errored",
    "video.asset.ready",
    "video.asset.errored",
}


def _string_value(value: object) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _float_value(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _extract_playback_id(data: dict[str, Any]) -> str | None:
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


def _extract_error_message(data: dict[str, Any]) -> str | None:
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
) -> tuple[ProjectVideo | None, bool]:
    video = db.scalar(
        select(ProjectVideo).where(
            or_(
                ProjectVideo.mux_upload_id == upload_id,
                ProjectVideo.pending_mux_upload_id == upload_id,
            )
        )
    )
    if video is None:
        return None, False

    return video, video.pending_mux_upload_id == upload_id


def _video_by_asset_id(
    db: Session,
    asset_id: str,
) -> tuple[ProjectVideo | None, bool]:
    video = db.scalar(
        select(ProjectVideo).where(
            or_(
                ProjectVideo.mux_asset_id == asset_id,
                ProjectVideo.pending_mux_asset_id == asset_id,
            )
        )
    )
    if video is None:
        return None, False

    return video, video.pending_mux_asset_id == asset_id


def _clear_pending(video: ProjectVideo) -> None:
    video.pending_mux_upload_id = None
    video.pending_mux_asset_id = None
    video.pending_mux_playback_id = None
    video.pending_status = None
    video.pending_duration_seconds = None
    video.pending_aspect_ratio = None
    video.pending_original_filename = None
    video.pending_error_message = None


def _handle_upload_asset_created(
    db: Session,
    data: dict[str, Any],
) -> bool:
    upload_id = _string_value(data.get("id"))
    asset_id = _string_value(data.get("asset_id"))
    if upload_id is None or asset_id is None:
        return False

    video, is_pending = _video_by_upload_id(db, upload_id)
    if video is None:
        return False

    if is_pending:
        if video.pending_status == "ready":
            return True

        video.pending_mux_asset_id = asset_id
        video.pending_status = "processing"
        video.pending_error_message = None
    else:
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

    video, is_pending = _video_by_upload_id(db, upload_id)
    if video is None:
        return False

    error_message = (
        _extract_error_message(data) or "Mux could not process the video upload."
    )

    if is_pending:
        if video.pending_status == "ready":
            return True

        video.pending_status = "error"
        video.pending_error_message = error_message
    else:
        if video.status == "ready":
            return True

        video.status = "error"
        video.error_message = error_message

    db.commit()
    return True


def _handle_asset_ready(
    db: Session,
    data: dict[str, Any],
) -> bool:
    asset_id = _string_value(data.get("id"))
    if asset_id is None:
        return False

    video, is_pending = _video_by_asset_id(db, asset_id)
    if video is None:
        return False

    playback_id = _extract_playback_id(data)
    duration = _float_value(data.get("duration"))
    aspect_ratio = _string_value(data.get("aspect_ratio"))

    if not is_pending:
        video.status = "ready"

        if playback_id is not None:
            video.mux_playback_id = playback_id
        if duration is not None:
            video.duration_seconds = duration
        if aspect_ratio is not None:
            video.aspect_ratio = aspect_ratio

        video.error_message = None
        db.commit()
        return True

    # A replacement is not promoted until it has a usable playback ID.
    if playback_id is None:
        video.pending_status = "error"
        video.pending_error_message = (
            "Mux marked the replacement ready without a playback ID."
        )
        db.commit()
        return True

    old_upload_id = video.mux_upload_id
    old_asset_id = video.mux_asset_id

    # Persist the old resource before promotion so a failed remote cleanup
    # remains retryable without risking the replacement that is becoming
    # active.
    video.cleanup_mux_upload_id = old_upload_id
    video.cleanup_mux_asset_id = old_asset_id
    video.cleanup_error_message = None

    # Promote the ready replacement first. From this point forward the
    # project always has a valid current video even if old-resource cleanup
    # temporarily fails.
    video.mux_upload_id = video.pending_mux_upload_id
    video.mux_asset_id = video.pending_mux_asset_id
    video.mux_playback_id = playback_id
    video.status = "ready"
    video.duration_seconds = duration
    video.aspect_ratio = aspect_ratio
    video.original_filename = video.pending_original_filename
    video.error_message = None

    _clear_pending(video)
    db.commit()

    # Cleanup is intentionally after promotion. Successful cleanup removes
    # the bookkeeping. Failure keeps the old IDs so cleanup can be retried.
    try:
        cleanup_project_video(
            upload_id=video.cleanup_mux_upload_id,
            asset_id=video.cleanup_mux_asset_id,
        )
    except (MuxAPIError, MuxConfigurationError) as exc:
        video.cleanup_error_message = str(exc)
        db.commit()
        return True

    video.cleanup_mux_upload_id = None
    video.cleanup_mux_asset_id = None
    video.cleanup_error_message = None
    db.commit()

    return True


def _handle_asset_errored(
    db: Session,
    data: dict[str, Any],
) -> bool:
    asset_id = _string_value(data.get("id"))
    if asset_id is None:
        return False

    video, is_pending = _video_by_asset_id(db, asset_id)
    if video is None:
        return False

    error_message = (
        _extract_error_message(data) or "Mux could not process the video asset."
    )

    if is_pending:
        if video.pending_status == "ready":
            return True

        video.pending_status = "error"
        video.pending_error_message = error_message
    else:
        # Duplicate/out-of-order failure events must never make a
        # successfully ready active asset unusable again.
        if video.status == "ready":
            return True

        video.status = "error"
        video.error_message = error_message

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
        return _handle_upload_asset_created(db, data)

    if event_type == "video.upload.errored":
        return _handle_upload_errored(db, data)

    if event_type == "video.asset.ready":
        return _handle_asset_ready(db, data)

    if event_type == "video.asset.errored":
        return _handle_asset_errored(db, data)

    return False
