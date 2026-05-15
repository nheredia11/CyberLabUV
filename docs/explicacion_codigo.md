# Explicacion del codigo incluido

## 1. `.env.example`
Este archivo concentra variables basicas del proyecto:
- `PROJECT_NAME`: nombre visible del prototipo;
- `PROJECT_SLUG`: nombre corto para contenedores y recursos;
- `PLATFORM_PORT`: puerto local del smoke test;
- `APP_ENV`: modo de ejecucion.

La ventaja es que el proyecto queda mas mantenible y listo para cambiar valores sin tocar todos los scripts.

## 2. `docker-compose.yml`
El compose del smoke test tiene varias partes importantes:

### Servicio `ui-smoke`
- Usa `nginx:alpine` porque es una imagen ligera y estable.
- Publica el puerto local para poder abrir la pagina desde el navegador.
- Monta la carpeta `landing/` como volumen de solo lectura para servir una pagina estatica.
- Tiene `healthcheck` para saber si el contenedor realmente responde.
- Usa `restart: unless-stopped` para mejorar resiliencia durante desarrollo.

### Servicio `worker-smoke`
- Simula un proceso auxiliar de plataforma.
- Escribe latidos de vida en un volumen compartido.
- Sirve para demostrar que el entorno puede manejar mas de un servicio.

### Red `valleseclab_net`
- Aisla los servicios del smoke test.
- Anticipa el uso de redes separadas por escenario mas adelante.

### Volumen `shared_data`
- Sirve como ejemplo de persistencia compartida.
- Luego podra aprovecharse para logs, evidencias o archivos de salida.

## 3. `check-requirements.sh`
Este script aplica varias buenas practicas:
- activa `set -euo pipefail` para detectar errores temprano;
- define funciones de salida (`ok`, `warn`, `fail`) para hacer la lectura mas clara;
- verifica que `docker` exista como comando;
- comprueba que Docker Compose este disponible;
- valida que el daemon de Docker responda;
- mide RAM y espacio libre;
- revisa si el puerto de la plataforma ya esta ocupado;
- escribe un reporte en `logs/environment_report.txt`.

## 4. `bootstrap-project.sh`
Su funcion es estandarizar la estructura del repositorio. Esto es importante porque un trabajo de grado necesita trazabilidad y organizacion. El script crea carpetas para:
- documentacion;
- logs;
- datos;
- modulos;
- resultados;
- escenarios;
- assets.

## 5. `init.sh`
Este script es la puerta de entrada del entorno de desarrollo.

Hace cuatro cosas:
1. Verifica si existe el archivo `.env`.
2. Llama a `bootstrap-project.sh` para garantizar estructura.
3. Lanza el smoke test con `docker compose up -d`.
4. Muestra mensajes claros sobre que revisar despues.

## 6. `status.sh`
Sirve para mostrar avance real a tutores o en pruebas internas porque entrega:
- lista de servicios del compose;
- resultado de salud del contenedor web;
- sugerencia de URL para validacion manual.

## 7. `verify-smoke.sh`
Automatiza la evidencia tecnica. Si la pagina local responde, guarda un archivo en `logs/` y deja una traza concreta de que el entorno estaba operativo.

## 8. `reset.sh` y `cleanup.sh`
Separar estas acciones es util porque no siempre quieres destruir el proyecto completo:
- `reset.sh` reinicia el escenario minimo;
- `cleanup.sh` apaga y limpia recursos temporales.

## 9. Modulo `M00_induccion`
Aunque el objetivo de esta entrega es el ambiente de desarrollo, se incluyo un modulo pedagogico minimo para que el repositorio ya refleje dos ideas que pidieron los tutores:
- parte teorica inicial;
- puntos de comprobacion.

Este modulo no cambia el proyecto. Solo demuestra que la estructura del repositorio ya puede alojar teoria, checkpoints y encuesta dentro del mismo simulador.

## 10. Nuevos scripts para escenarios
### `list-scenarios.sh`
Lista escenarios que ya tienen `docker-compose.yml` y ayuda a mostrar madurez del repositorio.

### `run-scenario.sh`
Permite iniciar un escenario puntual sin mezclarlo con el smoke test. Esto es importante porque la tesis plantea laboratorios modulares y reproducibles.

### `stop-scenario.sh`
Detiene un escenario especifico para mantener orden operativo y evitar residuos de pruebas.

### `status-scenarios.sh`
Resume el estado de los escenarios definidos y sirve para demos tecnicas ante tutor.

## 11. Nuevos modulos y escenarios
### `platform/scenario_catalog.json`
Centraliza un catalogo basico que luego puede usarse tanto en interfaz como en backend.

### `S01_reconocimiento`
Modulo inicial para descubrimiento de servicios en una red Docker aislada.

### `S02_autenticacion_http`
Incluye una aplicacion propia de laboratorio, pensada para demostrar una interfaz real del simulador sin depender aun de escenarios mas complejos.

### `S03_web_basico`
Deja una plantilla lista para consolidar practicas OWASP en una siguiente iteracion.
