from unittest.mock import Mock

import httpx
import pytest

from app.services import mux_video


def test_create_direct_upload_builds_expected_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mux_video.settings,
        "mux_token_id",
        "test-token-id",
    )
    monkeypatch.setattr(
        mux_video.settings,
        "mux_token_secret",
        "test-token-secret",
    )
    monkeypatch.setattr(
        mux_video.settings,
        "mux_upload_cors_origin",
        "http://localhost:5174",
    )

    response = Mock(spec=httpx.Response)
    response.is_error = False
    response.json.return_value = {
        "data": {
            "id": "upload-123",
            "url": "https://storage.example/upload",
            "status": "waiting",
        }
    }

    request = Mock(return_value=response)
    monkeypatch.setattr(
        mux_video.httpx,
        "request",
        request,
    )

    result = mux_video.create_direct_upload(
        project_id=42,
    )

    assert result.upload_id == "upload-123"
    assert result.upload_url == ("https://storage.example/upload")
    assert result.status == "waiting"

    request.assert_called_once_with(
        "POST",
        "https://api.mux.com/video/v1/uploads",
        auth=("test-token-id", "test-token-secret"),
        json={
            "cors_origin": "http://localhost:5174",
            "new_asset_settings": {
                "playback_policies": ["public"],
                "video_quality": "basic",
                "max_resolution_tier": "1080p",
                "passthrough": "project:42",
                "meta": {
                    "external_id": "project:42",
                },
            },
        },
        timeout=15.0,
    )


def test_mux_requires_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mux_video.settings,
        "mux_token_id",
        "",
    )
    monkeypatch.setattr(
        mux_video.settings,
        "mux_token_secret",
        "",
    )

    with pytest.raises(
        mux_video.MuxConfigurationError,
        match="MUX_TOKEN_ID, MUX_TOKEN_SECRET",
    ):
        mux_video.create_direct_upload(
            project_id=1,
        )


def test_mux_api_error_is_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mux_video.settings,
        "mux_token_id",
        "token",
    )
    monkeypatch.setattr(
        mux_video.settings,
        "mux_token_secret",
        "secret",
    )

    response = Mock(spec=httpx.Response)
    response.is_error = True
    response.json.return_value = {"error": {"message": "Invalid request."}}

    monkeypatch.setattr(
        mux_video.httpx,
        "request",
        Mock(return_value=response),
    )

    with pytest.raises(
        mux_video.MuxAPIError,
        match="Invalid request",
    ):
        mux_video.create_direct_upload(
            project_id=1,
        )


def test_mux_network_error_is_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mux_video.settings,
        "mux_token_id",
        "token",
    )
    monkeypatch.setattr(
        mux_video.settings,
        "mux_token_secret",
        "secret",
    )

    monkeypatch.setattr(
        mux_video.httpx,
        "request",
        Mock(side_effect=httpx.ConnectError("connection failed")),
    )

    with pytest.raises(
        mux_video.MuxAPIError,
        match="Could not connect to Mux",
    ):
        mux_video.create_direct_upload(
            project_id=1,
        )


def test_delete_asset_accepts_empty_success_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mux_video.settings,
        "mux_token_id",
        "token",
    )
    monkeypatch.setattr(
        mux_video.settings,
        "mux_token_secret",
        "secret",
    )

    response = Mock(spec=httpx.Response)
    response.status_code = 204
    response.is_error = False

    request = Mock(return_value=response)
    monkeypatch.setattr(
        mux_video.httpx,
        "request",
        request,
    )

    mux_video.delete_asset("asset-123")

    request.assert_called_once_with(
        "DELETE",
        "https://api.mux.com/video/v1/assets/asset-123",
        auth=("token", "secret"),
        timeout=15.0,
    )


def test_delete_asset_normalizes_mux_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mux_video.settings,
        "mux_token_id",
        "token",
    )
    monkeypatch.setattr(
        mux_video.settings,
        "mux_token_secret",
        "secret",
    )

    response = Mock(spec=httpx.Response)
    response.status_code = 500
    response.is_error = True
    response.json.return_value = {
        "error": {
            "message": "Mux deletion failed.",
        }
    }

    monkeypatch.setattr(
        mux_video.httpx,
        "request",
        Mock(return_value=response),
    )

    with pytest.raises(
        mux_video.MuxAPIError,
        match="Mux deletion failed",
    ):
        mux_video.delete_asset("asset-123")


def test_delete_asset_accepts_missing_remote_asset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mux_video.settings,
        "mux_token_id",
        "token",
    )
    monkeypatch.setattr(
        mux_video.settings,
        "mux_token_secret",
        "secret",
    )

    response = Mock(spec=httpx.Response)
    response.status_code = 404
    response.is_error = True
    response.json.return_value = {
        "error": {
            "message": "Asset not found.",
        }
    }

    request = Mock(return_value=response)

    monkeypatch.setattr(
        mux_video.httpx,
        "request",
        request,
    )

    mux_video.delete_asset("missing-asset")

    request.assert_called_once_with(
        "DELETE",
        "https://api.mux.com/video/v1/assets/missing-asset",
        auth=("token", "secret"),
        timeout=15.0,
    )


def test_get_direct_upload_returns_waiting_upload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mux_video.settings, "mux_token_id", "token")
    monkeypatch.setattr(mux_video.settings, "mux_token_secret", "secret")

    response = Mock(spec=httpx.Response)
    response.status_code = 200
    response.is_error = False
    response.json.return_value = {
        "data": {
            "id": "upload-123",
            "status": "waiting",
            "asset_id": None,
        }
    }

    request = Mock(return_value=response)
    monkeypatch.setattr(mux_video.httpx, "request", request)

    result = mux_video.get_direct_upload("upload-123")

    assert result == mux_video.MuxDirectUploadStatus(
        upload_id="upload-123",
        status="waiting",
        asset_id=None,
    )
    request.assert_called_once_with(
        "GET",
        "https://api.mux.com/video/v1/uploads/upload-123",
        auth=("token", "secret"),
        timeout=15.0,
    )


def test_get_direct_upload_returns_none_when_remote_upload_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mux_video.settings, "mux_token_id", "token")
    monkeypatch.setattr(mux_video.settings, "mux_token_secret", "secret")

    response = Mock(spec=httpx.Response)
    response.status_code = 404
    response.is_error = True

    monkeypatch.setattr(
        mux_video.httpx,
        "request",
        Mock(return_value=response),
    )

    assert mux_video.get_direct_upload("missing-upload") is None


def test_cancel_direct_upload_accepts_empty_success_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mux_video.settings, "mux_token_id", "token")
    monkeypatch.setattr(mux_video.settings, "mux_token_secret", "secret")

    response = Mock(spec=httpx.Response)
    response.status_code = 204
    response.is_error = False

    request = Mock(return_value=response)
    monkeypatch.setattr(mux_video.httpx, "request", request)

    mux_video.cancel_direct_upload("upload-123")

    request.assert_called_once_with(
        "PUT",
        "https://api.mux.com/video/v1/uploads/upload-123/cancel",
        auth=("token", "secret"),
        timeout=15.0,
    )


def test_cleanup_project_video_deletes_known_asset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delete_asset = Mock()
    get_upload = Mock()
    cancel_upload = Mock()

    monkeypatch.setattr(mux_video, "delete_asset", delete_asset)
    monkeypatch.setattr(mux_video, "get_direct_upload", get_upload)
    monkeypatch.setattr(
        mux_video,
        "cancel_direct_upload",
        cancel_upload,
    )

    mux_video.cleanup_project_video(
        upload_id="upload-123",
        asset_id="asset-123",
    )

    delete_asset.assert_called_once_with("asset-123")
    get_upload.assert_not_called()
    cancel_upload.assert_not_called()


def test_cleanup_project_video_cancels_waiting_upload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_upload = Mock(
        return_value=mux_video.MuxDirectUploadStatus(
            upload_id="upload-123",
            status="waiting",
            asset_id=None,
        )
    )
    cancel_upload = Mock()
    delete_asset = Mock()

    monkeypatch.setattr(mux_video, "get_direct_upload", get_upload)
    monkeypatch.setattr(
        mux_video,
        "cancel_direct_upload",
        cancel_upload,
    )
    monkeypatch.setattr(mux_video, "delete_asset", delete_asset)

    mux_video.cleanup_project_video(
        upload_id="upload-123",
        asset_id=None,
    )

    get_upload.assert_called_once_with("upload-123")
    cancel_upload.assert_called_once_with("upload-123")
    delete_asset.assert_not_called()


def test_cleanup_project_video_deletes_asset_created_before_webhook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mux_video,
        "get_direct_upload",
        Mock(
            return_value=mux_video.MuxDirectUploadStatus(
                upload_id="upload-123",
                status="asset_created",
                asset_id="asset-race-123",
            )
        ),
    )

    delete_asset = Mock()
    cancel_upload = Mock()

    monkeypatch.setattr(mux_video, "delete_asset", delete_asset)
    monkeypatch.setattr(
        mux_video,
        "cancel_direct_upload",
        cancel_upload,
    )

    mux_video.cleanup_project_video(
        upload_id="upload-123",
        asset_id=None,
    )

    delete_asset.assert_called_once_with("asset-race-123")
    cancel_upload.assert_not_called()


@pytest.mark.parametrize(
    "upload_status",
    [
        "cancelled",
        "errored",
        "timed_out",
    ],
)
def test_cleanup_project_video_accepts_terminal_upload_states(
    monkeypatch: pytest.MonkeyPatch,
    upload_status: str,
) -> None:
    monkeypatch.setattr(
        mux_video,
        "get_direct_upload",
        Mock(
            return_value=mux_video.MuxDirectUploadStatus(
                upload_id="upload-123",
                status=upload_status,
                asset_id=None,
            )
        ),
    )

    delete_asset = Mock()
    cancel_upload = Mock()

    monkeypatch.setattr(mux_video, "delete_asset", delete_asset)
    monkeypatch.setattr(
        mux_video,
        "cancel_direct_upload",
        cancel_upload,
    )

    mux_video.cleanup_project_video(
        upload_id="upload-123",
        asset_id=None,
    )

    delete_asset.assert_not_called()
    cancel_upload.assert_not_called()


def test_cleanup_project_video_accepts_missing_remote_upload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mux_video,
        "get_direct_upload",
        Mock(return_value=None),
    )

    delete_asset = Mock()
    cancel_upload = Mock()

    monkeypatch.setattr(mux_video, "delete_asset", delete_asset)
    monkeypatch.setattr(
        mux_video,
        "cancel_direct_upload",
        cancel_upload,
    )

    mux_video.cleanup_project_video(
        upload_id="missing-upload",
        asset_id=None,
    )

    delete_asset.assert_not_called()
    cancel_upload.assert_not_called()


def test_cleanup_project_video_rejects_asset_created_without_asset_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mux_video,
        "get_direct_upload",
        Mock(
            return_value=mux_video.MuxDirectUploadStatus(
                upload_id="upload-123",
                status="asset_created",
                asset_id=None,
            )
        ),
    )

    with pytest.raises(
        mux_video.MuxAPIError,
        match="did not return its asset ID",
    ):
        mux_video.cleanup_project_video(
            upload_id="upload-123",
            asset_id=None,
        )


def test_cleanup_project_video_rejects_unknown_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mux_video,
        "get_direct_upload",
        Mock(
            return_value=mux_video.MuxDirectUploadStatus(
                upload_id="upload-123",
                status="mystery_state",
                asset_id=None,
            )
        ),
    )

    with pytest.raises(
        mux_video.MuxAPIError,
        match="unsupported state",
    ):
        mux_video.cleanup_project_video(
            upload_id="upload-123",
            asset_id=None,
        )
