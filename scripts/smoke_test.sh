#!/usr/bin/env bash
set -e

BASE_URL="http://localhost:8000"
echo "[SmokeTest] Iniciando pruebas de humo en CyberLabUV..."

# 1. Health check
curl -f "$BASE_URL/health" || exit 1

# 2. Login dev docente / estudiante
TOKEN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "estudiante@uv.edu.co", "role": "student"}' | grep -o '"token":"[^"]*' | grep -o '[^"]*$')

if [ -z "$TOKEN" ]; then
  echo "[Error] No se pudo obtener el token de acceso."
  exit 1
fi

# 3. Aceptar Consentimiento
curl -s -X POST "$BASE_URL/api/consent" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"accepted": true, "version": "1.0"}'

# 4. Iniciar Escenario S01
curl -s -X POST "$BASE_URL/api/scenarios/S01/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "estudiante", "action": "start"}'

# 5. Ejecutar comando permitido
curl -s -X POST "$BASE_URL/api/scenarios/S01/command" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "estudiante", "scenario_id": "S01", "command": "nmap -p 22 localhost"}'

# 6. Enviar Checkpoint
curl -s -X POST "$BASE_URL/api/checkpoints/submit" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"student_id": "estudiante", "module_id": "S01", "checkpoint_id": "CP1", "status": "completed", "evidence": "nmap output"}'

# 7. Descargar PDF
curl -s -I "$BASE_URL/api/students/estudiante/report.pdf" \
  -H "Authorization: Bearer $TOKEN" | grep "application/pdf" || exit 1

# 8. Detener Escenario
curl -s -X POST "$BASE_URL/api/scenarios/S01/stop" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "estudiante", "action": "stop"}'

echo "[SmokeTest] ¡Todas las pruebas de humo pasaron exitosamente!"