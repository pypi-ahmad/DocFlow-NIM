"""Check the hosted Parse contract using a generated, non-sensitive page."""

import io
import os

import httpx
from PIL import Image, ImageDraw


def main():
    key = os.environ.get("NVIDIA_API_KEY", "").strip()
    if not key:
        raise SystemExit("NVIDIA_API_KEY is missing from the process environment.")
    page = Image.new("RGB", (800, 600), "white")
    ImageDraw.Draw(page).text(
        (50, 60), "DocFlow test invoice\nTotal: 42.00", fill="black", font_size=32
    )
    buffer = io.BytesIO()
    page.save(buffer, format="PNG")
    try:
        response = httpx.post(
            "https://ai.api.nvidia.com/v1/retrieval/nvidia/nemotron-3.5-parse/parse",
            headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
            files={"document": ("synthetic.png", buffer.getvalue(), "image/png")},
            timeout=120,
        )
    except httpx.RequestError as exc:
        raise SystemExit(f"Network failure: {type(exc).__name__}") from None
    print(f"HTTP {response.status_code}")
    if response.is_success:
        result = response.json()
        print("Response fields:", sorted(result))
        print("Finish reason:", result.get("finish_reason"))
        print("Content:", str(result.get("content", ""))[:1500])
    else:
        print("Request failed; credentials and response body withheld.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
