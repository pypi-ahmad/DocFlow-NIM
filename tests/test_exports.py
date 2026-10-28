import warnings
from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_zip_does_not_duplicate_saved_markdown(tmp_path):
    (tmp_path / "document.md").write_text("Hello", encoding="utf-8")
    result = {
        "name": "test.pdf",
        "complete": True,
        "pages": [{"number": 1, "markdown": "Hello"}],
    }
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "streamlit_app.py"))
    app.session_state["results"] = [(result, tmp_path)]
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        app.run()
    assert not app.exception
    assert not any("Duplicate name" in str(item.message) for item in captured)
