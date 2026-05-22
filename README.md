# CyberLabUV / ValleSec Lab

Prototipo funcional de simulador académico de ciberseguridad con dos capas principales:

- **Backend FastAPI + SQLite** para módulos, checkpoints, encuestas, eventos de escenarios y analíticas docentes.
- **Frontend React + Vite** con dashboard del estudiante, ruta de aprendizaje, práctica local, resultados, panel docente, modo claro/oscuro y vistas alineadas con los bocetos del trabajo de grado.

## Estructura principal

```text
backend/                 API FastAPI
frontend/                Interfaz React
platform/modules/        Contenidos Markdown, checkpoints y encuestas
scenarios/               Escenarios Docker del laboratorio
scripts/                 Operación local y verificación del entorno
data/                    Base SQLite local
```

## Ejecutar en desarrollo

```bash
bash scripts/run-platform.sh
```

Servicios:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Documentación API: http://localhost:8000/docs

## Ejecutar sin Docker

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Usuarios demo

- Estudiante: `ana.rodriguez@uv.edu.co`
- Docente: `carlos.m@uv.edu.co`

## Endpoints principales

- `GET /api/modules`
- `GET /api/students/ana/dashboard`
- `POST /api/modules/{module_id}/checkpoints`
- `POST /api/modules/{module_id}/surveys`
- `POST /api/scenarios/action`
- `GET /api/teacher/analytics`

## Seguridad operacional

Por defecto, las acciones sobre escenarios se registran en modo seguro (`ALLOW_SCENARIO_COMMANDS=false`). Para permitir ejecución real de scripts Docker desde la API, define:

```bash
ALLOW_SCENARIO_COMMANDS=true
```

Úsalo solo en un equipo local controlado.
