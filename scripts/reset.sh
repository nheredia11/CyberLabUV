#!/usr/bin/env bash
# Reinicia el smoke test sin tocar el resto del proyecto.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/common.sh"

load_env
validate_port

cd "$(smoke_dir)"
docker compose --env-file "$ROOT_DIR/.env" down
docker compose --env-file "$ROOT_DIR/.env" up -d

ok "Smoke test reiniciado."
