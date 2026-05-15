#!/usr/bin/env bash
# Inicializacion del ambiente base.
# 1) Garantiza estructura.
# 2) Genera .env si no existe.
# 3) Valida configuracion.
# 4) Levanta el smoke test.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/common.sh"

bash "$ROOT_DIR/scripts/bootstrap-project.sh"
load_env
validate_port

mkdir -p "$ROOT_DIR/logs" "$ROOT_DIR/data" "$ROOT_DIR/assets" "$ROOT_DIR/platform/results"

cd "$(smoke_dir)"
docker compose --env-file "$ROOT_DIR/.env" config >/dev/null
docker compose --env-file "$ROOT_DIR/.env" up -d

ok "Smoke test iniciado."
info "Ejecuta ahora: bash scripts/status.sh"
info "Luego verifica en navegador: $(smoke_url)"
