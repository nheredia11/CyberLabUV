# Roadmap de implementación v2 - CyberLabUV / ValleSec Lab

Esta iteración responde a las observaciones de tutoría: avanzar más la implementación, reducir texto en la interfaz, hacer el panel docente más gráfico y empezar a mostrar una primera simulación funcional.

## Cambios implementados

1. **Dashboard más visual del estudiante**
   - Indicador circular de progreso general.
   - Tarjetas KPI de progreso, módulos, insignias y puntos.
   - Botones directos para continuar ruta o abrir laboratorio.
   - Nivel formativo por módulo: pendiente, inicial, en consolidación o autónomo.

2. **Retroalimentación adaptativa**
   - Nuevo endpoint: `GET /api/modules/{module_id}/feedback`.
   - Genera recomendaciones según checkpoints completados y pendientes.
   - La vista de ruta muestra mensaje, nivel, próximos pasos y checkpoints pendientes.

3. **Terminal guiada segura**
   - Nuevo endpoint: `POST /api/scenarios/terminal`.
   - Sólo acepta comandos permitidos por escenario.
   - Registra comandos, estado y salida para analíticas docentes.
   - Sirve como evidencia reproducible sin ejecutar comandos peligrosos fuera del laboratorio.

4. **Panel docente más tipo dashboard**
   - Indicadores grandes: progreso promedio, alertas de refuerzo, checkpoints cerrados y comandos guiados.
   - Gráfica por módulo.
   - Recomendaciones docentes derivadas del avance.

5. **Base para primera simulación demostrable**
   - Escenario priorizado: `auth_http`.
   - Flujo esperado: iniciar escenario, ejecutar comando guiado, registrar checkpoint, revisar feedback y observar analíticas.

## Próximo sprint recomendado

1. Convertir `auth_http` en el primer escenario completamente presentable.
2. Agregar enlace visible al servicio vulnerable cuando el contenedor esté arriba.
3. Añadir rúbrica docente para evaluar evidencia.
4. Crear reporte exportable de la sesión del estudiante.
5. Implementar login visual por correo institucional y selector de rol estudiante/docente.
