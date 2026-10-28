"""Page inference transports; credentials remain in the server process."""

import io
import os
from dataclasses import dataclass
from typing import Literal

import httpx
from PIL import Image

HOSTED_URL = "https://ai.api.nvidia.com/v1/retrieval/nvidia/nemotron-3.5-parse/parse"
MODEL_REVISION = "4035ffb1d8f8bafcdb867dfaf6f7514f101464f9"


class ParseError(RuntimeError):
    """A page could not be parsed; message is safe to display."""


@dataclass(frozen=True)
class PageResult:
    content: str
    finish_reason: str
    usage: dict
    backend: str

    @property
    def complete(self) -> bool:
        return self.finish_reason == "stop"


def parse_page(
    image: Image.Image, mode: Literal["offline", "online"], *, client=None
) -> PageResult:
    """Parse one RGB page, never falling back to another backend."""
    if mode not in ("offline", "online"):
        raise ValueError("Choose offline or online mode.")
    headers = {"Accept": "application/json"}
    if mode == "online":
        key = os.environ.get("NVIDIA_API_KEY", "").strip()
        if not key:
            raise ParseError("NVIDIA_API_KEY is missing from the process environment.")
        headers["Authorization"] = f"Bearer {key}"
        url = HOSTED_URL
    else:
        url = "http://127.0.0.1:8473/v1/parse"
    encoded = io.BytesIO()
    image.convert("RGB").save(encoded, format="PNG")
    sender = client or httpx
    try:
        response = sender.post(
            url,
            headers=headers,
            files={"document": ("page.png", encoded.getvalue(), "image/png")},
            timeout=180,
        )
    except httpx.RequestError:
        raise ParseError(
            f"Cannot reach the {mode} model. Check its availability."
        ) from None
    if not response.is_success:
        raise ParseError(f"The {mode} model returned HTTP {response.status_code}.")
    try:
        payload = response.json()
        content = payload["content"]
        reason = payload["finish_reason"]
        usage = payload.get("usage", {})
        if (
            not isinstance(content, str)
            or not isinstance(reason, str)
            or not isinstance(usage, dict)
        ):
            raise ValueError
    except (ValueError, KeyError, TypeError):
        raise ParseError("The model returned an invalid page response.") from None
    return PageResult(content, reason, usage, mode)
