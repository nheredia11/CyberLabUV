#!/usr/bin/env bash
# Crea la estructura base del repositorio del simulador.
# Se puede ejecutar varias veces sin romper el proyecto.

set -euo pipefail
ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)

mkdir -p   "$ROOT_DIR/docs"   "$ROOT_DIR/logs"   "$ROOT_DIR/data"   "$ROOT_DIR/assets"   "$ROOT_DIR/platform/modules"   "$ROOT_DIR/platform/results"   "$ROOT_DIR/scenarios/smoke"   "$ROOT_DIR/scenarios/recon"   "$ROOT_DIR/scenarios/auth_http"   "$ROOT_DIR/scenarios/webapp"   "$ROOT_DIR/assets/ui"

echo "[OK] Estructura base del proyecto lista en: $ROOT_DIR"
