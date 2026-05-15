#!/usr/bin/env bash
# Verificacion amplia del ambiente de desarrollo para ValleSec Lab.
# Revisa herramientas, daemon, RAM, disco, permisos y puerto de la plataforma.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/common.sh"

load_env
validate_port

LOG_DIR="$ROOT_DIR/logs"
REPORT_FILE="$LOG_DIR/environment_report.txt"
mkdir -p "$LOG_DIR"

{
  echo "=== Reporte de ambiente - ValleSec Lab ==="
  date
  echo "Proyecto: $PROJECT_NAME"
  echo "Slug: $PROJECT_SLUG"
  echo "Entorno: $APP_ENV"
  echo "Puerto de plataforma: $PLATFORM_PORT"
  echo

  if command -v docker >/dev/null 2>&1; then
    ok "Docker encontrado: $(docker --version)"
  else
    fail "Docker no esta instalado. Ejecuta scripts/install_docker_ubuntu.sh o instala Docker manualmente."
  fi

  if docker compose version >/dev/null 2>&1; then
    ok "Docker Compose disponible: $(docker compose version)"
  else
    fail "Docker Compose no esta disponible."
  fi

  if docker info >/dev/null 2>&1; then
    ok "Daemon de Docker operativo."
  else
    warn "Docker esta instalado pero el daemon no responde. Verifica systemctl status docker y tus permisos."
  fi

  if [ "$(id -u)" -ne 0 ] && getent group docker >/dev/null 2>&1; then
    if id -nG | tr ' ' '\n' | grep -qx docker; then
      ok "Usuario actual pertenece al grupo docker."
    else
      warn "Usuario actual no pertenece al grupo docker. Puede requerir sudo para ejecutar contenedores."
    fi
  fi

  ram_gb=$(free -g | awk '/^Mem:/ {print $2}')
  if [ "${ram_gb:-0}" -ge 15 ]; then
    ok "RAM detectada: ${ram_gb} GB"
  else
    warn "RAM detectada: ${ram_gb} GB. Recomendado: 16 GB o mas."
  fi

  free_gb=$(df -BG "$ROOT_DIR" | awk 'NR==2 {gsub("G","",$4); print $4}')
  if [ "${free_gb:-0}" -ge 20 ]; then
    ok "Espacio libre detectado: ${free_gb} GB"
  else
    warn "Espacio libre detectado: ${free_gb} GB. Recomendado: al menos 20 GB para la base."
  fi

  if command -v ss >/dev/null 2>&1; then
    if ss -ltn | awk '{print $4}' | grep -q ":${PLATFORM_PORT}$"; then
      warn "El puerto ${PLATFORM_PORT} ya esta en uso. Cambia PLATFORM_PORT en .env si es necesario."
    else
      ok "Puerto ${PLATFORM_PORT} libre para el smoke test."
    fi
  else
    warn "No se encontro el comando ss para validar puertos abiertos."
  fi

  if [ -f "$(smoke_dir)/docker-compose.yml" ]; then
    ok "Archivo docker-compose del smoke test presente."
  else
    fail "No existe scenarios/smoke/docker-compose.yml"
  fi

  ok "Verificacion finalizada."
} | tee "$REPORT_FILE"
