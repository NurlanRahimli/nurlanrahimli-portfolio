from io import BytesIO

import pytest
from fastapi import HTTPException
from PIL import Image

from app.services.image_processing import create_image_variants
from app.services.media_validation import validate_media
from app.services.r2_storage import R2ConfigurationError, R2Storage


def make_image(
    *,
    width: int = 1200,
    height: int = 800,
    image_format: str = "PNG",
) -> bytes:
    image = Image.new(
        "RGB",
        (width, height),
        "white",
    )
    buffer = BytesIO()
    image.save(buffer, format=image_format)
    return buffer.getvalue()


def test_validate_image_returns_metadata() -> None:
    content = make_image(width=1200, height=800)

    result = validate_media(
        content,
        "image/png",
    )

    assert result.file_type == "image"
    assert result.mime_type == "image/png"
    assert result.file_size == len(content)
    assert result.width == 1200
    assert result.height == 800


def test_validate_pdf_returns_document_metadata() -> None:
    content = b"%PDF-1.7\nportfolio resume"

    result = validate_media(
        content,
        "application/pdf",
    )

    assert result.file_type == "document"
    assert result.mime_type == "application/pdf"
    assert result.file_size == len(content)
    assert result.width is None
    assert result.height is None


def test_validate_media_rejects_unsupported_type() -> None:
    with pytest.raises(HTTPException) as exc_info:
        validate_media(
            b"hello",
            "text/plain",
        )

    assert exc_info.value.status_code == 422


def test_validate_media_rejects_fake_image() -> None:
    with pytest.raises(HTTPException) as exc_info:
        validate_media(
            b"not an image",
            "image/png",
        )

    assert exc_info.value.status_code == 422


def test_validate_media_rejects_fake_pdf() -> None:
    with pytest.raises(HTTPException) as exc_info:
        validate_media(
            b"not a pdf",
            "application/pdf",
        )

    assert exc_info.value.status_code == 422


def test_create_image_variants_uses_expected_widths() -> None:
    content = make_image(
        width=3000,
        height=2000,
    )

    variants = create_image_variants(content)

    assert [variant.name for variant in variants] == [
        "thumbnail",
        "small",
        "medium",
        "large",
    ]

    assert [variant.width for variant in variants] == [
        400,
        800,
        1400,
        2400,
    ]

    assert all(variant.mime_type == "image/webp" for variant in variants)


def test_small_image_variants_never_upscale() -> None:
    content = make_image(
        width=300,
        height=200,
    )

    variants = create_image_variants(content)

    assert len(variants) == 4
    assert all(variant.width == 300 for variant in variants)
    assert all(variant.height == 200 for variant in variants)


def test_r2_public_url_encodes_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import r2_storage as module

    monkeypatch.setattr(
        module.settings,
        "r2_public_base_url",
        "https://media.example.com/",
    )

    storage = R2Storage()

    assert storage.public_url("portfolio/My Project/image 1.webp") == (
        "https://media.example.com/portfolio/My%20Project/image%201.webp"
    )


def test_r2_requires_public_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import r2_storage as module

    monkeypatch.setattr(
        module.settings,
        "r2_public_base_url",
        "",
    )

    storage = R2Storage()

    with pytest.raises(R2ConfigurationError):
        storage.public_url("image.webp")
