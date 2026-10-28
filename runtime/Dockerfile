FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv
WORKDIR /runtime
RUN uv init --bare --python 3.12 --vcs none && uv add 'transformers==5.14.1' 'torchvision==0.26.0' 'timm==1.0.22' pillow beautifulsoup4 fastapi uvicorn python-multipart
COPY runtime/probe_local.py /runtime/probe_local.py
COPY runtime/server.py /runtime/server.py
COPY docflow/image_limits.py /runtime/docflow/image_limits.py
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
CMD ["uv", "run", "--no-sync", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
