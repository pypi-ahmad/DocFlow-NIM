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
    image: Image.Image,
    mode: Literal["offline", "online"],
    *,
    client=None,
    api_key: str | None = None,
) -> PageResult:
    """Parse one RGB page, never falling back to another backend."""
    if mode not in ("offline", "online"):
        raise ValueError("Choose offline or online mode.")
    headers = {"Accept": "application/json"}
    if mode == "online":
        key = os.environ.get("NVIDIA_API_KEY", "") if api_key is None else api_key
        validate_api_key(key)
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
    except httpx.TimeoutException:
        raise ParseError("The model timed out. Try fewer pages and retry.") from None
    except httpx.RequestError:
        raise ParseError(
            f"Cannot reach the {mode} model. Check its availability."
        ) from None
    if not response.is_success:
        messages = {
            401: "NVIDIA rejected the API key. Check or replace it.",
            403: "This key cannot access the model. Check your NVIDIA account permissions.",
            429: "NVIDIA rate or quota limit reached. Check your quota and retry later.",
        }
        raise ParseError(
            messages.get(
                response.status_code,
                f"The {mode} model returned HTTP {response.status_code}. Retry later.",
            )
        )
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


def validate_api_key(key):
    """Reject unusable credentials without including their value in errors."""
    if not isinstance(key, str) or not key.strip():
        raise ParseError("NVIDIA API key is missing. Enter your key to continue.")
    if not key.isascii() or any(
        char.isspace() or ord(char) < 33 or ord(char) == 127 for char in key
    ):
        raise ParseError(
            "Paste a valid NVIDIA API key without whitespace or control characters."
        )
