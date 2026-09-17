from dataclasses import dataclass
from io import BytesIO

from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError

from app.services.media_constants import (
    ALLOWED_MEDIA_MIME_TYPES,
    DOCUMENT_MIME_TYPES,
    IMAGE_MIME_TYPES,
    MAX_DOCUMENT_BYTES,
    MAX_IMAGE_BYTES,
    MAX_IMAGE_PIXELS,
)


@dataclass(frozen=True, slots=True)
class ValidatedMedia:
    file_type: str
    mime_type: str
    file_size: int
    width: int | None = None
    height: int | None = None


def _validation_error(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=detail,
    )


def validate_media(
    content: bytes,
    mime_type: str,
) -> ValidatedMedia:
    normalized_mime = mime_type.lower().strip()
    file_size = len(content)

    if normalized_mime not in ALLOWED_MEDIA_MIME_TYPES:
        raise _validation_error("Unsupported media type.")

    if normalized_mime in DOCUMENT_MIME_TYPES:
        if file_size > MAX_DOCUMENT_BYTES:
            raise _validation_error("Document exceeds the maximum file size.")

        if not content.startswith(b"%PDF-"):
            raise _validation_error("Invalid PDF document.")

        return ValidatedMedia(
            file_type="document",
            mime_type=normalized_mime,
            file_size=file_size,
        )

    if normalized_mime not in IMAGE_MIME_TYPES:
        raise _validation_error("Unsupported media type.")

    if file_size > MAX_IMAGE_BYTES:
        raise _validation_error("Image exceeds the maximum file size.")

    try:
        with Image.open(BytesIO(content)) as image:
            width, height = image.size

            if width <= 0 or height <= 0:
                raise _validation_error("Invalid image dimensions.")

            if width * height > MAX_IMAGE_PIXELS:
                raise _validation_error("Image exceeds the maximum pixel count.")

            image.verify()

    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise _validation_error("Invalid image file.") from exc

    return ValidatedMedia(
        file_type="image",
        mime_type=normalized_mime,
        file_size=file_size,
        width=width,
        height=height,
    )
