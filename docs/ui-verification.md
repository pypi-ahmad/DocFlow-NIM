# UI verification

Scope: the Hugging Face Gradio upload-to-export layout and the local Streamlit conversion screen. Backend inference and deployment are unchanged. Existing security fixes remain in place.

## Changes

- Upload controls and results occupy separate panels, stacked by the frameworks at narrow widths.
- One primary parsing action, clear page-range instructions and an explicit empty state guide the flow.
- System fonts avoid additional font downloads. The layout uses fewer heading sizes and comfortable text spacing.
- Matching teal accents, neutral surfaces and light/dark colors replace default styling.
- The Gradio layout is separate from model initialization so it can be previewed on CPU.

## Coverage

| Domain | Inspected | Limit |
| --- | --- | --- |
| Accessibility | Native labeled controls, image alt text, default keyboard/focus behavior retained; no custom animation | Keyboard, screen-reader and forced-color walks not verified |
| Layout | Source ordering, wrapping rules, panel minimum widths and actual stress harness configuration | Rendered 320px, 200% zoom and RTL layout not verified |
| Writing | Upload, page-range, processing, empty-state and export wording | Source checked |
| Typography | System font stacks, heading hierarchy, line height, wrapping and 16px Gradio inputs | Actual font rendering not verified |
| Colors | Declared primary button and Streamlit text/surface pairs | Rendered colors and framework defaults not measured |
| UI polish | Theme radii, component grouping and native state handling | Hover, focus, loading and error appearance not visually verified |

## Observed checks

- `uv run python -m pytest tests -q`: 13 passed. Root discovery includes copied audit fixtures and fails collection; the application tests are scoped explicitly.
- `uv run ty check docflow`: passed.
- Ruff checks on the changed UI Python files passed with `BLE001` excluded for the existing Streamlit broad exception handler.
- Streamlit AppTest: empty state and switching to NVIDIA API mode loaded without exceptions.
- Gradio 6.31.0: the actual layout built with 35 components and four event dependencies. Both local preview configuration endpoints returned HTTP 200.
- Calculated declared contrast: light primary button 5.47:1; dark primary button 9.78:1. Streamlit configured text/surface pairs range from 13.35:1 to 17.85:1. These values describe declared pairs, not browser measurements.

## Upload stress page

The harness imports the real `upload_panel` component. Scenarios cover empty and single uploads at 320px, five synthetic files with long and multilingual names at 320px, and one upload at 1200px. It does not load production state or call inference. Loading/error fixtures were omitted because this component does not accept those states as inputs.

Visual observation was skipped because no browser surface was available. No visual breaks or comprehensive visual approval are claimed. Open `http://127.0.0.1:7861` after starting the stress preview, tab through the controls, and check dark mode and browser zoom. The page remains available until its preview process is stopped.
