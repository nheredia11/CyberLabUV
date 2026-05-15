# Arquitectura inicial de escenarios de ValleSec Lab

## Objetivo de esta iteracion
Dejar una base coherente para pasar del smoke test a un **prototipo funcional con interfaces basicas y escenarios iniciales**.

## Capas de la propuesta actual
1. **Capa de interfaz**
   - landing estatica del prototipo;
   - catalogo de escenarios;
   - interfaz web del laboratorio de autenticacion HTTP.

2. **Capa de orquestacion**
   - scripts `run-scenario`, `stop-scenario` y `list-scenarios`;
   - `docker-compose.yml` por escenario;
   - variables de entorno centralizadas.

3. **Capa de escenarios**
   - `recon`: reconocimiento de servicios dentro de una red aislada;
   - `auth_http`: laboratorio propio de autenticacion debil;
   - `webapp`: plantilla para escenario OWASP.

4. **Capa pedagogica**
   - teoria por modulo;
   - checkpoints;
   - encuesta de cierre;
   - catalogo comun para interfaz y documentacion.

## Criterios de seguridad aplicados
- redes Docker separadas por escenario;
- puertos minimos expuestos al host;
- no se usan datos reales ni credenciales institucionales;
- el laboratorio de autenticacion es propio y limitado al entorno local.

## Ruta de evolucion sugerida
- agregar recoleccion de evidencias por estudiante;
- crear bitacora JSON por sesion;
- integrar un tablero de instructor;
- crear pruebas de humo por escenario;
- agregar perfiles de Compose para Blue Team en iteraciones posteriores.
