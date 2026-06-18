# S04 - Autenticación simulada sobre servicios SSH y FTP

## Propósito

Este escenario permite estudiar riesgos de autenticación en servicios de red simulados. El laboratorio representa servicios tipo SSH y FTP sin exponer servicios reales del sistema operativo.

## Contexto del escenario

El estudiante interactúa con una interfaz web que simula intentos de autenticación sobre servicios SSH y FTP. Cada intento queda registrado como evento para facilitar análisis, discusión y retroalimentación.

## Lo que sí hace este escenario

- Simula intentos de autenticación sobre servicios SSH y FTP.
- Registra eventos válidos y fallidos.
- Permite discutir riesgos de credenciales débiles.
- Facilita la propuesta de controles defensivos.

## Lo que no hace este escenario

- No levanta un servidor SSH real.
- No levanta un servidor FTP real.
- No utiliza credenciales institucionales.
- No automatiza ataques contra sistemas externos.
- No permite fuerza bruta real contra infraestructura ajena.

## Relación con marcos de referencia

El escenario se relaciona con MITRE ATT&CK T1110, asociado a intentos de fuerza bruta. En este proyecto, la técnica se trabaja de forma simulada y pedagógica para comprender el riesgo y las medidas de mitigación.

## Controles a discutir

- Contraseñas robustas.
- Bloqueo progresivo.
- Autenticación multifactor.
- Registro centralizado de eventos.
- Alertas ante múltiples intentos fallidos.
- Deshabilitar servicios innecesarios.
- Uso de llaves en lugar de contraseñas para SSH.

## Cierre pedagógico

El objetivo no es vulnerar un servicio, sino comprender por qué la autenticación débil aumenta el riesgo y cómo se puede reducir mediante controles preventivos y detectivos.