from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings

MUX_API_BASE_URL = "https://api.mux.com/video/v1"


class MuxConfigurationError(RuntimeError):
    pass


class MuxAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class MuxDirectUpload:
    upload_id: str
    upload_url: str
    status: str


@dataclass(frozen=True)
class MuxDirectUploadStatus:
    upload_id: str
    status: str
    asset_id: str | None


def ensure_mux_configured() -> None:
    missing = []

    if not settings.mux_token_id.strip():
        missing.append("MUX_TOKEN_ID")

    if not settings.mux_token_secret.strip():
        missing.append("MUX_TOKEN_SECRET")

    if missing:
        raise MuxConfigurationError(
            "Mux is not configured. Missing: " + ", ".join(missing)
        )


def _extract_error_message(
    response: httpx.Response,
) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text.strip() or "Unknown Mux API error."

    error = payload.get("error")

    if isinstance(error, dict):
        messages = error.get("messages")
        if isinstance(messages, list) and messages:
            return "; ".join(str(message) for message in messages)

        message = error.get("message")
        if message:
            return str(message)

    if isinstance(error, str):
        return error

    return "Unknown Mux API error."


def mux_request(
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_mux_configured()

    try:
        response = httpx.request(
            method,
            f"{MUX_API_BASE_URL}{path}",
            auth=(
                settings.mux_token_id,
                settings.mux_token_secret,
            ),
            json=json,
            timeout=15.0,
        )
    except httpx.HTTPError as exc:
        raise MuxAPIError("Could not connect to Mux.") from exc

    if response.is_error:
        raise MuxAPIError(_extract_error_message(response))

    try:
        payload = response.json()
    except ValueError as exc:
        raise MuxAPIError("Mux returned an invalid response.") from exc

    data = payload.get("data")

    if not isinstance(data, dict):
        raise MuxAPIError("Mux returned an invalid response.")

    return data


def create_direct_upload(
    *,
    project_id: int,
) -> MuxDirectUpload:
    data = mux_request(
        "POST",
        "/uploads",
        json={
            "cors_origin": settings.mux_upload_cors_origin,
            "new_asset_settings": {
                "playback_policies": ["public"],
                "video_quality": "basic",
                "max_resolution_tier": "1080p",
                "passthrough": f"project:{project_id}",
                "meta": {
                    "external_id": f"project:{project_id}",
                },
            },
        },
    )

    upload_id = data.get("id")
    upload_url = data.get("url")
    upload_status = data.get("status")

    if not isinstance(upload_id, str) or not upload_id:
        raise MuxAPIError("Mux did not return an upload ID.")

    if not isinstance(upload_url, str) or not upload_url:
        raise MuxAPIError("Mux did not return an upload URL.")

    if not isinstance(upload_status, str):
        upload_status = "waiting"

    return MuxDirectUpload(
        upload_id=upload_id,
        upload_url=upload_url,
        status=upload_status,
    )


def delete_asset(
    asset_id: str,
) -> None:
    ensure_mux_configured()

    try:
        response = httpx.request(
            "DELETE",
            f"{MUX_API_BASE_URL}/assets/{asset_id}",
            auth=(
                settings.mux_token_id,
                settings.mux_token_secret,
            ),
            timeout=15.0,
        )
    except httpx.HTTPError as exc:
        raise MuxAPIError("Could not connect to Mux.") from exc

    if response.status_code == 404:
        return

    if response.is_error:
        raise MuxAPIError(_extract_error_message(response))


def get_direct_upload(
    upload_id: str,
) -> MuxDirectUploadStatus | None:
    ensure_mux_configured()

    try:
        response = httpx.request(
            "GET",
            f"{MUX_API_BASE_URL}/uploads/{upload_id}",
            auth=(
                settings.mux_token_id,
                settings.mux_token_secret,
            ),
            timeout=15.0,
        )
    except httpx.HTTPError as exc:
        raise MuxAPIError("Could not connect to Mux.") from exc

    if response.status_code == 404:
        return None

    if response.is_error:
        raise MuxAPIError(_extract_error_message(response))

    try:
        payload = response.json()
    except ValueError as exc:
        raise MuxAPIError("Mux returned an invalid response.") from exc

    data = payload.get("data")
    if not isinstance(data, dict):
        raise MuxAPIError("Mux returned an invalid response.")

    remote_upload_id = data.get("id")
    upload_status = data.get("status")
    asset_id = data.get("asset_id")

    if not isinstance(remote_upload_id, str) or not remote_upload_id:
        raise MuxAPIError("Mux did not return an upload ID.")

    if not isinstance(upload_status, str) or not upload_status:
        raise MuxAPIError("Mux did not return an upload status.")

    if not isinstance(asset_id, str) or not asset_id:
        asset_id = None

    return MuxDirectUploadStatus(
        upload_id=remote_upload_id,
        status=upload_status,
        asset_id=asset_id,
    )


def cancel_direct_upload(
    upload_id: str,
) -> None:
    ensure_mux_configured()

    try:
        response = httpx.request(
            "PUT",
            f"{MUX_API_BASE_URL}/uploads/{upload_id}/cancel",
            auth=(
                settings.mux_token_id,
                settings.mux_token_secret,
            ),
            timeout=15.0,
        )
    except httpx.HTTPError as exc:
        raise MuxAPIError("Could not connect to Mux.") from exc

    if response.status_code == 404:
        return

    if response.is_error:
        raise MuxAPIError(_extract_error_message(response))


def cleanup_project_video(
    *,
    upload_id: str | None,
    asset_id: str | None,
) -> None:
    if asset_id:
        delete_asset(asset_id)
        return

    if not upload_id:
        return

    upload = get_direct_upload(upload_id)

    if upload is None:
        return

    if upload.status == "waiting":
        cancel_direct_upload(upload_id)
        return

    if upload.status == "asset_created":
        if not upload.asset_id:
            raise MuxAPIError(
                "Mux upload created an asset but did not return its asset ID."
            )
        delete_asset(upload.asset_id)
        return

    if upload.status in {
        "cancelled",
        "errored",
        "timed_out",
    }:
        return

    raise MuxAPIError(f'Mux upload is in unsupported state "{upload.status}".')
