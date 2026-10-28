# User guide

## First-time setup

You need Windows, Python 3.12, `uv`, Docker Desktop with NVIDIA GPU access, and disk space for the model and container image. Setup requires internet access. Offline inference passed a synthetic-page test on an RTX 4060 Laptop GPU with 8 GB VRAM; other hardware and documents may behave differently.

Open PowerShell in the project directory and install dependencies:

```powershell
uv sync
```

Download the pinned model and postprocessing files:

```powershell
uv run python -c "from huggingface_hub import snapshot_download; snapshot_download('nvidia/Nemotron-3.5-Parse', revision='4035ffb1d8f8bafcdb867dfaf6f7514f101464f9', local_dir='.models/nemotron-3.5-parse', allow_patterns=['*.json','*.py','*.safetensors','*.jinja','nemotron_parse/**','LICENSE*','NOTICE*','TOKENIZER_ATTRIBUTION.md'], ignore_patterns=['reference/**'])"
```

Start Docker Desktop, then build the local worker image:

```powershell
docker build -f runtime/Dockerfile -t docflow-nim-local:dev .
```

Run `.\launch.cmd` or double-click `launch.cmd`. It starts Docker Desktop if needed, starts the worker, waits for the model, and launches the app at [http://127.0.0.1:8472](http://127.0.0.1:8472). The model and worker are currently required even for online mode.

## Convert documents

1. Choose **offline** or **online** in the sidebar. Offline sends pages to the local worker; online sends them to NVIDIA. There is no automatic fallback.
2. Upload PDFs or supported images. Files are limited to 200 MiB and documents to 500 pages.
3. For one file, select the first and last page, inclusive and starting at 1. Set the last page to `0` for all remaining pages. Multiple files are processed sequentially, using all pages.
4. Select **Convert** and inspect the Preview, Markdown, Annotated, and JSON tabs. A partial-conversion warning means a page failed or was truncated.
5. Download Markdown, JSON, or ZIP. ZIPs include saved page images, annotations, and generated files, including HTML and chunks when available. A retried partial conversion can leave older files in its result directory, so check annotations against the current JSON result.

Conversions are saved under `conversion_results/`. Choose a saved conversion in the sidebar and select **Open saved conversion** to view it. Complete results can be reused for the same input, mode, and page selection. Incomplete results are processed again.

For online mode, make `NVIDIA_API_KEY` available to the process before starting the launcher. The sidebar shows whether it is present, not whether it is valid. Keep the value out of project files, screenshots, and logs. Saved JSON and page images contain document content; protect that directory accordingly.

To check presence without displaying the key:

```powershell
if ([string]::IsNullOrWhiteSpace($env:NVIDIA_API_KEY)) { 'Missing' } else { 'Present' }
```

If the key was configured outside the current terminal, reopen the terminal before launching the app.

## Troubleshooting

- **Local model stopped or loading:** run `launch.cmd`, wait for readiness, and select **Refresh readiness**. If startup fails, inspect `docker logs --tail 20 docflow-nim-worker`.
- **Model files missing:** repeat the pinned download above. Both modes need the postprocessing files in `.models/nemotron-3.5-parse`.
- **Docker or GPU unavailable:** start Docker Desktop and check GPU access with `docker run --rm --gpus all docflow-nim-local:dev nvidia-smi`.
- **Online key missing or rejected:** check the process environment and NVIDIA account access without printing the key. Restart the launcher after changing environment variables.
- **Partial conversion:** inspect page errors in Annotated or JSON. Correct the problem and convert again.
- **Port already in use:** close the conflicting app or select a free port when starting Streamlit manually. Do not stop unrelated processes.

See the [developer guide](developer-guide.md) for implementation details and diagnostics.

Image inputs have a 40-megapixel limit per frame, checked before RGB conversion. Rebuild the local worker after updating its code, using the root-context Docker command above.

## Use your NVIDIA API key in the Space

Select **My NVIDIA API key**, enter your key in the masked field, then parse your documents. Only Nemotron-3.5-Parse is supported. Requests pass through the Space to NVIDIA and use your NVIDIA quota without allocating ZeroGPU. Existing file and page limits apply.

The key stays in the current page session for repeated conversions. Clear key, confirmed Clear documents and results, or a page refresh removes it. The app does not write it to disk, exports, logs, cookies or browser local storage. Switching processing modes hides the field but retains its value. NVIDIA authentication or quota failures never trigger automatic fallback to Space GPU.

The local Streamlit app continues to read its server-side NVIDIA_API_KEY environment variable.
