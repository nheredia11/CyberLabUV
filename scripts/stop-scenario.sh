#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/common.sh"

SCENARIO_NAME=${1:-}
[ -n "$SCENARIO_NAME" ] || fail "Debes indicar el escenario. Ejemplo: bash scripts/stop-scenario.sh recon"

load_env
SCENARIO_DIR=$(scenario_dir "$SCENARIO_NAME")
[ -d "$SCENARIO_DIR" ] || fail "No existe el escenario: $SCENARIO_NAME"
[ -f "$SCENARIO_DIR/docker-compose.yml" ] || fail "El escenario $SCENARIO_NAME no tiene docker-compose.yml"

info "Deteniendo escenario: $SCENARIO_NAME"
cd "$SCENARIO_DIR"
docker compose --env-file "$ROOT_DIR/.env" down --remove-orphans
ok "Escenario $SCENARIO_NAME detenido"
