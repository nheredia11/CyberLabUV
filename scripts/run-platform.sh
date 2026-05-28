#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

COMPOSE_FILE="docker-compose.dev.yml"

# CyberLabUV launcher for Linux/WSL/Git Bash.
# Supports both Docker Compose v2 (docker compose) and legacy docker-compose.
if docker compose version >/dev/null 2>&1; then
  echo "[CyberLab] Using Docker Compose v2: docker compose"
  docker compose -f "$COMPOSE_FILE" up --build
elif command -v docker-compose >/dev/null 2>&1; then
  echo "[CyberLab] Using legacy Docker Compose: docker-compose"
  docker-compose -f "$COMPOSE_FILE" up --build
else
  cat <<'MSG'
[CyberLab] Docker Compose is not available in this shell.

Try one of these options:
1) From PowerShell, run:
   docker compose version
   docker compose -f docker-compose.dev.yml up --build

2) If you use WSL, enable WSL Integration in Docker Desktop:
   Docker Desktop > Settings > Resources > WSL Integration > enable your distro.

3) On Ubuntu/WSL, install the Compose plugin:
   sudo apt update
   sudo apt install docker-compose-plugin

MSG
  exit 1
fi
