"""Document rendering and common Nemotron output processing."""

import hashlib
import importlib
import io
import json
import sys
from pathlib import Path
from typing import Any

import bleach
import markdown2
import pypdfium2 as pdfium
from PIL import Image, ImageDraw

from docflow.backends import MODEL_REVISION, parse_page
from docflow.image_limits import check_image_size

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / ".models" / "nemotron-3.5-parse"


def _page_indexes(count, first, last):
    if count > 500:
        raise ValueError("Maximum document length is 500 pages.")
    if first < 1 or (last is not None and last < first):
        raise ValueError("Invalid page selection.")
    return range(first - 1, min(count, last if last is not None else count))


def page_count(data, filename):
    """Inspect page metadata without rasterizing pages or creating RGB copies."""
    if len(data) > 200 * 1024**2:
        raise ValueError("Maximum file size is 200 MiB.")
    if Path(filename).suffix.lower() == ".pdf":
        with pdfium.PdfDocument(data) as pdf:
            count = len(pdf)
    else:
        with Image.open(io.BytesIO(data)) as image:
            check_image_size(image.size)
            count = getattr(image, "n_frames", 1)
    _page_indexes(count, 1, None)
    return count


def page_images(data, filename, first=1, last=None):
    """Render selected pages only, preserving their order in the document."""
    if len(data) > 200 * 1024**2:
        raise ValueError("Maximum file size is 200 MiB.")
    if Path(filename).suffix.lower() == ".pdf":
        with pdfium.PdfDocument(data) as pdf:
            for index in _page_indexes(len(pdf), first, last):
                page = pdf[index]
                try:
                    scale = min(1664 / page.get_width(), 2048 / page.get_height())
                    bitmap = page.render(scale=scale)
                    try:
                        yield bitmap.to_pil().convert("RGB")
                    finally:
                        bitmap.close()
                finally:
                    page.close()
    else:
        with Image.open(io.BytesIO(data)) as image:
            count = getattr(image, "n_frames", 1)
            for index in _page_indexes(count, first, last):
                image.seek(index)
                check_image_size(image.size)
                page = image.convert("RGB")
                page.thumbnail((1664, 2048))
                yield page


def convert(data, filename, mode, first=1, last=None, progress=None, *,
            page_parser=None, output_root=None):
    if first < 1 or (last is not None and last < first):
        raise ValueError("Invalid page selection.")
    if not (MODEL / "postprocessing.py").is_file():
        raise ValueError("Run model setup to install the pinned NVIDIA postprocessor.")
    if str(MODEL) not in sys.path:
        sys.path.insert(0, str(MODEL))
    postprocess_document = importlib.import_module(
        "postprocessing"
    ).postprocess_document

    identity = hashlib.sha256(
        data + json.dumps([mode, MODEL_REVISION, first, last, 1]).encode()
    ).hexdigest()
    directory = (Path(output_root) if output_root is not None else ROOT / "conversion_results") / identity
    saved = directory / "document.json"
    if saved.exists():
        result = json.loads(saved.read_text(encoding="utf-8"))
        if result["complete"]:
            return result, directory
    directory.mkdir(parents=True, exist_ok=True)
    pages: list[dict[str, Any]] = []
    for number, image in enumerate(page_images(data, filename, first, last), first):
        image.save(directory / f"page-{number}.png")
        try:
            raw = page_parser(image) if page_parser is not None else parse_page(image, mode)
            parsed = postprocess_document(raw.content, image_size=image.size)
            item = {
                "number": number,
                "raw": raw.content,
                "finish_reason": raw.finish_reason,
                "usage": raw.usage,
                "complete": raw.complete,
                **parsed,
            }
            annotated = image.copy()
            draw = ImageDraw.Draw(annotated)
            for block in parsed["blocks"]:
                box = block.get("bbox_pixels")
                if box and len(box) == 4:
                    draw.rectangle(box, outline="red", width=2)
            annotated.save(directory / f"annotated-{number}.png")
        except Exception as exc:
            item = {
                "number": number,
                "complete": False,
                "error": str(exc),
                "markdown": "",
                "blocks": [],
            }
        pages.append(item)
        if progress:
            progress(number)
    if not pages:
        raise ValueError("No pages matched the selection.")
    result = {
        "name": Path(filename).name,
        "backend": mode,
        "local_model_revision": MODEL_REVISION if mode in ("offline", "space-gpu") else None,
        "complete": all(p["complete"] for p in pages),
        "pages": pages,
    }
    saved.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    markdown = "\n\n---\n\n".join(page["markdown"] for page in pages)
    (directory / "document.md").write_text(markdown, encoding="utf-8")
    html = bleach.clean(
        str(markdown2.markdown(markdown, extras=["tables", "fenced-code-blocks"])),
        tags={
            "p",
            "br",
            "strong",
            "em",
            "h1",
            "h2",
            "h3",
            "h4",
            "table",
            "thead",
            "tbody",
            "tr",
            "td",
            "th",
            "pre",
            "code",
            "ul",
            "ol",
            "li",
            "blockquote",
        },
        attributes={"td": ["rowspan", "colspan"], "th": ["rowspan", "colspan"]},
        strip=True,
    )
    (directory / "document.html").write_text(
        '<!doctype html><html><head><meta charset="utf-8"><title>Document</title></head><body>'
        + html
        + "</body></html>",
        encoding="utf-8",
    )
    chunks = [
        {"page": page["number"], **block} for page in pages for block in page["blocks"]
    ]
    (directory / "chunks.json").write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result, directory
