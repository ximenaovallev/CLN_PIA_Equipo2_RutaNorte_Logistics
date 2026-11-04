# Casos de uso (Unidad 3, vigentes en el PIA)

| ID | Caso de uso | Actor | Reglas relacionadas | Resultado esperado | Historias / BPMN |
|---|---|---|---|---|---|
| CU-01 | Responder cotización (acepta / rechaza) | Cliente | La cotización solo cambia mientras está en proceso | Cotización ACEPTADA o RECHAZADA registrada | US-17, US-01–03 / "¿Respuesta del cliente?" |
| CU-02 | Generar orden de servicio | Operaciones | La orden solo se genera tras la aceptación | Orden en estado CONFIRMADO con historial | US-06 / "Generar orden de servicio" |
| CU-03 | Asignar unidad y operador (flujo normal y excepción de recursos no disponibles) | Operaciones | Unidad con capacidad suficiente; operador disponible; reasignar conserva historial | Orden en UNIDAD_ASIGNADA, o error de negocio sin cambios | US-07, US-08 / "¿Unidad adecuada y operador disponible?" |
| CU-04 | Registrar entrega o incidencia en destino | Operador | Entrega exige LLEGADA_A_DESTINO; receptor y evidencia; incidencias no entregan | Orden ENTREGADO o incidencia registrada con evidencia | US-11, US-12, US-13 / "¿Entrega posible, completa y sin daño?" |
| CU-05 | Consultar estado del servicio | Atención al Cliente | Consulta sin depender de Operaciones | Estado, eventos, retrasos e incidencias | US-14 / "Consultar estado…" |
| CU-06 | Cancelar servicio (supuesto S-04) | Operaciones | Registrar quién la solicita y el motivo; autoridad configurable; no se cancela un servicio entregado | Orden CANCELADO con solicitante y motivo en el historial | US-05 / S2, T5, G5, T5A, E2 |
| CU-07 | Autorizar carga de alto valor (supuesto S-02) | Operaciones | La carga de alto valor se autoriza antes de asignar recursos | Autorización registrada; permite CU-03 | US-16 / G2 |

Los supuestos S-01 a S-05 están en `docs/architecture/supuestos.md`.

En el PIA los 19 comandos y 7 consultas del Service Layer cubren las 17 historias (ver `historias_de_usuario.md`); estos siete casos de uso son los detallados con diagramas de secuencia (`architecture/diagramas/05_*` y `06_*`). Los supuestos S-01 a S-05 están en `architecture/supuestos.md`.
