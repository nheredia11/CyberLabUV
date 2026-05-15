# S02 - Autenticacion HTTP debil en entorno controlado

## Proposito
Este escenario introduce un laboratorio propio de autenticacion HTTP con fines pedagogicos. Sirve para estudiar politicas debiles, respuestas del sistema y necesidad de mitigaciones como limite de intentos, monitoreo y credenciales robustas.

## Lo que si hace
- Presenta una interfaz web local para autenticar usuarios de prueba.
- Registra intentos de acceso dentro del contenedor.
- Permite al instructor reiniciar facilmente el escenario.

## Lo que no hace
- No incluye tecnicas avanzadas de evasion.
- No automatiza ataques reales fuera del laboratorio.
- No usa credenciales institucionales ni datos reales.

## Buenas practicas a discutir al cierre
- bloqueo progresivo;
- trazabilidad de intentos;
- mensajes de error no excesivamente informativos;
- gestion segura de credenciales.
