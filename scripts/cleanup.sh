#!/usr/bin/env bash
# Detiene el smoke test y limpia recursos temporales del escenario minimo.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/common.sh"

load_env
validate_port

cd "$(smoke_dir)"
docker compose --env-file "$ROOT_DIR/.env" down --remove-orphans

ok "Smoke test detenido y recursos temporales limpiados."
