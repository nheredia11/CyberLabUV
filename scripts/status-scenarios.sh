#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/common.sh"

load_env

echo '=== Escenarios con compose ==='
for dir in "$ROOT_DIR"/scenarios/*; do
  [ -d "$dir" ] || continue
  [ -f "$dir/docker-compose.yml" ] || continue
  name=$(basename "$dir")
  echo
  echo "--- $name ---"
  (cd "$dir" && docker compose --env-file "$ROOT_DIR/.env" ps) || warn "No fue posible consultar $name"
done
