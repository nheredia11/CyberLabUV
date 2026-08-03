# S05 - MITM simulado en tráfico no cifrado

## Propósito

Este escenario permite comprender el riesgo de enviar información sin cifrado. La práctica representa un flujo cliente-servidor donde un observador puede ver mensajes de laboratorio.

## Contexto del escenario

El laboratorio no ejecuta un ataque MITM real. En su lugar, presenta una simulación pedagógica que muestra cómo un mensaje no cifrado puede quedar expuesto a observación dentro de una comunicación insegura.

## Lo que sí hace este escenario

- Simula envío de mensajes no cifrados.
- Registra eventos visibles para análisis.
- Permite discutir el uso de HTTPS/TLS.
- Facilita la relación entre práctica, riesgo y mitigación.

## Lo que no hace este escenario

- No realiza ARP spoofing.
- No intercepta tráfico real.
- No analiza tráfico de la red del usuario.
- No captura credenciales reales.
- No se conecta a sistemas externos.

## Relación con seguridad defensiva

El escenario se relaciona con prácticas de protección y detección, porque permite discutir la importancia de cifrar comunicaciones, validar certificados, evitar datos sensibles en texto claro y monitorear tráfico anómalo.

## Controles a discutir

- Uso obligatorio de HTTPS/TLS.
- Validación correcta de certificados.
- No transmitir credenciales en texto claro.
- Segmentación de red.
- Monitoreo de tráfico anómalo.
- Educación del usuario sobre conexiones inseguras.

## Cierre pedagógico

El objetivo es que el estudiante comprenda el riesgo conceptual de la comunicación no cifrada y proponga controles de protección, sin ejecutar técnicas ofensivas contra redes reales.