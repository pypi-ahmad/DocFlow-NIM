"""Preview the actual Gradio interface on CPU, without loading the model.

Run: uv run --with gradio==6.31.0 python scripts/preview_ui.py
Add --stress to inspect the upload component with synthetic filenames.
"""

import argparse
import sys
import tempfile
from pathlib import Path

import gradio as gr
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from docflow.space_ui import prepare
from gradio_ui import CSS, THEME, build_demo, upload_panel


def preview_only(state, backend="Space GPU", api_key=""):
    """Keep the preview from silently invoking any inference service."""
    raise gr.Error(
        "UI preview only. Open the Hugging Face app or launch.cmd to parse documents."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stress", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="docflow-ui-") as directory:
        if args.stress:
            root = Path(directory)
            names = [
                "receipt.png",
                "quarterly-report-" + "a" * 60 + ".png",
                "تقرير-NVIDIA-2026.png",
                "Résumé-東京.png",
                "invoice-05.png",
            ]
            for name in names:
                Image.new("RGB", (20, 20), "white").save(root / name)
            scenarios = [
                ("Empty · 320px", 320, None),
                ("One document · 320px", 320, [str(root / names[0])]),
                (
                    "Five documents, long and multilingual filenames · 320px",
                    320,
                    [str(root / name) for name in names],
                ),
                ("One document · 1200px", 1200, [str(root / names[0])]),
            ]
            widths = ""
            with gr.Blocks(title="DocFlow upload stress test") as demo:
                gr.Markdown(
                    "# Upload panel stress test\nSynthetic files only. Tab through the controls; also check dark mode and 200% zoom. Parsing is disconnected."
                )
                for index, (label, width, files) in enumerate(scenarios):
                    gr.Markdown(
                        f"## {label}\nVisual observation: not verified in this session."
                    )
                    with gr.Column(
                        min_width=0,
                        elem_id=f"scenario-{index}",
                        elem_classes="workspace-panel",
                    ):
                        upload_panel(files)
                    widths += f"#scenario-{index} {{ width: {width}px; max-width: 100%; flex: none; }}\n"
            css = CSS + widths
        else:
            demo = build_demo(prepare, preview_only)
            css = CSS
        demo.queue().launch(
            server_name="127.0.0.1",
            server_port=7861 if args.stress else 7860,
            theme=THEME,
            css=css,
            inbrowser=False,
            max_file_size="50mb",
        )
