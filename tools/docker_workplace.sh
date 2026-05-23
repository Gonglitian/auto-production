#!/bin/bash
# tools/docker_workplace.sh — init/build/shell into project-local Docker env.
set -u
CMD=${1:-init}
REPO="${AUTO_PRODUCTION_REPO:?need AUTO_PRODUCTION_REPO}"
NAME=${PROJECT_NAME:-$(basename "$(pwd)")}

case "$CMD" in
  init)
    [ -f Dockerfile ]    || cp "$REPO/templates/Dockerfile" .
    [ -f compose.yaml ]  || cp "$REPO/templates/compose.yaml" .
    [ -f .env ] || cat > .env <<EOF
PROJECT_NAME=$NAME
CUDA_VISIBLE_DEVICES=0
DATA_DIR=./data
CKPT_DIR=./ckpts
EOF
    echo "✅ Dockerfile + compose.yaml + .env ready (project=$NAME)"
    echo "Next: edit Dockerfile (base image / requirements.txt) → ./tools/docker_workplace.sh build"
    ;;
  build)
    docker compose build dev
    ;;
  shell)
    docker compose run --rm dev bash
    ;;
  *)
    echo "usage: $0 {init|build|shell}"; exit 2 ;;
esac
