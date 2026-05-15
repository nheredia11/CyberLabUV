#!/usr/bin/env bash
# Instalacion de Docker para Ubuntu o Debian usando el repositorio oficial.
# Debe ejecutarse solo en maquinas donde Docker aun no este instalado.

set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "[ERROR] Ejecuta este script con sudo o como root."
  exit 1
fi

if [ ! -r /etc/os-release ]; then
  echo "[ERROR] No fue posible identificar la distribucion Linux."
  exit 1
fi

. /etc/os-release
DISTRO_ID="${ID:-}"
VERSION_CODENAME="${VERSION_CODENAME:-}"

case "$DISTRO_ID" in
  ubuntu|debian) ;;
  *)
    echo "[ERROR] Este script solo soporta Ubuntu o Debian. Detectado: ${DISTRO_ID:-desconocido}."
    exit 1
    ;;
esac

if [ -z "$VERSION_CODENAME" ]; then
  echo "[ERROR] No fue posible identificar VERSION_CODENAME."
  exit 1
fi

echo "[INFO] Actualizando indice de paquetes..."
apt-get update

echo "[INFO] Instalando dependencias base..."
apt-get install -y ca-certificates curl gnupg lsb-release

echo "[INFO] Creando carpeta de keyrings..."
install -m 0755 -d /etc/apt/keyrings

echo "[INFO] Descargando clave oficial de Docker..."
curl -fsSL "https://download.docker.com/linux/${DISTRO_ID}/gpg" | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "[INFO] Configurando repositorio oficial para ${DISTRO_ID} (${VERSION_CODENAME})..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${DISTRO_ID} ${VERSION_CODENAME} stable" \
  | tee /etc/apt/sources.list.d/docker.list >/dev/null

echo "[INFO] Instalando Docker Engine y Docker Compose plugin..."
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "[INFO] Habilitando servicio Docker..."
systemctl enable docker
systemctl start docker

echo "[INFO] Agregando al usuario invocador al grupo docker..."
if [ -n "${SUDO_USER:-}" ]; then
  usermod -aG docker "$SUDO_USER"
  echo "[WARN] Cierra sesion y vuelve a entrar para aplicar el grupo docker a $SUDO_USER."
else
  echo "[WARN] No se detecto SUDO_USER; valida manualmente si el usuario final quedo en el grupo docker."
fi

echo "[OK] Docker instalado."
docker --version
docker compose version
