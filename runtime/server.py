"""Local-only, serialized Nemotron inference service."""

import io
import threading

import torch
from fastapi import FastAPI, HTTPException, UploadFile
from PIL import Image
from transformers import AutoModel, AutoProcessor, GenerationConfig

app = FastAPI()
lock = threading.Lock()
model = (
    AutoModel.from_pretrained(
        "/model", trust_remote_code=True, local_files_only=True, dtype=torch.bfloat16
    )
    .to("cuda")
    .eval()
)
processor = AutoProcessor.from_pretrained(
    "/model", trust_remote_code=True, local_files_only=True
)
config = GenerationConfig.from_pretrained("/model", local_files_only=True)
config.max_new_tokens = 8744


@app.get("/health")
def health():
    return {"ready": True}


@app.post("/v1/parse")
def parse(document: UploadFile):
    data = document.file.read(100 * 1024**2 + 1)
    if len(data) > 100 * 1024**2:
        raise HTTPException(413, "Image too large")
    try:
        with Image.open(io.BytesIO(data)) as source:
            image = source.convert("RGB")
    except Exception:
        raise HTTPException(422, "Invalid image") from None
    prompt = (
        "</s><s><predict_bbox><predict_classes><output_markdown><predict_text_in_pic>"
    )
    with lock, torch.inference_mode():
        inputs = processor(
            images=[image], text=prompt, return_tensors="pt", add_special_tokens=False
        ).to("cuda")
        try:
            outputs = model.generate(**inputs, generation_config=config)
            content = processor.batch_decode(outputs, skip_special_tokens=False)[0]
            tokens = outputs.shape[-1]
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            raise HTTPException(503, "Insufficient GPU memory") from None
    return {
        "content": content,
        "finish_reason": "length" if tokens >= config.max_new_tokens else "stop",
        "usage": {"output_tokens": tokens},
    }
