import httpx
import pytest
from PIL import Image

from docflow.backends import HOSTED_URL, ParseError, parse_page


def test_missing_key_prevents_request(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    with pytest.raises(ParseError, match="missing"):
        parse_page(Image.new("RGB", (32, 32)), "online")


def test_offline_has_no_cloud_auth_or_fallback(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-test-value")

    def handle(request):
        assert request.url.host == "127.0.0.1"
        assert "authorization" not in request.headers
        return httpx.Response(503)

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ParseError, match="503"):
            parse_page(Image.new("RGB", (32, 32)), "offline", client=client)


def test_online_preserves_truncation(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")

    def handle(request):
        assert str(request.url) == HOSTED_URL
        assert request.headers["authorization"] == "Bearer test-key"
        assert b'name="document"' in request.read()
        return httpx.Response(
            200, json={"content": "partial", "finish_reason": "length", "usage": {}}
        )

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        result = parse_page(Image.new("RGB", (32, 32)), "online", client=client)
    assert not result.complete


def test_malformed_response_rejected():
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"content": 12})
        )
    ) as client:
        with pytest.raises(ParseError, match="invalid"):
            parse_page(Image.new("RGB", (32, 32)), "offline", client=client)
