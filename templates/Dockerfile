# Default per-project Dockerfile for auto-production.
# Customize the CUDA / Python base; the rest is convention.
FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3-pip python3.11-venv \
    git curl wget tmux htop nvtop \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Project's pip lockfile (override by mounting); empty by default
COPY requirements.txt* /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt 2>/dev/null || true

# auto-production env
ENV AUTO_PRODUCTION_REPO=/opt/auto-production
RUN git clone --depth 1 https://github.com/Gonglitian/auto-production.git $AUTO_PRODUCTION_REPO 2>/dev/null || true

ENTRYPOINT ["/bin/bash"]
