# Nemotron 3.5 Parse research

Researched on 2026-10-28. Requested sources: [NVIDIA Build](https://build.nvidia.com/nvidia/nemotron-3.5-parse) and [NVIDIA's Hugging Face model repository](https://huggingface.co/nvidia/Nemotron-3.5-Parse). No inference requests, model downloads, installation, or application changes were performed.

## What it is

Nemotron 3.5 Parse combines document text extraction with layout classes, bounding boxes, reading order, tables, and chart-aware output. NVIDIA positions it as a single-model page parser. That role is broader than a layout detector. [NIM overview](https://docs.nvidia.com/nim/ingestion/parse/latest/overview.html)

The exact model is `nvidia/Nemotron-3.5-Parse` on Hugging Face and `nvidia/nemotron-3.5-parse` in NIM. The model card reports 630,800,496 unique trainable parameters, including its multi-token-prediction head; architecture combines C-RADIOv4-SO400M with a 10-layer mBART decoder. The card dates the release October 17, 2026. [NVIDIA model card](https://huggingface.co/nvidia/Nemotron-3.5-Parse)

NIM release 2.4 instead calls it a 650M model and introduces the standalone `nvcr.io/nim/nvidia/nemotron-parse` container. The container name is not a model-version identifier: this release serves 3.5 only. Its new document API replaces the older VLM NIM chat-completions interface. [Release notes](https://docs.nvidia.com/nim/ingestion/parse/latest/release-notes.html)

## Inputs, outputs, and limits

The standalone NIM accepts one PNG/JPEG page per multipart `POST /v1/parse` request, uploaded as `document`. PDFs must be rasterized first. It accepts neither page arrays nor several pages stitched together. Both image dimensions must be at least 17 pixels; preprocessing fits content within 1664 pixels wide by 2048 high, preserving aspect ratio. The complete request is limited to 100 MiB. [API usage](https://docs.nvidia.com/nim/ingestion/parse/latest/use-the-api.html)

Its JSON response contains `content`, `finish_reason`, and output-token usage. Content mixes text/formatting with coordinate and class tokens; it is not already clean Markdown or DocLayout block JSON. Coordinates span 0–1 relative to the image: multiply x by width and y by height. The default and maximum output limit is 9,000 tokens; requests can lower it. [API usage](https://docs.nvidia.com/nim/ingestion/parse/latest/use-the-api.html)

The NIM owns prompts and sampling. Detection-only mode is unsupported. This differs from custom model serving and matters if the intended change is only replacing PP-DocLayoutV3. [Migration guide](https://docs.nvidia.com/nim/ingestion/parse/latest/overview.html#migrate-from-the-vlm-nim)

NVIDIA's postprocessing helpers produce document Markdown and structured blocks. HTML/hierarchical JSON preserve merged table cells; flat Markdown, CSV, and record JSON flatten spans. Chart processing can split numeric/percentage columns and associate captions, so preserve raw output when comparing postprocessing choices. [Postprocessing documentation](https://huggingface.co/nvidia/Nemotron-3.5-Parse/blob/main/docs/postprocessing.md)

## Deployment and access

| Route | Verified considerations |
| --- | --- |
| Hosted Build service | The public page advertises a free endpoint and API-key access. Public-page availability is not proof that an authenticated request succeeds. Quotas and production pricing were not verified. [Build page](https://build.nvidia.com/nvidia/nemotron-3.5-parse) |
| Standalone NIM | Version 2.4 uses Docker with an NVIDIA-capable runtime. NVIDIA's Windows workstation instructions require WSL2. Weights can come from NGC or Hugging Face and be cached. [Getting started](https://docs.nvidia.com/nim/ingestion/parse/latest/getting-started.html) |
| Custom model serving | The repository documents its own vLLM plugin and serving configuration. An OpenAI-compatible custom server is distinct from the standalone NIM API; do not transplant older chat examples into `/v1/parse`. [Serving guide](https://huggingface.co/nvidia/Nemotron-3.5-Parse/blob/main/docs/serving.md) |

The current NIM support matrix lists A100 80GB, A10G, GB200, H100, L40S, and RTX PRO 6000 Blackwell Server Edition in BF16. This does not establish compatibility with an unspecified consumer GPU. [Support matrix](https://docs.nvidia.com/nim/ingestion/parse/latest/support-matrix.html)

NVIDIA measures roughly 4.3–5.18 GiB GPU memory after startup/warmup at batch capacity one; inference can consume more. High-throughput configurations reserve substantially more memory. Page latency depends on content, token limits, and concurrency, so model parameter count alone is insufficient for sizing. [Performance and memory](https://docs.nvidia.com/nim/ingestion/parse/latest/performance.html)

## Quality and documentation caveats

A `length` finish reason can mean truncated content; there is no continuation API. Even `stop` does not certify complete extraction. NVIDIA suggests improved images or separate crops for oversized outputs, with manual checks for omissions and duplication. Queue overload can return 503; queue/inference timeout can return 504. [Troubleshooting](https://docs.nvidia.com/nim/ingestion/parse/latest/troubleshoot.html)

Published numbers differ across official pages. The API model reference reports ParseBench 69.05 at 14.21 pages/second in its reference BF16 setup. [API model reference](https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3_5-parse)

The current Hugging Face card reports a higher triple-pass result, with separate full-page, detection, and crop-refinement work. These are different published configurations; neither establishes accuracy on this project's forms. [Model card](https://huggingface.co/nvidia/Nemotron-3.5-Parse)

Model weights use OpenMDW 1.1. The Hugging Face card identifies the tokenizer as MIT, while NVIDIA's API model reference says CC-BY-4.0. This inconsistency remains unresolved; check the exact downloaded revision's attribution files before distribution. [Model card](https://huggingface.co/nvidia/Nemotron-3.5-Parse), [API model reference](https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3_5-parse)

Hosted trial and downloaded container terms are separate from weight licensing. [NIM governing terms](https://docs.nvidia.com/nim/ingestion/parse/latest/eula.html)

## Fit with DocLayout

Current DocLayout combines PP-DocLayoutV3 layout analysis with a whole-page Luna/Sol reading request, then reconciles geometry and preserves model text. Field extraction consumes saved Markdown and evidence metadata separately. [Conversion walkthrough](codebase-research-2026-10-28.md), [document builder](../../DocLayout/doclayout/builders/document.py#L52), [field retry](../../DocLayout/doclayout/ui/batch.py#L195)

Inference: Nemotron is a candidate alternative parsing backend covering both layout and transcription. It would require an adapter for semantic classes, coordinates, Markdown/tables, page IDs, provenance, and error statuses. It does not itself establish the project's business-field extraction contract. Retain that downstream boundary when evaluating it.

A useful evaluation would run the same representative pages through both parsers and compare omissions, identifiers/dates, checkboxes, merged tables, reading order, evidence geometry, latency, and resource cost. Preserve the current converter until that evidence supports a change. This research authorizes no pipeline replacement.

## Research checks

Context7 resolved NVIDIA NIM documentation, but its fetched snippets concerned unrelated LLM/speech APIs. The linked primary Parse sources were therefore read directly. Current model identity, native API, deployment limits, and conflicting documentation were checked; hosted service operation, local GPU compatibility, and comparative accuracy remain untested.

## Does Nemotron require PP-DocLayoutV3?

No. Nemotron 3.5 Parse supplies both text and layout annotations itself. NVIDIA documents the standalone NIM as a single-model page parser, so PP-DocLayoutV3 is not a required dependency. PDFs still need rasterization, and the response needs postprocessing. [NIM overview](https://docs.nvidia.com/nim/ingestion/parse/latest/overview.html)

The optional reference pipelines also do not require PP-DocLayoutV3. Double pass reparses table/chart crops identified by the full-page prediction. Triple pass adds detection, but its source sends the detection prompt to the same served Nemotron model and endpoint; it does not invoke a separate Paddle detector. [Pipeline instructions](https://huggingface.co/nvidia/Nemotron-3.5-Parse/blob/main/reference/parsebench/pipeline/README.md), [request implementation](https://huggingface.co/nvidia/Nemotron-3.5-Parse/blob/main/reference/parsebench/pipeline/run.py)

These multipass examples use custom vLLM serving. Native NIM does not expose detection-only requests. Start with Nemotron alone; adding a separate layout detector would be a custom design choice requiring evidence of benefit. [NIM migration guidance](https://docs.nvidia.com/nim/ingestion/parse/latest/overview.html#migrate-from-the-vlm-nim)
