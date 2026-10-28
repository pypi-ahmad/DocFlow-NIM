---
title: DocFlow NIM
sdk: gradio
sdk_version: 6.31.0
python_version: "3.12"
app_file: app.py
short_description: Parse PDFs and images with NVIDIA Nemotron
---

# DocFlow NIM

**Live Gradio app:** [DocFlow NIM on Hugging Face](https://huggingface.co/spaces/pypi-ahmad/DocFlow-NIM)

DocFlow NIM converts PDF pages and images into structured text using NVIDIA Nemotron-3.5-Parse. Choose local GPU inference or NVIDIA's hosted service in the Streamlit interface. The app is a work in progress.

## Start

Follow the [first-time setup](docs/user-guide.md#first-time-setup), then run `launch.cmd` and open [http://127.0.0.1:8472](http://127.0.0.1:8472). The launcher starts the local worker even when you intend to use online mode.

- [User guide](docs/user-guide.md): setup, conversion, downloads, and troubleshooting.
- [Developer guide](docs/developer-guide.md): architecture, files, and checks.
- [Model research](docs/nemotron-3.5-parse-research.md): sources and deployment context.

## Current capabilities

The app supports PDF, PNG, JPEG, GIF, TIFF, and WebP uploads, single-file page selection, sequential multi-file conversion, annotated page previews, Markdown and JSON downloads, and saved ZIP exports. New conversions also generate HTML and chunk files for the ZIP. Office inputs, concurrent batches, additional exports, a conversion CLI, and a public conversion API are unfinished. Chat, classification, and business-field extraction are excluded. The app uses neither OpenAI models nor PP-DocLayoutV3.

## Clone

Repository: [pypi-ahmad/DocFlow-NIM](https://github.com/pypi-ahmad/DocFlow-NIM)

```powershell
git clone https://github.com/pypi-ahmad/DocFlow-NIM.git
cd DocFlow-NIM
```

## Hugging Face Gradio Space

Create a Gradio Space at https://huggingface.co/new-space and select ZeroGPU hardware (subject to account eligibility). This app requires a GPU. No NVIDIA API key is needed.

Upload only the application files, replacing the repository ID:

```powershell
uv run hf upload YOUR_USERNAME/DocFlow-NIM . . --repo-type space --include "app.py" --include "gradio_ui.py" --include "requirements.txt" --include "README.md" --include "docflow/*.py"
```

Wait for the build and pinned model download, then upload documents and select Parse documents. Choose a document to inspect pages, Markdown, layout annotations, JSON, and exports, or download the batch ZIP. Up to five selected pages across five files are supported, with 50 MiB per file. Page ranges apply to single uploads; batches process all pages.

Documents run on Hugging Face servers. Session results are temporary. Clear removes session-owned output directories; framework-cached downloads follow Gradio's separate cleanup schedule. Never upload local model weights, credentials, caches, or conversion results. The Windows Streamlit app remains available through `launch.cmd`.

The initial GPU limit is 120 seconds. Quota exhaustion or timeouts may require signing in or submitting fewer pages. Live ZeroGPU checks passed for a synthetic image and a five-page PDF (about 12 and 30 seconds end to end). These small samples do not establish throughput for dense documents.

Image inputs are limited to 40 megapixels per frame before RGB expansion. PDF preflight reads page metadata; conversion renders only selected PDF pages and keeps their original page numbers.

## Use your NVIDIA API key in the Space

Select **My NVIDIA API key**, enter your key in the masked field, then parse your documents. Only Nemotron-3.5-Parse is supported. Requests pass through the Space to NVIDIA and use your NVIDIA quota without allocating ZeroGPU. Existing file and page limits apply.

The key stays in the current page session for repeated conversions. Clear key, confirmed Clear documents and results, or a page refresh removes it. The app does not write it to disk, exports, logs, cookies or browser local storage. Switching processing modes hides the field but retains its value. NVIDIA authentication or quota failures never trigger automatic fallback to Space GPU.

The local Streamlit app continues to read its server-side NVIDIA_API_KEY environment variable.

## Diagrams

Download a diagram HTML file and open it in your browser to explore it. Each diagram includes source links pinned to the application revision it describes. The JSON source is stored beside each HTML file.

- [Architecture](.archify/suite-docflow-20261028-202145/architecture/architecture.html)
- [Workflow](.archify/suite-docflow-20261028-202145/workflow/workflow.html)
- [Sequence](.archify/suite-docflow-20261028-202145/sequence/sequence.html)
- [Dataflow](.archify/suite-docflow-20261028-202145/dataflow/dataflow.html)
- [Lifecycle](.archify/suite-docflow-20261028-202145/lifecycle/lifecycle.html)
