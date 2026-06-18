# S03 - Aplicación web vulnerable para prácticas OWASP

## Propósito

Este escenario presenta una aplicación web de laboratorio para analizar vulnerabilidades comunes descritas por OWASP. La práctica se centra en comprender riesgos asociados a entradas de usuario, validación insuficiente y exposición de archivos.

## Contexto del escenario

El laboratorio incluye tres ejercicios didácticos:

- búsqueda con comportamiento inseguro para discutir inyección;
- formulario de comentarios para analizar riesgos de XSS;
- consulta de archivos para estudiar Directory Traversal de forma controlada.

## Lo que sí hace este escenario

- Presenta formularios web de laboratorio.
- Permite observar respuestas inseguras en un entorno local.
- Registra eventos para análisis posterior.
- Facilita la discusión de controles de seguridad web.

## Lo que no hace este escenario

- No contiene datos reales.
- No se conecta a bases de datos institucionales.
- No debe usarse para probar sitios externos.
- No busca enseñar evasión avanzada ni explotación fuera del laboratorio.

## Relación con OWASP

El escenario se relaciona con categorías de OWASP Top 10 como fallas de control de acceso, inyección, errores de validación y exposición de información por manejo inseguro de rutas o entradas.

## Cierre pedagógico

El objetivo principal es que el estudiante comprenda cómo una mala validación de entradas puede generar riesgos y qué controles pueden reducirlos.