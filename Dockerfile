# Meridian image (AEA-50; docs/design/contracts/stage7/data.md section 7). Stages: web -> index -> runtime.
# No ARG or ENV holds a secret; secrets are Railway variables (gauntlet-hosting-default).
ARG NODE_VERSION=24

# --- web: apps/web's own build, only when apps/web/package.json exists (DAT-21, AEA-50-1). Reads apps/web and the
# one OpenAPI file; writes nothing back. Dev dependencies stay (tsc -b type-checks tests; prebuild regenerates types).
FROM node:${NODE_VERSION}-bookworm-slim AS web
WORKDIR /src/apps/web
COPY apps/web/ /src/apps/web/
COPY docs/ux/03-structure/ui-contracts.openapi.yaml /src/docs/ux/03-structure/ui-contracts.openapi.yaml
RUN mkdir -p /out \
 && if [ -f package.json ]; then \
      npm ci && npm run build && npm run check:dist && cp -a dist /out/dist; \
    else \
      echo "web stage: no apps/web/package.json, frontend build skipped"; \
    fi

# --- base: Python 3.12 and the locked dependencies (no dev group).
# The official python image sets ENV GPG_KEY (a public key id), which AC-4's name check forbids and no later stage can
# unset, so the same interpreter (3.12, as requires-python says) is copied onto a plain Debian base with the shared libraries it links against.
FROM debian:bookworm-slim AS base
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates netbase tzdata libbz2-1.0 libffi8 liblzma5 libncursesw6 \
      libreadline8 libsqlite3-0 libssl3 libuuid1 zlib1g libgomp1 \
 && rm -rf /var/lib/apt/lists/*
COPY --from=python:3.12-slim-bookworm /usr/local/ /usr/local/
RUN ldconfig
COPY --from=ghcr.io/astral-sh/uv:0.12.16 /uv /usr/local/bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    FASTEMBED_CACHE_PATH=/opt/fastembed \
    PATH=/app/.venv/bin:$PATH
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src/ ./src/
RUN uv sync --locked --no-dev

# --- index: WF-14. Builds /app/index with the ingest CLI (data.md section 3) and caches the embedding model.
FROM base AS index
COPY docs/data/issued/meridian_dataset/knowledge_base/ /build/knowledge_base/
COPY data/kb_transcriptions/ /build/kb_transcriptions/
RUN python -m meridian.retrieval.ingest \
      --kb-dir /build/knowledge_base \
      --transcriptions-dir /build/kb_transcriptions \
      --out-dir /app/index

# --- runtime: code, issued dataset (read-only), index, model cache, web dist when built, eval reports, BUILD_SHA.
FROM base AS runtime
ENV HF_HUB_OFFLINE=1 \
    MERIDIAN_DATA_DIR=/data \
    MERIDIAN_INDEX_DIR=/app/index \
    MERIDIAN_WEB_DIST_DIR=/app/apps/web/dist \
    PORT=8080
COPY docs/data/issued/meridian_dataset/ /app/docs/data/issued/meridian_dataset/
COPY --from=index /opt/fastembed /opt/fastembed
COPY --from=index /app/index /app/index
COPY --from=web /out/ /app/apps/web/
COPY scripts/ /app/scripts/
RUN --mount=type=bind,source=.,target=/ctx \
    mkdir -p /app/eval/reports /data \
 && if [ -d /ctx/eval/reports ]; then cp -a /ctx/eval/reports/. /app/eval/reports/; fi \
 && if [ -f /ctx/BUILD_SHA ]; then cp /ctx/BUILD_SHA /app/BUILD_SHA; else echo 'WARNING: no BUILD_SHA in the build context; agent_version reads RAILWAY_GIT_COMMIT_SHA at run time or else unknown' >&2; fi \
 && chmod -R a-w /app/docs/data/issued
EXPOSE 8080
CMD ["sh", "-c", "MERIDIAN_AGENT_VERSION=\"$(python -m scripts.agent_version)\" && export MERIDIAN_AGENT_VERSION && exec uvicorn --factory scripts.serve:create_deployed_app --host 0.0.0.0 --port \"$PORT\" --workers 1 --log-config scripts/log_config.json --no-access-log --timeout-keep-alive 75"]
