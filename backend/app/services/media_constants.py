from typing import Final

IMAGE_MIME_TYPES: Final[frozenset[str]] = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/avif",
    }
)

DOCUMENT_MIME_TYPES: Final[frozenset[str]] = frozenset(
    {
        "application/pdf",
    }
)

ALLOWED_MEDIA_MIME_TYPES: Final[frozenset[str]] = IMAGE_MIME_TYPES | DOCUMENT_MIME_TYPES

MAX_IMAGE_BYTES: Final[int] = 20 * 1024 * 1024
MAX_DOCUMENT_BYTES: Final[int] = 20 * 1024 * 1024
MAX_IMAGE_PIXELS: Final[int] = 50_000_000

IMAGE_VARIANT_WIDTHS: Final[dict[str, int]] = {
    "thumbnail": 400,
    "small": 800,
    "medium": 1400,
    "large": 2400,
}
