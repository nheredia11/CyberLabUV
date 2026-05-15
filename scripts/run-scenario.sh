#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/common.sh"

SCENARIO_NAME=${1:-}
[ -n "$SCENARIO_NAME" ] || fail "Debes indicar el escenario. Ejemplo: bash scripts/run-scenario.sh recon"

load_env
SCENARIO_DIR=$(scenario_dir "$SCENARIO_NAME")
[ -d "$SCENARIO_DIR" ] || fail "No existe el escenario: $SCENARIO_NAME"
[ -f "$SCENARIO_DIR/docker-compose.yml" ] || fail "El escenario $SCENARIO_NAME no tiene docker-compose.yml"

info "Iniciando escenario: $SCENARIO_NAME"
info "Directorio: $SCENARIO_DIR"
cd "$SCENARIO_DIR"
docker compose --env-file "$ROOT_DIR/.env" config >/dev/null
docker compose --env-file "$ROOT_DIR/.env" up -d
ok "Escenario $SCENARIO_NAME iniciado"
