---
name: docker-workplace
description: "每个 project 一个 Dockerfile + GPU pinning via .env，环境彻底隔离。避免 conda env 互相污染。Use when user says \"docker\", \"docker workplace\", \"容器化\", \"env 隔离\", \"GPU pin\", \"Dockerfile\"."
argument-hint: "[--init | --build | --shell]"
allowed-tools: Bash(*), Read, Write
---

# /docker-workplace — Per-Project Docker Env

> 借鉴 AI-Researcher Docker workplace pattern。

## Overview

`Dockerfile` + `.env` + `compose.yaml`，固定：

- Python / CUDA / cuDNN / nccl 版本
- pip lockfile
- GPU pinning (CUDA_VISIBLE_DEVICES via env)
- mount: source / data / output

## Workflow

`--init`：

```bash
cp $AUTO_PRODUCTION_REPO/templates/Dockerfile .
cp $AUTO_PRODUCTION_REPO/templates/compose.yaml .
# user 改 base image / cuda version
```

`--build`：`docker build -t myproj:latest .`
`--shell`：`docker compose run --rm dev bash`

启动后 conda / pip 都在容器内，host 不污染。

## Output

- `Dockerfile` / `compose.yaml` / `.env`
- 容器镜像 `<project>:latest`

## Composition

- METHOD gate 软推荐（不强制——pure conda 也行）
- `/cross-host-sync` 记录 conda_env 字段时填 docker image tag
