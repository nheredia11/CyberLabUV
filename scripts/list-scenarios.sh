#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)

printf 'Escenarios disponibles en %s\n\n' "$ROOT_DIR/scenarios"
for dir in "$ROOT_DIR"/scenarios/*; do
  [ -d "$dir" ] || continue
  name=$(basename "$dir")
  if [ -f "$dir/docker-compose.yml" ]; then
    printf ' - %s\n' "$name"
  fi
done
