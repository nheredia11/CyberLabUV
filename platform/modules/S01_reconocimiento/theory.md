# S01 - Reconocimiento de red y servicios

## Propósito

Este escenario introduce el reconocimiento de red y servicios en un entorno local, controlado y académico. El objetivo es que el estudiante observe qué servicios se encuentran disponibles dentro del laboratorio y registre los hallazgos de manera responsable.

## Contexto del escenario

El laboratorio expone una aplicación HTTP y servicios simulados tipo SSH y FTP dentro de una red Docker. El ejercicio permite comprender cómo un analista identifica servicios, versiones aparentes y posibles superficies de exposición.

## Lo que sí hace este escenario

- Expone servicios de laboratorio en una red controlada.
- Permite observar banners y puertos simulados.
- Registra eventos cuando los servicios reciben conexiones.
- Facilita la discusión sobre inventario, exposición y monitoreo.

## Lo que no hace este escenario

- No analiza redes reales.
- No realiza explotación de vulnerabilidades.
- No interactúa con sistemas externos.
- No debe usarse contra infraestructura institucional o pública.

## Relación con marcos de referencia

Este escenario se relaciona con MITRE ATT&CK T1046, porque permite estudiar la identificación de servicios de red en una fase de reconocimiento. También se relaciona con NIST Identify, al apoyar la comprensión del inventario y la superficie de exposición.

## Cierre pedagógico

El objetivo no es atacar un servicio, sino comprender por qué el reconocimiento es una fase importante para identificar activos expuestos y definir controles de protección.