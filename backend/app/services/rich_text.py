from __future__ import annotations

import nh3


ALLOWED_TAGS = {
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "s",
    "ul",
    "ol",
    "li",
    "blockquote",
    "a",
}

ALLOWED_ATTRIBUTES = {
    "a": {
        "href",
        "target",
    },
}


def sanitize_rich_text(value: str) -> str:
    """Sanitize administrator-authored rich text before persistence."""

    normalized = value.strip()

    if not normalized:
        return ""

    return nh3.clean(
        normalized,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={
            "http",
            "https",
            "mailto",
        },
        link_rel="noopener noreferrer",
    ).strip()
