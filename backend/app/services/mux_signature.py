import hashlib
import hmac
import time

MUX_SIGNATURE_TOLERANCE_SECONDS = 300


class MuxWebhookSignatureError(ValueError):
    pass


def _parse_signature_header(
    signature_header: str,
) -> tuple[int, list[str]]:
    timestamp: int | None = None
    signatures: list[str] = []

    for component in signature_header.split(","):
        key, separator, value = component.strip().partition("=")

        if not separator:
            continue

        if key == "t":
            try:
                timestamp = int(value)
            except ValueError as exc:
                raise MuxWebhookSignatureError(
                    "Invalid Mux webhook timestamp."
                ) from exc

        elif key == "v1" and value:
            signatures.append(value)

    if timestamp is None:
        raise MuxWebhookSignatureError("Mux webhook signature is missing a timestamp.")

    if not signatures:
        raise MuxWebhookSignatureError(
            "Mux webhook signature contains no v1 signature."
        )

    return timestamp, signatures


def verify_mux_webhook_signature(
    raw_body: bytes,
    signature_header: str,
    secret: str,
    *,
    now: int | None = None,
    tolerance_seconds: int = MUX_SIGNATURE_TOLERANCE_SECONDS,
) -> None:
    if not secret.strip():
        raise MuxWebhookSignatureError("Mux webhook signing secret is not configured.")

    if not signature_header.strip():
        raise MuxWebhookSignatureError("Missing Mux webhook signature.")

    timestamp, signatures = _parse_signature_header(signature_header)

    current_time = int(time.time()) if now is None else now

    if current_time - timestamp > tolerance_seconds:
        raise MuxWebhookSignatureError("Mux webhook timestamp is too old.")

    # Also reject timestamps too far into the future. This keeps the
    # accepted clock-skew window symmetrical and prevents future-dated
    # signatures from bypassing replay protection.
    if timestamp - current_time > tolerance_seconds:
        raise MuxWebhookSignatureError(
            "Mux webhook timestamp is too far in the future."
        )

    signed_payload = str(timestamp).encode("ascii") + b"." + raw_body

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    if not any(
        hmac.compare_digest(
            expected_signature,
            signature,
        )
        for signature in signatures
    ):
        raise MuxWebhookSignatureError("Invalid Mux webhook signature.")
