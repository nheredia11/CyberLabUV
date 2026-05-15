#!/usr/bin/env bash
# Funciones comunes para scripts operativos de ValleSec Lab.

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

ok()   { echo "[OK] $1"; }
info() { echo "[INFO] $1"; }
warn() { echo "[WARN] $1"; }
fail() { echo "[ERROR] $1"; exit 1; }

ensure_env_file() {
  if [ ! -f "$ROOT_DIR/.env" ]; then
    if [ -f "$ROOT_DIR/.env.example" ]; then
      cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
      ok "Archivo .env creado a partir de .env.example"
    else
      fail "No existe .env ni .env.example en $ROOT_DIR"
    fi
  fi
}

load_env() {
  ensure_env_file
  set -a
  # shellcheck disable=SC1091
  . "$ROOT_DIR/.env"
  set +a

  : "${PROJECT_NAME:=ValleSecLab}"
  : "${PROJECT_SLUG:=valleseclab}"
  : "${PLATFORM_PORT:=8080}"
  : "${APP_ENV:=development}"
}

validate_port() {
  case "${PLATFORM_PORT}" in
    ''|*[!0-9]*) fail "PLATFORM_PORT debe ser numerico. Valor actual: ${PLATFORM_PORT}" ;;
  esac

  if [ "$PLATFORM_PORT" -lt 1 ] || [ "$PLATFORM_PORT" -gt 65535 ]; then
    fail "PLATFORM_PORT debe estar entre 1 y 65535. Valor actual: ${PLATFORM_PORT}"
  fi
}

smoke_dir() {
  printf '%s/scenarios/smoke' "$ROOT_DIR"
}

smoke_url() {
  printf 'http://localhost:%s' "$PLATFORM_PORT"
}

scenario_dir() {
  printf "%s/scenarios/%s" "$ROOT_DIR" "$1"
}
