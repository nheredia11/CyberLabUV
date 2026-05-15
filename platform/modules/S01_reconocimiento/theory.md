# S01 - Reconocimiento de red y servicios

## Proposito
Este escenario introduce al estudiante al reconocimiento inicial dentro de un laboratorio controlado. La meta no es atacar, sino **identificar** activos y comprender por que la exposicion de servicios incrementa la superficie de ataque.

## Conceptos clave
- Descubrimiento de hosts y servicios.
- Puertos y banners como evidencia tecnica.
- Relacion entre visibilidad de red y riesgo.
- Importancia de registrar hallazgos antes de cualquier fase posterior.

## Activos del escenario
- `student-recon`: contenedor de observacion del estudiante.
- `target-web`: servicio HTTP informativo.
- `target-login`: servicio HTTP con autenticacion simulada.
- `target-cache`: servicio Redis visible solo dentro de la red interna.

## Regla pedagogica
Toda evidencia debe quedar consignada en notas del escenario antes de avanzar a modulos de autenticacion o aplicacion web.
