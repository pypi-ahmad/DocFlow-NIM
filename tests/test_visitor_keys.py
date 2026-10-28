import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from PIL import Image

from docflow.backends import ParseError, parse_page, validate_api_key


def test_explicit_keys_are_isolated(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "owner-secret")
    seen = []

    def handle(request):
        seen.append(request.headers["authorization"])
        return httpx.Response(200, json={"content": "text", "finish_reason": "stop"})

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        for key in ("visitor-one", "visitor-two"):
            result = parse_page(
                Image.new("RGB", (8, 8)), "online", api_key=key, client=client
            )
            assert key not in repr(result)
        with pytest.raises(ParseError, match="missing"):
            parse_page(Image.new("RGB", (8, 8)), "online", api_key="", client=client)
    assert seen == ["Bearer visitor-one", "Bearer visitor-two"]


@pytest.mark.parametrize("status", [401, 403, 429, 500])
def test_provider_errors_do_not_echo_secrets(status):
    secret = "sentinel-credential"
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(status, text=secret)
        )
    ) as client:
        with pytest.raises(ParseError) as error:
            parse_page(
                Image.new("RGB", (8, 8)), "online", api_key=secret, client=client
            )
    assert secret not in str(error.value)


def test_dispatch_bypasses_gpu_and_does_not_store_key():
    # Load the real dispatcher without downloading or initializing GPU weights.
    tree = ast.parse(Path("app.py").read_text(encoding="utf-8"))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run"
    )
    namespace = dict(
        gr=SimpleNamespace(Progress=lambda: None, Error=ParseError),
        ParseError=ParseError,
        validate_api_key=validate_api_key,
        run_gpu=Mock(),
        convert_batch=Mock(),
        parse_page=Mock(),
    )
    exec(
        compile(ast.Module(body=[function], type_ignores=[]), "app.py", "exec"),
        namespace,
    )
    state = {"jobs": []}
    namespace["run"](state, "My NVIDIA API key", "visitor-key")
    namespace["run_gpu"].assert_not_called()
    args = namespace["convert_batch"].call_args.args
    assert args[1] == "online"
    args[2]("image")
    namespace["parse_page"].assert_called_once_with(
        "image", "online", api_key="visitor-key"
    )
    assert state == {"jobs": []}
    namespace["convert_batch"].reset_mock()
    namespace["run"](state, "Space GPU", "")
    namespace["run_gpu"].assert_called_once()
    namespace["convert_batch"].assert_not_called()
