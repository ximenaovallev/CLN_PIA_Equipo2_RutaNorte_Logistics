# BPMN del proceso (RutaNorte Logistics)

`01_bpmn_rutanorte.bpmn` (editable en bpmn.io) y `01_bpmn_rutanorte.png`. Es el BPMN de la Unidad 2 actualizado en la Unidad 3 (cancelación, cambios operativos y consulta) y **se conserva sin cambios en el PIA**; el diseño y el código se derivan de él:

| Elemento BPMN | En el código |
|---|---|
| T1 Solicitar cotización → T2 Elaborar | `Cotizacion` (SOLICITADO → COTIZADO), `POST /cotizaciones`, `PUT …/importe` |
| G1 ¿Respuesta del cliente? / T3 Modificar / E1 Rechazada | `Cotizacion.aceptar / rechazar / modificar` |
| T4 Generar orden (CONFIRMADO) | `OrdenDeServicio.generar_desde`, `POST /ordenes` |
| S2, T5, G5, T5A, T5B, E2, E2B Cambio o cancelación | `cancelar`, `solicitar_cambio_operativo`, `revisar_cambio_operativo` |
| T6 / G2 ¿Unidad adecuada y operador disponible? / T7 / T8 | `asignacion_permitida()` (Specification), `AsignadorDeRecursos`, `asignar_recursos` |
| T9 / G3 / T10 Recepción (RECOLECTADO) | `registrar_recepcion`, `recepcion_documentada()` |
| T11 Traslado (EN_TRANSITO) | `iniciar_traslado` |
| B1, T12, T13 Avería o retraso; T14, T15, T20, T21 Incidencias | `registrar_incidencia` (no cambia el estado) |
| T16 Llegada (LLEGADA_A_DESTINO) | `registrar_llegada_a_destino` |
| G4 ¿Entrega posible, completa y sin daño? / T17–T19 (ENTREGADO) | `registrar_entrega` + `entrega_documentada()` |
| S3 / T22 y S4 / T23, DS1 | Queries `ConsultarEstadoDelServicio` y `ConsultarIndicadores` |

La correspondencia historia ↔ BPMN ↔ endpoint ↔ prueba está en `docs/architecture/trazabilidad.md` y `tests/test_trazabilidad.py` verifica que cada ID BPMN citado exista en el archivo.
