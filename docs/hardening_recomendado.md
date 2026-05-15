# Hardening recomendado para la siguiente fase de ValleSec Lab

## Prioridad alta
1. Mantener imagenes fijadas a versiones especificas y revisar CVE antes de cada entrega.
2. Separar redes por escenario para no mezclar trafico entre practicas.
3. Evitar contenedores privilegiados salvo cuando el caso academico lo requiera y quede justificado.
4. No exponer puertos innecesarios al host.
5. Mantener secretos fuera del repositorio y usar `.env` solo para desarrollo local.

## Prioridad media
1. Agregar escaneo de imagenes con Trivy o Docker Scout.
2. Firmar imagenes o al menos documentar su procedencia.
3. Registrar evidencias tecnicas por escenario en `platform/results`.
4. Definir politicas de nombres, redes y puertos por escenario.
5. Preparar un archivo `Makefile` o tareas equivalentes para estandarizar comandos.

## Prioridad academica
1. Documentar limites eticos y de uso aceptable dentro del simulador.
2. Mantener cada escenario aislado, reproducible y reversible.
3. Guardar checkpoints tecnicos y pedagogicos por practica.
4. Demostrar que las pruebas ocurren solo en entornos controlados.
