"""Model-independent Gradio layout, shared by the Space and local UI preview."""

import gradio as gr

from docflow.space_ui import cleanup, view

THEME = gr.themes.Soft(
    primary_hue="teal",
    neutral_hue="slate",
    font=["Segoe UI", "Arial", "sans-serif"],
    font_mono=["Cascadia Code", "Consolas", "monospace"],
).set(
    button_primary_background_fill="#0f766e",
    button_primary_background_fill_hover="#115e59",
    button_primary_text_color="#ffffff",
    button_primary_background_fill_dark="#5eead4",
    button_primary_background_fill_hover_dark="#99f6e4",
    button_primary_text_color_dark="#042f2e",
)

CSS = """

.gradio-container { max-width: 1440px !important; margin-inline: auto; }

#app-header { padding-block: 12px 20px; }

#app-header h1 { font-size: clamp(1.75rem, 3vw, 2.25rem); letter-spacing: -.04em;

    line-height: 1.15; text-wrap: balance; }

#app-header p { max-width: 65ch; line-height: 1.6; }

.workspace-panel { padding: 24px !important; border-radius: 20px !important;

    border: 1px solid var(--border-color-primary); background: var(--block-background-fill); }

.workspace-panel h2 { font-size: 1.25rem; letter-spacing: -.02em; }

.workspace-panel p { line-height: 1.6; text-wrap: pretty; }

#result-markdown { max-width: 75ch; margin-inline: auto; padding: 16px; }

#result-markdown, .workspace-panel { overflow-wrap: anywhere; min-width: 0; }

#workspace { align-items: flex-start; gap: 24px; }

#upload-panel { flex-basis: 320px; }

#results-panel { flex-basis: 560px; }

#app-footer { padding-block: 16px; }

.gradio-container input, .gradio-container textarea { font-size: 16px !important; }

.gradio-container button { white-space: normal; }

.gradio-container input[type=number] { font-variant-numeric: tabular-nums; }

@media (max-width: 600px) {

    .workspace-panel { padding: 16px !important; border-radius: 16px !important; }

    #app-header { padding-block: 16px; }

}

"""


def upload_panel(files=None):
    """Render the real upload component without model or session dependencies."""

    gr.Markdown("## 1. Add documents\nUpload PDFs or images to get started.")

    uploads = gr.File(
        label="Documents",
        value=files,
        file_count="multiple",
        height=180,
        file_types=[".pdf", ".png", ".jpg", ".jpeg", ".gif", ".tif", ".tiff", ".webp"],
    )

    gr.Markdown(
        "**Up to 5 pages total** · 50 MiB per file · Images up to 40 megapixels"
    )

    page_mode = gr.Radio(
        ["All pages", "Custom range"], value="All pages", label="Pages"
    )

    with gr.Group(visible=False) as page_range:
        gr.Markdown(
            "For one document, choose a range. For multiple documents, all pages are included."
        )

        with gr.Row():
            first = gr.Number(
                value=1, precision=0, minimum=1, label="First page", min_width=100
            )

            last = gr.Number(
                value=0, precision=0, minimum=0, label="Last page", min_width=100
            )

        gr.Markdown("Set last page to **0** to include all remaining pages.")

    page_mode.change(
        lambda mode: (gr.Group(visible=mode == "Custom range"), 1, 0),
        page_mode,
        [page_range, first, last],
    )

    button = gr.Button("Parse documents", variant="primary")

    clear = gr.Button("Clear documents and results", size="sm", variant="stop")

    gr.Markdown(
        "Files are processed on Hugging Face. Results are temporary; download them before leaving."
    )

    return uploads, first, last, button, clear


def build_demo(preflight, run):
    """Build the complete UI with supplied conversion callbacks."""

    with gr.Blocks(delete_cache=(3600, 3600), title="DocFlow NIM") as demo:
        gr.Markdown(
            "# DocFlow NIM\nYour document workspace · NVIDIA Nemotron-3.5-Parse",
            elem_id="app-header",
        )

        state = gr.State(value={}, time_to_live=3600, delete_callback=cleanup)

        with gr.Row(elem_id="workspace"):
            with gr.Column(
                scale=2,
                min_width=260,
                elem_id="upload-panel",
                elem_classes="workspace-panel",
            ):
                uploads, first, last, button, clear = upload_panel()

            with gr.Column(
                scale=4,
                min_width=260,
                elem_id="results-panel",
                elem_classes="workspace-panel",
            ):
                gr.Markdown(
                    "## 2. Review results\nParsed pages and downloads appear here after conversion."
                )

                selection = gr.Dropdown(label="Document", choices=[], interactive=True)

                status = gr.Markdown(
                    "Add documents to start. Your parsed pages will appear here."
                )

                with gr.Tabs():
                    with gr.Tab("Review"):
                        gr.Markdown(
                            "Select a page thumbnail to read its text alongside the original."
                        )

                        with gr.Row():
                            with gr.Column(min_width=230):
                                preview = gr.Gallery(
                                    label="Source pages",
                                    columns=1,
                                    height=520,
                                    object_fit="contain",
                                    interactive=False,
                                )

                            with gr.Column(min_width=230):
                                markdown = gr.Markdown(
                                    sanitize_html=True, elem_id="result-markdown"
                                )

                    with gr.Tab("Layout"):
                        annotated = gr.Gallery(
                            label="Detected layout",
                            columns=2,
                            height=420,
                            object_fit="contain",
                        )

                    with gr.Tab("JSON"):
                        structured = gr.JSON(label="Structured document")

                with gr.Accordion(
                    "Download results", open=True, visible=False
                ) as exports:
                    downloads = gr.File(
                        label="Selected document · Markdown, HTML and JSON",
                        file_count="multiple",
                        interactive=False,
                    )

                    archive = gr.File(
                        label="All documents · ZIP archive", interactive=False
                    )

        gr.Markdown(
            "Powered by NVIDIA Nemotron-3.5-Parse · GPU quota or time limits may require fewer pages.",
            elem_id="app-footer",
        )

        outputs = [status, preview, markdown, annotated, structured, downloads]

        conversion = button.click(
            preflight, [uploads, first, last, state], state
        ).success(
            run,
            state,
            [state, selection, archive, *outputs],
            concurrency_limit=1,
            concurrency_id="model",
        )

        conversion.success(lambda: gr.Accordion(visible=True), outputs=exports)

        selection.input(view, [state, selection], outputs)

        def read_page(state, selection, event: gr.SelectData):

            result = state["results"][int(selection)][0]

            page = result["pages"][event.index]

            return page["markdown"]

        preview.select(read_page, [state, selection], markdown)

        with gr.Group(visible=False) as confirmation:
            gr.Markdown(
                "Clear these documents and results? Download any results you want to keep first."
            )

            confirm_clear = gr.Button("Clear documents and results", variant="stop")

            cancel_clear = gr.Button("Keep documents")

        clear.click(lambda: gr.Group(visible=True), outputs=confirmation)

        cancel_clear.click(lambda: gr.Group(visible=False), outputs=confirmation)

        def reset(state):
            """Remove session artifacts and clear visible results."""

            cleanup(state)

            return (
                {},
                None,
                gr.Dropdown(choices=[], value=None),
                None,
                "Ready. Add documents, then select Parse documents.",
                [],
                "",
                [],
                None,
                None,
            )

        confirm_clear.click(
            reset, state, [state, uploads, selection, archive, *outputs]
        ).then(
            lambda: (gr.Group(visible=False), gr.Accordion(visible=False)),
            outputs=[confirmation, exports],
        )

    return demo
