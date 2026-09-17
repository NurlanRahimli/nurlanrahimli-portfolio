from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps

from app.services.media_constants import IMAGE_VARIANT_WIDTHS


@dataclass(frozen=True, slots=True)
class ImageVariant:
    name: str
    content: bytes
    mime_type: str
    width: int
    height: int


def create_image_variants(
    content: bytes,
) -> list[ImageVariant]:
    variants: list[ImageVariant] = []

    with Image.open(BytesIO(content)) as source:
        normalized = ImageOps.exif_transpose(source)

        if normalized.mode not in {"RGB", "RGBA"}:
            normalized = normalized.convert("RGB")

        for name, target_width in IMAGE_VARIANT_WIDTHS.items():
            width = min(target_width, normalized.width)

            if width <= 0:
                continue

            height = max(
                1,
                round(normalized.height * (width / normalized.width)),
            )

            resized = normalized.resize(
                (width, height),
                Image.Resampling.LANCZOS,
            )

            if resized.mode == "RGBA":
                background = Image.new(
                    "RGB",
                    resized.size,
                    (255, 255, 255),
                )
                background.paste(
                    resized,
                    mask=resized.getchannel("A"),
                )
                resized = background
            elif resized.mode != "RGB":
                resized = resized.convert("RGB")

            buffer = BytesIO()
            resized.save(
                buffer,
                format="WEBP",
                quality=85,
                method=6,
            )

            variants.append(
                ImageVariant(
                    name=name,
                    content=buffer.getvalue(),
                    mime_type="image/webp",
                    width=width,
                    height=height,
                )
            )

    return variants
