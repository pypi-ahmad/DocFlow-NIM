"""Session-scoped CPU preparation and exports for the public Space."""
import json
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path

from docflow.conversion import page_count

EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".tif", ".tiff", ".webp"}


def cleanup(state):
    """Delete only the temporary directory created for this session."""
    if state and state.get("root"):
        shutil.rmtree(state["root"], ignore_errors=True)


def prepare(files, first, last, state):
    """Validate the complete workload before allocating a GPU."""
    if not files or len(files) > 5:
        raise ValueError("Upload between one and five documents.")
    first, last = int(first), int(last)
    if first < 1 or last < 0 or (last and last < first):
        raise ValueError("Choose a valid page range; last page 0 means all.")
    jobs, count = [], 0
    for path in files:
        path = Path(path)
        if path.suffix.lower() not in EXTENSIONS or path.stat().st_size > 50 * 1024**2:
            raise ValueError("Use supported PDFs/images up to 50 MiB per file.")
        start, end = (first, last or None) if len(files) == 1 else (1, None)
        total = page_count(path.read_bytes(), path.name)
        selected = max(0, min(total, end if end is not None else total) - start + 1)
        count += selected
        if count > 5:
            raise ValueError("Select at most five pages in total.")
        if not selected:
            raise ValueError("No pages matched the selection.")
        jobs.append({"path": str(path), "first": start, "last": end})
    state = dict(state or {})
    if not state.get("root"):
        state["root"] = tempfile.mkdtemp(prefix="docflow-space-")
    state["job_root"] = str(Path(state["root"]) / uuid.uuid4().hex)
    state["jobs"] = jobs
    state["results"] = []
    return state


def bundle(results, destination):
    """Keep each document in its own archive directory, even for equal names."""
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for index, (_, directory) in enumerate(results, 1):
            for file in Path(directory).iterdir():
                if file.is_file():
                    archive.write(file, f"document-{index}/{file.name}")
    return str(destination)


def view(state, selection):
    """Return the selected document's previews and downloadable artifacts."""
    result, directory = state["results"][int(selection)]
    directory = Path(directory)
    previews = [str(directory / f"page-{page['number']}.png") for page in result["pages"]]
    annotations = sorted(str(p) for p in directory.glob("annotated-*.png"))
    files = [str(directory / name) for name in
             ("document.md", "document.html", "document.json", "chunks.json")]
    return ("Complete" if result["complete"] else "Some pages are incomplete. Inspect Layout and JSON for errors, then retry those pages.",
            previews, (directory / "document.md").read_text(encoding="utf-8"),
            annotations, json.loads((directory / "document.json").read_text(encoding="utf-8")), files)
