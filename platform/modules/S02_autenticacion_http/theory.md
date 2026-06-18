# S02 - Autenticación HTTP débil en entorno controlado

## Propósito

Este escenario introduce un laboratorio propio de autenticación HTTP con fines pedagógicos. El objetivo es estudiar cómo una política de autenticación débil puede aumentar el riesgo de acceso no autorizado dentro de una aplicación web.

El ejercicio se desarrolla únicamente en un entorno local, controlado y académico.

## Contexto del escenario

El laboratorio presenta una aplicación web vulnerable de demostración. Esta aplicación permite observar fallos comunes relacionados con autenticación, tales como:

- ausencia de bloqueo progresivo;
- credenciales débiles de prueba;
- mensajes de error poco controlados;
- falta de monitoreo visible para intentos repetidos;
- ausencia de políticas robustas de contraseña.

## Lo que sí hace este escenario

- Presenta una interfaz web local para autenticar usuarios de prueba.
- Permite observar el comportamiento de una autenticación débil.
- Registra intentos de acceso dentro del entorno de laboratorio.
- Facilita la discusión sobre controles preventivos y detectivos.
- Permite registrar checkpoints y evidencias del proceso.

## Lo que no hace este escenario

- No utiliza credenciales institucionales reales.
- No se conecta a servicios externos.
- No automatiza ataques contra sistemas reales.
- No incluye técnicas avanzadas de evasión.
- No debe ejecutarse fuera del laboratorio autorizado.

## Relación con marcos de referencia

Este escenario se relaciona con:

- **OWASP A07: Identification and Authentication Failures**, por el análisis de fallos de autenticación.
- **NIST Protect/Detect**, por la discusión de controles de protección, monitoreo y trazabilidad.
- **Hacking ético académico**, porque la práctica se realiza en un entorno autorizado y aislado.

## Buenas prácticas a discutir al cierre

Al finalizar el escenario, el estudiante debe proponer controles como:

- bloqueo progresivo después de varios intentos fallidos;
- registro y monitoreo de intentos de autenticación;
- uso de contraseñas robustas;
- autenticación multifactor;
- mensajes de error menos informativos;
- separación entre usuarios de prueba y usuarios reales;
- revisión periódica de logs.

## Cierre pedagógico

El propósito principal no es obtener una contraseña, sino comprender por qué una autenticación débil representa un riesgo y cómo puede mitigarse mediante controles técnicos y buenas prácticas de seguridad.