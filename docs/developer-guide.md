# Developer guide

## Project layout

- `streamlit_app.py` implements the interface and ZIP assembly.
- `docflow/conversion.py` renders pages, invokes parsing, postprocesses results, and saves artifacts. `docflow/backends.py` selects the inference transport.
- `runtime/` contains the local GPU worker, its probe, and Dockerfile.
- `scripts/` contains worker startup and the synthetic hosted-service probe.
- `tests/` contains pytest tests. `docs/` contains guides and research.
- `.models/` holds the downloaded model; `conversion_results/` holds outputs. Both are ignored by Git and may contain large or sensitive files.

## Conversion flow

The UI prepares input bytes and page selection, then calls `convert`. PDF pages are rendered with PDFium; image frames are loaded with Pillow. Each page is sent to `parse_page` as PNG and processed with NVIDIA's downloaded `postprocessing.py`. Results include page text, blocks, bounding boxes, raw output, completion state, and available usage. Annotated PNGs draw the returned pixel bounding boxes.

Offline requests go to the worker at `127.0.0.1:8473`. Its `/health` endpoint reports readiness and `/v1/parse` accepts one uploaded page. The worker loads the pinned model locally and serializes inference with a lock. Online requests go to NVIDIA's hosted parse endpoint with the process `NVIDIA_API_KEY`. Never log the key or automatically switch modes after an error.

Results are stored in `conversion_results/<hash>/document.json`, alongside page images and generated files. The hash includes source bytes, mode, configured model revision, page range, and a format version. The hosted service's actual model version is not part of this cache key. Complete results are reused; incomplete results are processed again.

## Checks

Run from the project root:

```powershell
uv run python -m pytest -q
uv run ty check docflow
uv run ruff check --select E4,E7,E9,F,I docflow scripts tests streamlit_app.py
```

The optional hosted probe sends a generated synthetic image to NVIDIA and requires a configured key:

```powershell
uv run python scripts/probe_online.py
```

Check the worker with `docker logs --tail 20 docflow-nim-worker` and its health endpoint at `http://127.0.0.1:8473/health`. For setup and normal use, see the [user guide](user-guide.md).

## Boundaries

The model snapshot is pinned to `4035ffb1d8f8bafcdb867dfaf6f7514f101464f9`. Preserve NVIDIA's model and tokenizer notices when distributing their files. The Docker build resolves its dependencies during construction and has no separate runtime lockfile. The app is unfinished: see the [README](../README.md) for current scope. The neighboring DocLayout repository is reference material only.
