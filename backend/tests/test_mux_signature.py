import hashlib
import hmac

import pytest

from app.services.mux_signature import (
    MuxWebhookSignatureError,
    verify_mux_webhook_signature,
)

SECRET = "mux-test-secret"
NOW = 1_700_000_000
BODY = b'{"type":"video.asset.ready"}'


def sign(
    body: bytes = BODY,
    *,
    timestamp: int = NOW,
    secret: str = SECRET,
) -> str:
    payload = str(timestamp).encode("ascii") + b"." + body

    signature = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return f"t={timestamp},v1={signature}"


def test_valid_signature() -> None:
    verify_mux_webhook_signature(
        BODY,
        sign(),
        SECRET,
        now=NOW,
    )


def test_multiple_v1_signatures_accepts_matching_one() -> None:
    valid = sign().split("v1=", 1)[1]

    verify_mux_webhook_signature(
        BODY,
        f"t={NOW},v1=invalid,v1={valid}",
        SECRET,
        now=NOW,
    )


def test_rejects_modified_body() -> None:
    with pytest.raises(
        MuxWebhookSignatureError,
        match="Invalid Mux webhook signature",
    ):
        verify_mux_webhook_signature(
            b'{"modified":true}',
            sign(),
            SECRET,
            now=NOW,
        )


def test_rejects_wrong_secret() -> None:
    with pytest.raises(
        MuxWebhookSignatureError,
        match="Invalid Mux webhook signature",
    ):
        verify_mux_webhook_signature(
            BODY,
            sign(),
            "wrong-secret",
            now=NOW,
        )


def test_rejects_missing_header() -> None:
    with pytest.raises(
        MuxWebhookSignatureError,
        match="Missing Mux webhook signature",
    ):
        verify_mux_webhook_signature(
            BODY,
            "",
            SECRET,
            now=NOW,
        )


def test_rejects_missing_timestamp() -> None:
    with pytest.raises(
        MuxWebhookSignatureError,
        match="missing a timestamp",
    ):
        verify_mux_webhook_signature(
            BODY,
            "v1=abc",
            SECRET,
            now=NOW,
        )


def test_rejects_invalid_timestamp() -> None:
    with pytest.raises(
        MuxWebhookSignatureError,
        match="Invalid Mux webhook timestamp",
    ):
        verify_mux_webhook_signature(
            BODY,
            "t=abc,v1=123",
            SECRET,
            now=NOW,
        )


def test_rejects_missing_v1_signature() -> None:
    with pytest.raises(
        MuxWebhookSignatureError,
        match="contains no v1 signature",
    ):
        verify_mux_webhook_signature(
            BODY,
            f"t={NOW}",
            SECRET,
            now=NOW,
        )


def test_rejects_stale_timestamp() -> None:
    with pytest.raises(
        MuxWebhookSignatureError,
        match="timestamp is too old",
    ):
        verify_mux_webhook_signature(
            BODY,
            sign(timestamp=NOW - 301),
            SECRET,
            now=NOW,
        )


def test_accepts_timestamp_at_tolerance_boundary() -> None:
    timestamp = NOW - 300

    verify_mux_webhook_signature(
        BODY,
        sign(timestamp=timestamp),
        SECRET,
        now=NOW,
    )


def test_rejects_far_future_timestamp() -> None:
    with pytest.raises(
        MuxWebhookSignatureError,
        match="too far in the future",
    ):
        verify_mux_webhook_signature(
            BODY,
            sign(timestamp=NOW + 301),
            SECRET,
            now=NOW,
        )
