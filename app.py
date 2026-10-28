"""Gradio entry point for Hugging Face ZeroGPU Spaces."""
import spaces  # Must precede torch and other CUDA imports.
# ruff: noqa: I001
import gradio as gr
import torch
from huggingface_hub import snapshot_download
from transformers import AutoModel, AutoProcessor, GenerationConfig
from pathlib import Path

from docflow.backends import MODEL_REVISION, PageResult
from docflow.conversion import MODEL, convert
from docflow.space_ui import bundle, prepare, view
from gradio_ui import CSS, THEME, build_demo

snapshot_download("nvidia/Nemotron-3.5-Parse", revision=MODEL_REVISION, local_dir=MODEL)
model = AutoModel.from_pretrained(MODEL, trust_remote_code=True,
                                dtype=torch.bfloat16).to("cuda").eval()
processor = AutoProcessor.from_pretrained(MODEL, trust_remote_code=True)
config = GenerationConfig.from_pretrained(MODEL)
config.max_new_tokens = 8744


def parse(image):
    """Run the pinned model directly on the allocated Space GPU."""
    prompt = "</s><s><predict_bbox><predict_classes><output_markdown><predict_text_in_pic>"
    with torch.inference_mode():
        inputs = processor(images=[image], text=prompt, return_tensors="pt",
                           add_special_tokens=False).to("cuda")
        output = model.generate(**inputs, generation_config=config)
        tokens = output.shape[-1]
        return PageResult(processor.batch_decode(output, skip_special_tokens=False)[0],
                          "length" if tokens >= config.max_new_tokens else "stop",
                          {"output_tokens": tokens}, "space-gpu")


def preflight(files, first, last, state):
    """Reject invalid workloads before the GPU event."""
    try:
        return prepare(files, first, last, state)
    except (ValueError, OSError) as exc:
        raise gr.Error(str(exc)) from None


@spaces.GPU(duration=120)
def run(state: dict, progress=gr.Progress()):  # noqa: B008 -- Gradio progress injection
    """Convert up to five pages; all returned state is CPU data."""
    results = []
    for index, job in enumerate(state["jobs"]):
        path = Path(job["path"])
        progress(index / len(state["jobs"]), desc=f"Parsing {path.name}")
        results.append(convert(path.read_bytes(), path.name, "space-gpu",
                               job["first"], job["last"], page_parser=parse,
                               output_root=Path(state["job_root"]) / str(index)))
    state["results"] = [(result, str(directory)) for result, directory in results]
    archive = bundle(results, Path(state["job_root"]) / "documents.zip")
    choices = [(f"{i + 1}. {result['name']}", str(i)) for i, (result, _) in enumerate(results)]
    return state, gr.Dropdown(choices=choices, value="0"), archive, *view(state, "0")


demo = build_demo(preflight, run)

if __name__ == "__main__":
    demo.queue().launch(max_file_size="50mb", theme=THEME, css=CSS)
