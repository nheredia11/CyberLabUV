```markdown
# CyberLabUV: Simulador Ciberseguridad Interactivo Basado en Contenedores

> **Trabajo de Grado / Tesis de Pregrado**  
> **Fecha de Sustentación:** 9 de noviembre de 2026  
> **Institución:** Universidad del Valle (UV)  
> **Espacio de Investigación:** 📓 [Cyber NDH](https://gemini.google.com/notebook/37f6661e-22ee-42c4-90f0-e3a88893c250)

---

## 📋 Descripción del Proyecto

**CyberLabUV** es una plataforma educativa de ciberseguridad basada en microservicios contenerizados (Docker). Su objetivo principal es ofrecer un entorno de prácticas controlado, seguro y reproducible donde estudiantes de ingeniería puedan ejecutar laboratorios prácticos de reconocimiento de red, análisis de autenticación HTTP/servicios y mitigación de vulnerabilidades (OWASP Top 10), alineado con marcos de referencia internacionales como **MITRE ATT&CK**, **NIST CSF** y **ASVS 4.0.3**.

La arquitectura está compuesta por un backend robusto en **FastAPI**, una interfaz moderna y reactiva en **React / Vite**, persistencia relacional en **SQLite** y un motor dinámico de orquestación mediante **Docker Compose v2**.

---

## 🛠️ Stack Tecnológico

* **Backend**: Python 3.11 + FastAPI, Uvicorn, Pytest, ReportLab (generación de reportes PDF).
* **Frontend**: Node.js 20 + React, Vite, TailwindCSS, DOMPurify (sanitización XSS).
* **Base de Datos**: SQLite con control de concurrencia y transacciones ACID.
* **Orquestación y Prácticas**: Docker & Docker Compose v2, contenedores atacantes aislados (`alpine:3.21` con `nmap`, `curl`, `hydra`, etc.).

---

## ⚙️ Prerrequisitos (Guía de Inicio en 15 Minutos en Windows + WSL 2)

Para desplegar y ejecutar el simulador localmente en Windows, asegúrate de contar con:
1. **Windows 10 / 11** con **WSL 2** habilitado.
2. **Docker Desktop** instalado y configurado con el motor WSL 2 activo (icono en verde en la barra de tareas).
3. **Git** y **PowerShell** o Bash.

---

## 🚀 Despliegue Rápido de la Plataforma

Sigue estos pasos en tu terminal para levantar el sistema completo:

1. **Clonar y acceder al repositorio**:
   ```powershell
   git clone <url-del-repositorio>
   cd CyberLabUV

```

2. **Configurar las Variables de Entorno**:
Crea un archivo `.env` en la raíz (o copia el de ejemplo) configurando tus credenciales y parámetros de desarrollo:
```env
APP_ENV=development
ENABLE_DEV_LOGIN=true
ALLOW_SCENARIO_COMMANDS=true
TEACHER_EMAILS=dev@uv.edu.co,docente@uv.edu.co
GOOGLE_CLIENT_ID=tu-google-client-id.apps.googleusercontent.com
PILOT_SALT=tu-salto-seguro-para-anonimizacion

```


3. **Iniciar la plataforma con Docker Compose**:
```powershell
bash scripts/run-platform.sh

```


*(O alternativamente con Docker Compose directo:* `docker compose -f docker-compose.dev.yml up --build`*)*
4. **Acceder a los servicios**:
* **Frontend (Interfaz de Usuario)**: [http://localhost:5173](http://localhost:5173)
* **Backend API (Swagger Docs)**: [http://localhost:8000/docs](http://localhost:8000/docs) *(Deshabilitado en modo producción por seguridad)*



---

## 🧪 Pruebas Automatizadas y Calidad de Código

Para verificar que toda la lógica del backend, los middleware de seguridad y los flujos de escenarios pasen correctamente las pruebas unitarias e de integración:

```powershell
# Activar entorno virtual de Python
& .venv\Scripts\Activate.ps1

# Ejecutar pytest con PYTHONPATH configurado
$env:PYTHONPATH="backend"
pytest tests/ -v

```

Para verificar la compilación del frontend:

```powershell
cd frontend
npm install
npm run build

```

---

## 🔍 Solución de Problemas Frecuentes (Troubleshooting)

* **Error de conexión WSL/Docker (`Bash/Service/0x8007274c`)**:
* Ejecuta en PowerShell: `wsl --shutdown` y asegúrate de que Docker Desktop esté completamente iniciado antes de reintentar.


* **Contenedores huérfanos o bloqueos de sesión**:
* Limpia los contenedores residuales de práctica ejecutando:
```powershell
docker ps -a --filter "name=session_"
docker compose ls

```


* Si es necesario, fuerza la limpieza con: `docker rm -f <container_id>`


* **Permisos de `docker.sock**`:
* Asegúrate de que Docker Desktop permita la comunicación mediante el socket en entornos WSL.



---

## 📂 Estructura del Repositorio

```text
CyberLabUV/
├── backend/              # API FastAPI, modelos, esquemas y lógica de negocio
├── frontend/             # Interfaz de usuario React + Vite
├── scenarios/            # Definiciones Docker Compose de los laboratorios (S01-S05)
├── scripts/              # Scripts de automatización de despliegue y limpieza
├── tests/                # Suite de pruebas unitarias y de integración (pytest)
└── docs/tesis/           # Documentación formal académica de sustentación

```

---

## 📄 Licencia y Autoría

Desarrollado para optar al título de Ingeniería de Sistemas en la **Universidad del Valle**. Todos los derechos reservados © 2026.

```

```