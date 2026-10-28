# Repository Guidelines

## Workspace scope

Keep project work in this repository. Store research reports in `docs/`. The separate DocLayout repository is reference material; do not write deliverables there unless explicitly requested.

## Project structure and current state

The repository contains application code in `docflow/`, the Streamlit entry point `streamlit_app.py`, backend tests in `tests/`, local GPU runtime files in `runtime/`, and research in `docs/`. Dependencies are managed by `pyproject.toml` and `uv.lock`. Local code-index metadata lives in `.code-review-graph/` and `.codegraph/`. See `README.md` for implemented features and remaining work.

Treat index databases and process files as tooling metadata; do not edit them as application code. When source files become available, update this guide with the actual module layout and entry points. Do not infer the implementation language or architecture from the directory name.

## Agreed application scope

Plan a standalone Python/Streamlit app based on DocLayout's conversion workflow. Use only `nvidia/Nemotron-3.5-Parse` for model inference; exclude OpenAI models and PP-DocLayoutV3.

- Keep document uploads, supported input conversions, page selection, batch processing, previews, layout annotations, exports, and saved results.
- Exclude document chat, classification, and business-field extraction, including their screens and backend logic. Do not retain manual versions of those features.
- Offline mode runs the model locally. After initial setup, it must work without network access and must never fall back to online inference automatically.
- Online mode uses NVIDIA's hosted model with the existing `NVIDIA_API_KEY` environment variable, read server-side. Never copy the key into project files or expose it in the UI or logs.

Normalize both backends into a shared document structure for previews and exports. Include backend, model version when available, page selection, and conversion settings in cache identity.

Implementation is underway. Hosted and local inference have passed synthetic-page smoke checks. Verify compatibility on the target GPU and representative documents. Use `uv` for Python environments and dependencies. Preserve applicable license notices when reusing reference code.

## Build, test, and development commands

Use `uv sync` for setup, `launch.cmd` for the UI, `uv run python -m pytest -q` for tests, and `uv run ty check docflow` for type checks. Inspect the workspace with:

- `Get-ChildItem -Force`: list root files, including hidden directories.
- `rg --files --hidden`: find files beneath the workspace.

Once project configuration exists, document the verified setup, run, and validation commands here. Include required runtime versions and prerequisites before asking contributors to execute them.

## Coding style and naming conventions

No language-specific style, indentation rules, formatter, or linter is established yet. Follow existing source conventions when code is added. Keep changes focused and avoid unrelated reformatting. Use descriptive names and document any adopted formatting rules alongside their configuration.

## Testing guidelines

Tests use pytest in `tests/test_*.py`; no coverage threshold is configured. Add focused checks that demonstrate intended behavior and relevant failures. Report checks actually run and explain verification limits.

## Commit and pull request guidelines

Use short, imperative commit subjects describing one change. Pull requests should explain the purpose, scope, and validation results; link relevant issues and include screenshots for visible interface changes.

## Security and configuration

Keep credentials out of source files, examples, and logs. Use configured environment variables for secrets. Preserve unrelated local files and request explicit authorization before destructive filesystem or Git operations.

The public Gradio Space also accepts visitor-supplied NVIDIA API keys as request-local credentials. Never put visitor keys in environment variables, shared globals, document state, caches, logs or exports. Space GPU remains the default; both routes use only Nemotron-3.5-Parse.
