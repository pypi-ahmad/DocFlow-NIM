"""DocFlow NIM conversion interface."""

import io
import json
import os
from zipfile import ZIP_DEFLATED, ZipFile

import httpx
import streamlit as st

from docflow.conversion import ROOT, convert

st.set_page_config(
    page_title="DocFlow NIM", page_icon=":material/description:", layout="wide"
)

st.title("DocFlow NIM")

st.markdown("Turn documents into text you can use.")

st.caption(
    "Powered by NVIDIA Nemotron-3.5-Parse · Markdown, layout annotations and structured JSON"
)

st.sidebar.subheader("Processing")

st.session_state.setdefault("results", [])

mode = st.sidebar.segmented_control(
    "Inference mode",
    ["offline", "online"],
    default="offline",
    format_func=lambda mode: "Local GPU" if mode == "offline" else "NVIDIA API",
    selection_mode="single",
    required=True,
)

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

upload_column, results_column = st.columns([1, 2], gap="large")

with upload_column, st.container(border=True):
    st.subheader("1. Add documents")

    st.caption("Upload PDFs or images, then choose the pages to parse.")

    files = st.file_uploader(
        "Documents",
        type=["pdf", "png", "jpg", "jpeg", "gif", "tif", "tiff", "webp"],
        accept_multiple_files=True,
    )

    page_mode = st.radio("Pages", ["All pages", "Custom range"], horizontal=True)

    with st.form("convert", border=False):
        first, last = 1, 0

        if page_mode == "Custom range":
            st.caption(
                "Page range applies to one document. Multiple documents include all pages."
            )

            first = st.number_input("First page", min_value=1, value=1)

            last = st.number_input(
                "Last page",
                min_value=0,
                value=0,
                help="Set to 0 to include all remaining pages.",
            )

        submitted = st.form_submit_button(
            "Parse documents",
            type="primary",
            width="stretch",
            disabled=not files or not ready,
        )

    if not files:
        st.caption("Add at least one document to enable parsing.")

    if mode == "offline":
        st.caption("Documents are processed by your local model worker.")

    else:
        st.caption("Documents are sent to NVIDIA for processing.")

    st.caption("Images: up to 40 megapixels. Download results after reviewing them.")

with results_column:
    st.subheader("2. Review results")

    st.caption("Inspect parsed text and page layout, then download your exports.")

    results_area = st.container()

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

                st.error(
                    f"{exc} Check the document and processing service, then try again."
                )

saved = sorted((ROOT / "conversion_results").glob("*/document.json"))

if saved:
    selected = st.sidebar.selectbox(
        "Saved conversion", saved, format_func=lambda p: p.parent.name[:12]
    )

    if st.sidebar.button("Open saved conversion"):
        st.session_state.results = [
            (json.loads(selected.read_text(encoding="utf-8")), selected.parent)
        ]

with results_area:
    if st.session_state.results:
        with st.popover("Clear results"):
            st.write("Remove results from this view? Saved files stay on disk.")
            if st.button("Clear this view"):
                st.session_state.results = []
                st.rerun()
    if not st.session_state.results:
        with st.container(border=True):
            st.markdown("### Your parsed documents will appear here")

            st.markdown(
                "Add a document and select **Parse documents** to see its text, layout and downloads."
            )

    for index, (result, directory) in enumerate(st.session_state.results):
        st.subheader(result["name"])

        if result["complete"]:
            st.success(f"Complete · {len(result['pages'])} pages ready")

        if not result["complete"]:
            st.warning(
                "Some pages are incomplete. Open Annotated to inspect page errors, then retry those pages."
            )

        markdown = "\n\n---\n\n".join(page["markdown"] for page in result["pages"])

        preview, raw, annotated, structured = st.tabs(
            ["Preview", "Markdown", "Annotated", "JSON"]
        )

        with preview:
            page_index = st.selectbox(
                "Page",
                range(len(result["pages"])),
                format_func=lambda i, result=result: (
                    f"Page {result['pages'][i]['number']}"
                ),
                key=f"page-{index}",
            )

            page = result["pages"][page_index]

            source, text = st.columns(2, gap="medium")

            with source:
                image = directory / f"page-{page['number']}.png"

                if image.exists():
                    st.image(
                        str(image),
                        alt=f"Original page {page['number']}",
                        width="stretch",
                    )

                else:
                    st.info("Source preview unavailable for this saved result.")

            with text:
                if page.get("error"):
                    st.error(page["error"])

                st.markdown(page["markdown"])

        with raw:
            st.code(markdown, language="markdown")

        with annotated:
            for page in result["pages"]:
                image = directory / f"annotated-{page['number']}.png"

                if image.exists():
                    st.image(
                        str(image),
                        caption=f"Page {page['number']}",
                        alt=f"Detected layout for page {page['number']}",
                    )

                if page.get("error"):
                    st.error(page["error"])

        with structured:
            st.json(result)

        st.download_button(
            "Download Markdown", markdown, "document.md", key=f"md-{index}"
        )

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
            "Download all files · ZIP",
            archive.getvalue(),
            "document.zip",
            key=f"zip-{index}",
        )
