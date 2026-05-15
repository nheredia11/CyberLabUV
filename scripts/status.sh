#!/usr/bin/env bash
# Estado del ambiente base y del smoke test.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/common.sh"

load_env
validate_port

cd "$(smoke_dir)"

echo "=== Estado de servicios de ValleSec Lab ==="
docker compose --env-file "$ROOT_DIR/.env" ps

echo
echo "=== Validacion HTTP rapida ==="
if command -v curl >/dev/null 2>&1; then
  if curl -fsS --max-time 10 "$(smoke_url)" >/dev/null; then
    ok "La interfaz minima responde en $(smoke_url)"
  else
    warn "La interfaz minima no respondio todavia en $(smoke_url). Revisa logs o espera unos segundos."
  fi
else
  warn "curl no esta instalado; valida manualmente desde el navegador en $(smoke_url)."
fi
