# CyberLabUV: Simulador práctico de ciberseguridad basado en contenedores

**Nombre operativo propuesto del simulador:** CyberLabUV 
**Subtitulo:** Plataforma didactica para entrenamiento practico en ciberseguridad en entornos controlados y reproducibles.

## 1. Que se entrega en este paquete
Este paquete no reemplaza la idea del trabajo de grado. La fortalece. Su objetivo es mostrar avance real en la tarea pendiente de **empezar a configurar el ambiente de desarrollo** y dejar una base mas seria para la futura implementacion y despliegue del simulador.

Incluye:
- scripts comentados para instalar, verificar, inicializar, reiniciar y limpiar el ambiente;
- un `docker-compose.yml` de smoke test endurecido en seguridad;
- un ejemplo de modulo teorico inicial;
- una guia detallada de configuracion;
- una explicacion de cada archivo clave y de cada bloque de codigo;
- y mejoras de hardening para demostrar criterio tecnico y de ciberseguridad.

## 2. Mejoras tecnicas aplicadas
En esta version se reforzaron varios puntos:
- los scripts ya leen el puerto desde `.env` y no dependen de `8080` fijo;
- se creo una libreria comun (`scripts/lib/common.sh`) para centralizar validaciones;
- el instalador de Docker detecta Ubuntu o Debian correctamente;
- `docker compose config` se valida antes de levantar servicios;
- el smoke test guarda evidencia HTML y cabeceras HTTP;
- el `compose` aplica `no-new-privileges`, `cap_drop: ALL`, `read_only` y limites basicos;
- y se agrego rotacion de logs para reducir crecimiento innecesario.

## 3. Arquitectura minima del ambiente de desarrollo
El ambiente se organiza en cinco piezas base:

1. **Host de desarrollo**  
   Equipo Linux donde se instala Docker y se almacena el repositorio.

2. **Scripts de automatizacion**  
   Automatizan la validacion del entorno, la creacion de estructura y el arranque del smoke test.

3. **Docker Compose**  
   Orquesta los servicios minimos de prueba y deja el proyecto listo para evolucionar hacia escenarios reales.

4. **Modulo pedagogico base**  
   Sirve como ejemplo de como se almacenaria teoria, checkpoints y encuesta.

5. **Carpetas de logs y resultados**  
   Preparan desde ya la captura de evidencias para pruebas tecnicas y pedagogicas.

## 4. Flujo recomendado para mostrar avance
```bash
bash scripts/check-requirements.sh
bash scripts/bootstrap-project.sh
cp .env.example .env
bash scripts/init.sh
bash scripts/status.sh
bash scripts/verify-smoke.sh
bash scripts/reset.sh
bash scripts/cleanup.sh
```

## 5. Que deberias mostrar en la proxima reunion
1. Salida de `docker --version`.
2. Salida de `docker compose version`.
3. Salida de `bash scripts/check-requirements.sh`.
4. Estructura de carpetas creada.
5. `docker compose ps` o `docker ps`.
6. Acceso local al smoke test en la URL configurada por `PLATFORM_PORT`.
7. Carpeta `logs/` con reporte, HTML y cabeceras HTTP generadas.
8. Justificacion de medidas de hardening basicas del compose.

## 6. Siguiente paso natural
Despues del smoke test, el siguiente paso tecnico coherente es crear un **escenario base de reconocimiento** con:
- un contenedor atacante;
- un contenedor objetivo con servicios visibles;
- una red Docker aislada;
- y checkpoints iniciales para registrar avance.


## 7. Escenarios y nuevas interfaces incorporadas
En esta iteracion ya se incorporan componentes que te acercan mucho mas a la fase 3 del proyecto:
- **Interfaz principal del prototipo** en `scenarios/smoke/landing/` con catalogo inicial de escenarios.
- **S01 Reconocimiento** con red aislada y multiples servicios visibles para observacion.
- **S02 Autenticacion HTTP** con una interfaz de laboratorio propia para discutir debilidades y mitigaciones.
- **S03 WebApp** como base de integracion para un laboratorio OWASP.
- Scripts dedicados: `list-scenarios.sh`, `run-scenario.sh`, `stop-scenario.sh`, `status-scenarios.sh`.

### Comandos sugeridos
```bash
bash scripts/list-scenarios.sh
bash scripts/run-scenario.sh recon
bash scripts/run-scenario.sh auth_http
bash scripts/status-scenarios.sh
bash scripts/stop-scenario.sh recon
bash scripts/stop-scenario.sh auth_http
```
