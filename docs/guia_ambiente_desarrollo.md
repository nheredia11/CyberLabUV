# Guia detallada de ambiente de desarrollo - ValleSec Lab

## 1. Objetivo
Esta guia convierte la tarea pendiente de "empezar a configurar el ambiente de desarrollo" en un avance visible, verificable y profesional. No busca implementar aun todos los escenarios del trabajo de grado; busca dejar lista la base tecnica sobre la cual se construiran esos escenarios.

## 2. Requisitos minimos recomendados
- Sistema operativo Linux (Ubuntu 22.04+ o Debian 12+).
- 16 GB de RAM recomendados.
- 20 GB de espacio libre para la base del proyecto.
- Docker Engine instalado.
- Docker Compose v2 disponible.
- Permisos para ejecutar Docker.
- Puerto configurable libre para la interfaz minima.

## 3. Logica de los scripts incluidos
### 3.1 `install_docker_ubuntu.sh`
Instala Docker usando el repositorio oficial y detecta correctamente si el host usa Ubuntu o Debian.

### 3.2 `check-requirements.sh`
Verifica versiones, daemon de Docker, RAM, espacio libre, puerto configurado y permisos basicos del usuario.

### 3.3 `bootstrap-project.sh`
Crea la estructura base del proyecto para que el repositorio ya tenga una organizacion consistente.

### 3.4 `init.sh`
Prepara carpetas, valida configuracion, crea `.env` si hace falta, valida el `compose` y levanta el smoke test.

### 3.5 `status.sh`
Muestra el estado del smoke test y la salud basica del servicio web usando la URL real configurada en `.env`.

### 3.6 `verify-smoke.sh`
Hace una comprobacion HTTP local, guarda evidencia HTML y cabeceras HTTP, y confirma que el entorno responde.

### 3.7 `reset.sh`
Reinicia el smoke test conservando la estructura del proyecto.

### 3.8 `cleanup.sh`
Apaga el smoke test y elimina recursos temporales del escenario minimo.

### 3.9 `scripts/lib/common.sh`
Centraliza carga de variables de entorno, validacion del puerto y funciones comunes para todos los scripts.

## 4. Pasos de configuracion
### Paso 1. Instalar Docker
```bash
bash scripts/install_docker_ubuntu.sh
```
Solo debe ejecutarse una vez en una maquina nueva. Si Docker ya esta instalado, este paso puede omitirse.

### Paso 2. Verificar requisitos
```bash
bash scripts/check-requirements.sh
```
Este paso genera un primer diagnostico. Si algo falla, conviene corregirlo antes de seguir.

### Paso 3. Crear estructura del proyecto
```bash
bash scripts/bootstrap-project.sh
```
Esto deja listas las carpetas de trabajo, escenarios, resultados y modulos.

### Paso 4. Generar archivo de entorno
```bash
cp .env.example .env
```
El archivo `.env` centraliza variables para cambiar el puerto, el nombre del proyecto o el modo de ejecucion sin editar varios archivos.

### Paso 5. Inicializar el smoke test
```bash
bash scripts/init.sh
```
Este paso levanta una interfaz minima en Nginx y un worker auxiliar. No es aun el simulador final, pero demuestra que el ambiente base ya esta operativo.

### Paso 6. Revisar estado
```bash
bash scripts/status.sh
```
Confirma que los contenedores esten corriendo y que el servicio web responda.

### Paso 7. Verificar por navegador o terminal
Abrir la URL que corresponda al valor de `PLATFORM_PORT` o ejecutar:
```bash
bash scripts/verify-smoke.sh
```

### Paso 8. Reiniciar o limpiar
```bash
bash scripts/reset.sh
bash scripts/cleanup.sh
```

## 5. Medidas de hardening aplicadas
- `no-new-privileges:true` para reducir escalamiento de privilegios.
- `cap_drop: ALL` para retirar capacidades Linux innecesarias.
- `read_only: true` para limitar escritura dentro del contenedor.
- `tmpfs` solo donde hace falta escritura temporal.
- `pids_limit` para reducir impacto de procesos descontrolados.
- rotacion basica de logs para contener crecimiento.
- validacion previa del `compose` antes del arranque.

## 6. Que demuestra tecnicamente este avance
- que el host de desarrollo fue identificado;
- que Docker y Docker Compose pueden ser validados;
- que la estructura del proyecto ya existe;
- que el proyecto ya usa variables de entorno;
- que un orquestador basico ya fue preparado;
- que los logs y evidencias ya tienen carpeta destino;
- que ya existe criterio minimo de ciberseguridad en el entorno base;
- y que la futura evolucion hacia escenarios reales no parte de cero.

## 7. Como lo defenderia en reunion
Se inicio la configuracion del ambiente de desarrollo con una base reproducible llamada ValleSec Lab. La entrega incluye scripts automatizados, validacion de requisitos, estructura inicial del repositorio, variables de entorno, un smoke test con Docker Compose y evidencia de preparacion para integrar escenarios reales en fases siguientes. Adicionalmente, el entorno ya incorpora medidas iniciales de hardening para demostrar que el simulador sera construido bajo criterios tecnicos y de ciberseguridad desde las primeras etapas.
