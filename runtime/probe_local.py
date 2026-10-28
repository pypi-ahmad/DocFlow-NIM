"""Run a synthetic page on the local GPU without network access."""

import torch
from PIL import Image, ImageDraw
from transformers import AutoModel, AutoProcessor, GenerationConfig

path = "/model"
assert torch.cuda.is_available(), "CUDA unavailable"
model = (
    AutoModel.from_pretrained(
        path, trust_remote_code=True, local_files_only=True, dtype=torch.bfloat16
    )
    .to("cuda")
    .eval()
)
processor = AutoProcessor.from_pretrained(
    path, trust_remote_code=True, local_files_only=True
)
page = Image.new("RGB", (800, 600), "white")
ImageDraw.Draw(page).text(
    (50, 60), "DocFlow test invoice\nTotal: 42.00", fill="black", font_size=32
)
prompt = "</s><s><predict_bbox><predict_classes><output_markdown><predict_text_in_pic>"
inputs = processor(
    images=[page], text=prompt, return_tensors="pt", add_special_tokens=False
).to("cuda")
config = GenerationConfig.from_pretrained(path, local_files_only=True)
config.max_new_tokens = 1024
with torch.inference_mode():
    output = model.generate(**inputs, generation_config=config)
print(processor.batch_decode(output, skip_special_tokens=False)[0])
print("Peak allocated GiB:", torch.cuda.max_memory_allocated() / 1024**3)
