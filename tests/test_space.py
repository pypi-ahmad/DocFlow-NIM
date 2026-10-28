import zipfile

import pytest
from PIL import Image

from docflow.space_ui import bundle, cleanup, prepare


def test_limit_and_session_isolation(tmp_path):
    image = tmp_path / "test.tiff"
    pages = [Image.new("RGB", (20, 20)) for _ in range(6)]
    pages[0].save(image, save_all=True, append_images=pages[1:])
    with pytest.raises(ValueError, match="five pages"):
        prepare([str(image)], 1, 0, {})
    a = prepare([str(image)], 2, 3, {})
    b = prepare([str(image)], 2, 3, {})
    try:
        assert a["root"] != b["root"]
        assert a["jobs"][0]["first"] == 2
    finally:
        cleanup(a)
        cleanup(b)


def test_duplicate_archive_names(tmp_path):
    results = []
    for index in range(2):
        directory = tmp_path / str(index)
        directory.mkdir()
        (directory / "document.md").write_text(str(index))
        results.append(({}, directory))
    path = bundle(results, tmp_path / "batch.zip")
    with zipfile.ZipFile(path) as archive:
        assert len(set(archive.namelist())) == 2
        assert archive.read("document-2/document.md") == b"1"
