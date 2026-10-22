#!/usr/bin/env bash
# Recreate the isolated AEA rehearsal container (aea-demo-rec) from the existing image.
#
#   ops/rehearsal-container.sh             stop + remove the old container, start a new one
#   ops/rehearsal-container.sh --dry-run   show the plan and key status; change nothing
#
# Provider keys (ANTHROPIC_API_KEY, OPENROUTER_API_KEY) come only from the shared workspace file
# via ../bin/with-provider-env and reach docker by name, never by value. Project settings come
# from this project's .env (provider keys in it are ignored). This does not rebuild the image:
#   docker build -t meridian:demo-rec .        # no credentials are involved in the build
# Works from any directory. Render uses its own environment group and is not touched.
set -euo pipefail

ROOT=$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)
LAUNCHER="$ROOT/../bin/with-provider-env"
NAME=aea-demo-rec
IMAGE=meridian:demo-rec
HOST_PORT=18431
DATA_DIR=${AEA_REHEARSAL_DATA:-/tmp/aea-demo-rec/data}
# The only project settings the rehearsal container receives (anything else in .env stays local).
PROJECT_KEYS='MERIDIAN_DEMO_USERNAME|MERIDIAN_DEMO_PASSWORD|MERIDIAN_SESSION_SECRET|MERIDIAN_LLM_MODEL|MERIDIAN_FAST_MODEL|MERIDIAN_DAILY_SPEND_CAP_USD'

DRY=0; [[ ${1:-} == "--dry-run" ]] && DRY=1

# The session secret is a project setting. Create it once so recreating keeps sessions valid.
if ! grep -qE '^MERIDIAN_SESSION_SECRET=.' "$ROOT/.env"; then
  if (( DRY )); then echo "would generate MERIDIAN_SESSION_SECRET in $ROOT/.env"
  else printf 'MERIDIAN_SESSION_SECRET=%s\n' "$(openssl rand -hex 32)" >> "$ROOT/.env"; echo "generated MERIDIAN_SESSION_SECRET in project .env"; fi
fi

if (( DRY )); then
  echo "container=$NAME image=$IMAGE port=127.0.0.1:$HOST_PORT->8080 data=$DATA_DIR"
  echo "project keys passed: ${PROJECT_KEYS//|/ }"
  echo "provider keys passed by name only: ANTHROPIC_API_KEY OPENROUTER_API_KEY"
  exec "$LAUNCHER" --check
fi

recreate() {
  local sel
  sel="$(dirname "$PROJECT_ENV_FILTERED")/selected.env"
  grep -E "^(${PROJECT_KEYS})=" "$PROJECT_ENV_FILTERED" > "$sel"
  mkdir -p "$DATA_DIR"
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  docker run -d --name "$NAME" \
    --env-file "$sel" \
    -e ANTHROPIC_API_KEY -e OPENROUTER_API_KEY \
    -e MERIDIAN_COOKIE_SECURE=false -e MERIDIAN_REQUIRE_FRONTEND=true \
    -p "127.0.0.1:$HOST_PORT:8080" \
    -v "$DATA_DIR:/data" \
    "$IMAGE" >/dev/null
  for _ in $(seq 1 60); do
    if curl -fsS "http://127.0.0.1:$HOST_PORT/healthz" >/dev/null 2>&1; then
      echo "$NAME is healthy at http://127.0.0.1:$HOST_PORT"; return 0
    fi
    sleep 1
  done
  echo "$NAME did not become healthy in 60 s; see: docker logs $NAME" >&2; return 1
}

# Validation happens before the old container is touched: a blank key leaves it running.
export -f recreate
export ROOT NAME IMAGE HOST_PORT DATA_DIR PROJECT_KEYS
exec "$LAUNCHER" --project-env "$ROOT/.env" -- bash -c recreate
