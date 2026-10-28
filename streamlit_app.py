"""DocFlow NIM conversion interface."""

import io
import json
import os
from zipfile import ZIP_DEFLATED, ZipFile

import httpx
import streamlit as st

from docflow.conversion import ROOT, convert

st.set_page_config(page_title="DocFlow NIM", layout="wide")
st.title("DocFlow NIM")
st.caption("Document parsing with NVIDIA Nemotron-3.5-Parse")
st.session_state.setdefault("results", [])
mode = st.sidebar.selectbox("Inference mode", ["offline", "online"])
ready = True
if mode == "online":
    st.sidebar.caption("Pages are sent to NVIDIA for processing.")
    st.sidebar.write(
        "API key available"
        if os.environ.get("NVIDIA_API_KEY", "").strip()
        else "NVIDIA_API_KEY is missing"
    )
else:
    st.sidebar.caption("Uses the local model worker on port 8473.")
    try:
        response = httpx.get("http://127.0.0.1:8473/health", timeout=2)
        ready = response.is_success and response.json().get("ready") is True
    except (httpx.RequestError, ValueError):
        ready = False
    if ready:
        st.sidebar.success("Local model ready")
    else:
        st.sidebar.warning(
            "Local model is stopped or still loading. Run launch.cmd, then refresh readiness."
        )
    st.sidebar.button("Refresh readiness")
files = st.file_uploader(
    "Documents",
    type=["pdf", "png", "jpg", "jpeg", "gif", "tiff", "webp"],
    accept_multiple_files=True,
)
with st.form("convert"):
    first = st.number_input("First page", min_value=1, value=1)
    last = st.number_input("Last page (0 means all)", min_value=0, value=0)
    submitted = st.form_submit_button("Convert", disabled=not files or not ready)
if submitted:
    st.session_state.results = []
    for upload in files:
        with st.status(f"Converting {upload.name}") as status:
            try:
                result, directory = convert(
                    upload.getvalue(),
                    upload.name,
                    mode,
                    int(first) if len(files) == 1 else 1,
                    int(last) or None if len(files) == 1 else None,
                    progress=lambda page: status.update(label=f"Processed page {page}"),
                )
                st.session_state.results.append((result, directory))
                status.update(
                    label=upload.name,
                    state="complete" if result["complete"] else "error",
                )
            except Exception as exc:
                status.update(label="Conversion failed", state="error")
                st.error(str(exc))
saved = sorted((ROOT / "conversion_results").glob("*/document.json"))
if saved:
    selected = st.sidebar.selectbox(
        "Saved conversion", saved, format_func=lambda p: p.parent.name[:12]
    )
    if st.sidebar.button("Open saved conversion"):
        st.session_state.results = [
            (json.loads(selected.read_text(encoding="utf-8")), selected.parent)
        ]
for index, (result, directory) in enumerate(st.session_state.results):
    st.subheader(result["name"])
    if not result["complete"]:
        st.warning("Partial conversion: inspect failed or truncated pages.")
    markdown = "\n\n---\n\n".join(page["markdown"] for page in result["pages"])
    preview, raw, annotated, structured = st.tabs(
        ["Preview", "Markdown", "Annotated", "JSON"]
    )
    with preview:
        st.markdown(markdown)
    with raw:
        st.code(markdown, language="markdown")
    with annotated:
        for page in result["pages"]:
            image = directory / f"annotated-{page['number']}.png"
            if image.exists():
                st.image(str(image), caption=f"Page {page['number']}")
            if page.get("error"):
                st.error(page["error"])
    with structured:
        st.json(result)
    st.download_button("Download Markdown", markdown, "document.md", key=f"md-{index}")
    st.download_button(
        "Download JSON",
        json.dumps(result, indent=2),
        "document.json",
        key=f"json-{index}",
    )
    archive = io.BytesIO()
    with ZipFile(archive, "w", ZIP_DEFLATED) as output:
        output.writestr("document.md", markdown)
        for artifact in directory.iterdir():
            if artifact.is_file() and artifact.name != "document.md":
                output.write(artifact, artifact.name)
    st.download_button(
        "Download ZIP", archive.getvalue(), "document.zip", key=f"zip-{index}"
    )
