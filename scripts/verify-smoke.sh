#!/usr/bin/env bash
# Verifica la pagina del smoke test y guarda evidencia local.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/common.sh"

load_env
validate_port

LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"
STAMP=$(date +%Y%m%d_%H%M%S)
OUT_FILE="$LOG_DIR/smoke_check_${STAMP}.html"
HDR_FILE="$LOG_DIR/smoke_check_${STAMP}.headers.txt"

if curl -fsS --max-time 10 -D "$HDR_FILE" "$(smoke_url)" > "$OUT_FILE"; then
  ok "Smoke test verificado. Evidencia HTML: $OUT_FILE"
  ok "Cabeceras HTTP guardadas en: $HDR_FILE"
else
  fail "No fue posible verificar el smoke test en $(smoke_url)"
fi
