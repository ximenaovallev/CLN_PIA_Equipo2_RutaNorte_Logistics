# Historias de usuario y criterios de aceptación (Gherkin)

Las 17 historias de la Unidad 2 se conservan con su identificador y se **refinan**: cada criterio genérico se convirtió en escenarios concretos (camino feliz y excepción) con datos de ejemplo, el endpoint que los ejecuta y las pruebas que los verifican. Los `.feature` están en `docs/analisis/features/`. `tests/test_trazabilidad.py` comprueba que todas las referencias de esta página existan.

| ID | Historia | Requisito | Necesidad | BPMN | Endpoint | Pruebas |
|---|---|---|---|---|---|---|
| US-01 | Solicitud de cotización | RF-01 | N1, N2 | S1, T1 | `POST /cotizaciones` | 3 |
| US-02 | Elaboración de cotización | RF-02, RNF-01 | N1, N2 | T2 | `PUT /cotizaciones/{cotizacion_id}/importe` | 2 |
| US-03 | Modificación de cotización | RF-03 | N1 | G1, T3 | `PUT /cotizaciones/{cotizacion_id}/solicitud` | 3 |
| US-04 | Revisión de cambios operativos | RF-08 | N2, N5 | S2, T5, G5, T5B | `POST /ordenes/{orden_id}/cambios-operativos`<br>`PUT /ordenes/{orden_id}/cambios-operativos/revision` | 3 |
| US-05 | Confirmación y registro de cancelación | RF-09, RF-05 | N1, N2, N5 | S2, T5, G5, T5A, E2, E2B | `POST /ordenes/{orden_id}/cancelacion`<br>`POST /ordenes` | 5 |
| US-06 | Generación de orden | RF-05 | N1, N2 | T4 | `POST /ordenes` | 2 |
| US-07 | Asignación de recursos | RF-06 | N2 | T6, G2, T8 | `POST /ordenes/{orden_id}/asignacion` | 5 |
| US-08 | Reasignación de operador | RF-07 | N2, N5 | G2, T7 | `POST /ordenes/{orden_id}/asignacion`<br>`PUT /operadores/{operador_id}/disponibilidad` | 3 |
| US-09 | Recepción y validación de mercancía | RF-10 | N4, N5 | T9, G3, T10, T14 | `POST /ordenes/{orden_id}/recepcion`<br>`POST /ordenes/{orden_id}/incidencias` | 3 |
| US-10 | Actualización de estados | RF-11 | N2 | T4, T8, T10, T11, T16, T19 | `POST /ordenes/{orden_id}/traslado`<br>`POST /ordenes/{orden_id}/llegada` | 5 |
| US-11 | Registro de incidencias | RF-12 | N3, N5 | B1, T12, T13, G4, T20, T21 | `POST /ordenes/{orden_id}/incidencias`<br>`POST /ordenes/{orden_id}/entrega` | 5 |
| US-12 | Registro de llegada y entrega | RF-13 | N2, N4 | T16, T17, T18, G4, T19 | `POST /ordenes/{orden_id}/llegada`<br>`POST /ordenes/{orden_id}/entrega` | 3 |
| US-13 | Evidencia y receptor | RF-13, RF-10 | N4 | T10, T14, T19, T20 | `POST /ordenes/{orden_id}/recepcion`<br>`POST /ordenes/{orden_id}/entrega` | 5 |
| US-14 | Consulta para Atención al Cliente | RF-14 | N3, N6 | S3, T22, E8, DS1 | `GET /ordenes/{orden_id}/estado`<br>`GET /ordenes` | 2 |
| US-15 | Indicadores históricos | RF-15 | N7 | S4, T23, E7, DS1 | `GET /indicadores` | 3 |
| US-16 | Controles para carga de alto valor | RF-16 | N8 | G2 (S-02) | `POST /ordenes/{orden_id}/autorizacion-alto-valor`<br>`POST /ordenes/{orden_id}/asignacion` | 4 |
| US-17 | Respuesta a la cotización | RF-04, RF-03 | N1, N2 | G1, E1, T3 | `POST /cotizaciones/{cotizacion_id}/respuesta`<br>`PUT /cotizaciones/{cotizacion_id}/solicitud` | 4 |

## US-01: Solicitud de cotización

**Como** cliente, **quiero** solicitar una cotización proporcionando origen, destino, mercancía, peso, dimensiones, fecha requerida y características especiales cuando sean necesarias, **para** obtener una propuesta de transporte adecuada.

- Requisitos: RF-01 · Necesidades: N1, N2 · BPMN: S1, T1
- API: `POST /cotizaciones`
- Componentes: `domain.cotizacion.Cotizacion`, `domain.valores.SolicitudDeCotizacion`, `application.handlers.SolicitarCotizacionHandler`

```gherkin
Scenario: Solicitud registrada con los datos proporcionados
  Given que el cliente CLI-1 está registrado
  When solicita una cotización de Monterrey a Querétaro con 800 kg de refacciones de 2 x 1.5 x 1.5 m para el 2026-12-01
  Then se registra la solicitud en estado SOLICITADO
  And se devuelve el identificador de la cotización con código 201

Scenario: Datos inválidos no se registran
  Given que el cliente CLI-1 está registrado
  When solicita una cotización con peso de -5 kg
  Then la API responde 400 con el código DatosInvalidos
  And no se crea ninguna cotización

Scenario: El solicitante debe existir
  Given que el cliente NO-EXISTE no está registrado
  When solicita una cotización
  Then la API responde 404 con el código EntidadNoEncontrada
```

Pruebas: `test_catalogos_y_cambios.py::test_ciclo_de_cotizacion_solicitada_cotizada_aceptada`, `test_catalogos_y_cambios.py::test_solicitar_cotizacion_exige_cliente_registrado`, `test_api.py::test_400_cuerpo_incompleto_o_valores_invalidos`

## US-02: Elaboración de cotización

**Como** vendedor, **quiero** elaborar una cotización utilizando la información proporcionada por el cliente, **para** presentar al cliente una propuesta con su importe.

- Requisitos: RF-02, RNF-01 · Necesidades: N1, N2 · BPMN: T2
- API: `PUT /cotizaciones/{cotizacion_id}/importe`
- Componentes: `domain.cotizacion.Cotizacion.elaborar`, `domain.maquina_de_estados.MaquinaDeEstados`, `application.handlers.ElaborarCotizacionHandler`

```gherkin
Scenario: Cotización elaborada
  Given una solicitud de cotización en estado SOLICITADO
  When Ventas registra el importe 1234.56 MXN
  Then el servicio pasa a COTIZADO
  And el importe se conserva exacto como Decimal

Scenario: El importe debe ser positivo
  Given una solicitud de cotización en estado SOLICITADO
  When Ventas registra el importe 0
  Then la API responde 400 y la cotización sigue en SOLICITADO
```

Pruebas: `test_catalogos_y_cambios.py::test_ciclo_de_cotizacion_solicitada_cotizada_aceptada`, `test_api.py::test_cotizacion_conserva_el_importe_decimal_exacto`

## US-03: Modificación de cotización

**Como** vendedor, **quiero** modificar una cotización mientras está en proceso, **para** corregir o ajustar la información antes de que el cliente responda.

- Requisitos: RF-03 · Necesidades: N1 · BPMN: G1, T3
- API: `PUT /cotizaciones/{cotizacion_id}/solicitud`
- Componentes: `domain.cotizacion.Cotizacion.modificar`, `domain.especificaciones.CotizacionEnProceso`, `application.handlers.ModificarCotizacionHandler`

```gherkin
Scenario: Modificación mientras está en proceso
  Given una cotización en proceso
  When Ventas cambia el destino a Guadalajara
  Then la información actualizada queda registrada

Scenario: No se modifica una cotización ya respondida
  Given una cotización que el cliente rechazó
  When Ventas intenta modificarla
  Then la API responde 409 con el código CotizacionNoModificable
```

Pruebas: `test_dominio.py::test_cotizacion_solo_se_modifica_mientras_esta_en_proceso`, `test_catalogos_y_cambios.py::test_modificar_cotizacion_mientras_esta_en_proceso`, `test_api.py::test_modificar_solicitud_solo_mientras_esta_en_proceso`

## US-04: Revisión de cambios operativos

**Como** responsable de Operaciones, **quiero** revisar los cambios que afectan una orden de servicio, **para** evitar que la operación continúe con condiciones no validadas.

- Requisitos: RF-08 · Necesidades: N2, N5 · BPMN: S2, T5, G5, T5B
- API: `POST /ordenes/{orden_id}/cambios-operativos`, `PUT /ordenes/{orden_id}/cambios-operativos/revision`
- Componentes: `domain.orden_de_servicio.OrdenDeServicio.solicitar_cambio_operativo`, `domain.orden_de_servicio.OrdenDeServicio.revisar_cambio_operativo`, `domain.especificaciones.CambioOperativoPendiente`, `application.handlers.SolicitarCambioOperativoHandler`, `application.handlers.RevisarCambioOperativoHandler`

```gherkin
Scenario: Un cambio pendiente bloquea la orden
  Given una orden CONFIRMADA
  When el cliente solicita cambiar el horario de recolección
  Then el cambio queda pendiente de revisión
  And asignar recursos responde 409 con el código CambioPendienteDeRevision

Scenario: Operaciones revisa y la orden continúa
  Given una orden con un cambio pendiente
  When Operaciones aprueba o rechaza el cambio
  Then el cambio deja de estar pendiente y la orden puede continuar
```

Pruebas: `test_catalogos_y_cambios.py::test_cambio_operativo_pendiente_bloquea_las_operaciones_hasta_revisarse`, `test_api.py::test_cambio_operativo_bloquea_y_se_revisa`, `test_especificaciones.py::test_sin_cambio_pendiente`

## US-05: Confirmación y registro de cancelación

**Como** responsable del servicio, **quiero** que la confirmación y las cancelaciones queden registradas, **para** conservar quién solicitó la acción y por qué.

- Requisitos: RF-09, RF-05 · Necesidades: N1, N2, N5 · BPMN: S2, T5, G5, T5A, E2, E2B
- API: `POST /ordenes/{orden_id}/cancelacion`, `POST /ordenes`
- Componentes: `domain.orden_de_servicio.OrdenDeServicio.cancelar`, `domain.servicios.AutoridadDeCancelacion`, `application.handlers.CancelarServicioHandler`

```gherkin
Scenario: Cancelación registrada con solicitante y motivo
  Given una orden CONFIRMADA
  When Cliente ACME solicita cancelar por "Ya no requiere el envío" y Operaciones la autoriza
  Then la orden queda CANCELADA
  And se conservan quién la solicitó y el motivo

Scenario: Un rol sin autoridad no cancela
  Given una orden CONFIRMADA y que solo Operaciones puede cancelar
  When Ventas intenta autorizar la cancelación
  Then la API responde 422 con el código SinAutoridadParaCancelar
  And la orden sigue CONFIRMADA

Scenario: Un servicio terminado no se cancela
  Given una orden ya CANCELADA o ENTREGADA
  When se solicita cancelar de nuevo
  Then la API responde 409 con el código TransicionDeEstadoInvalida
```

Pruebas: `test_supuestos_pendientes.py::test_s04_cancelacion_registra_quien_y_motivo`, `test_supuestos_pendientes.py::test_s04_rol_sin_autoridad_no_cancela`, `test_supuestos_pendientes.py::test_s04_la_autoridad_es_configurable`, `test_supuestos_pendientes.py::test_s04_exige_motivo_y_no_cancela_un_servicio_ya_cancelado`, `test_maquina_de_estados.py::test_se_puede_cancelar_un_servicio_aceptado_que_no_ha_terminado`

## US-06: Generación de orden

**Como** responsable de Operaciones, **quiero** generar una orden de servicio después de la aceptación de la cotización, **para** iniciar formalmente la operación.

- Requisitos: RF-05 · Necesidades: N1, N2 · BPMN: T4
- API: `POST /ordenes`
- Componentes: `domain.orden_de_servicio.OrdenDeServicio.generar_desde`, `domain.eventos.OrdenDeServicioGenerada`, `application.handlers.GenerarOrdenDeServicioHandler`

```gherkin
Scenario: Orden generada tras la aceptación
  Given una cotización ACEPTADA
  When Operaciones genera la orden con la ruta MTY-QRO y el horario de recolección
  Then la orden queda CONFIRMADA con un evento en su historial
  And se publica el evento OrdenDeServicioGenerada

Scenario: Sin aceptación no hay orden
  Given una cotización que el cliente no ha aceptado
  When Operaciones intenta generar la orden
  Then la API responde 422 con el código OrdenNoGenerable
  And no se crea ninguna orden
```

Pruebas: `test_casos_de_uso.py::test_cu02_orden_se_genera_solo_tras_aceptacion`, `test_api.py::test_422_no_se_genera_orden_de_una_cotizacion_sin_aceptar`

## US-07: Asignación de recursos

**Como** responsable de Operaciones, **quiero** asignar una unidad y un operador considerando carga, capacidad y disponibilidad, **para** garantizar que el servicio se ejecute con recursos adecuados.

- Requisitos: RF-06 · Necesidades: N2 · BPMN: T6, G2, T8
- API: `POST /ordenes/{orden_id}/asignacion`
- Componentes: `domain.servicios.AsignadorDeRecursos`, `domain.especificaciones.UnidadConCapacidadSuficiente`, `domain.especificaciones.OperadorDisponible`, `domain.especificaciones.asignacion_permitida`, `application.handlers.AsignarRecursosHandler`

```gherkin
Scenario: Asignación adecuada
  Given una orden CONFIRMADA de 800 kg y una unidad de 5000 kg / 30 m³ y un operador disponible
  When Operaciones asigna la unidad y el operador
  Then la orden pasa a UNIDAD_ASIGNADA
  And se publica el evento RecursosAsignados

Scenario: Unidad sin capacidad suficiente
  Given una orden de 800 kg y una unidad de 500 kg
  When Operaciones intenta asignarla
  Then la API responde 422 con el código RecursosNoDisponibles y el motivo "no es adecuada"
  And la orden sigue CONFIRMADA

Scenario: Operador no disponible
  Given un operador marcado como no disponible
  When Operaciones intenta asignarlo
  Then la API responde 422 con el motivo "no está disponible"
```

Pruebas: `test_casos_de_uso.py::test_cu03_asigna_unidad_y_operador_adecuados`, `test_casos_de_uso.py::test_cu03_unidad_sin_capacidad_suficiente_se_rechaza`, `test_casos_de_uso.py::test_cu03_operador_no_disponible_no_cambia_nada`, `test_especificaciones.py::test_y_exige_ambas_y_reporta_los_motivos_de_las_que_fallan`, `test_supuestos_pendientes.py::test_s01_limite_propio_de_peso_rechaza_aunque_la_unidad_tenga_capacidad`

## US-08: Reasignación de operador

**Como** responsable de Operaciones, **quiero** actualizar la asignación cuando un operador no está disponible, **para** mantener la continuidad del servicio y conservar el historial del cambio.

- Requisitos: RF-07 · Necesidades: N2, N5 · BPMN: G2, T7
- API: `POST /ordenes/{orden_id}/asignacion`, `PUT /operadores/{operador_id}/disponibilidad`
- Componentes: `domain.orden_de_servicio.OrdenDeServicio.asignar_recursos`, `application.handlers.CambiarDisponibilidadDeOperadorHandler`

```gherkin
Scenario: Reasignación con historial
  Given una orden UNIDAD_ASIGNADA con el operador OP-1
  And el operador OP-2 está disponible
  When Operaciones reasigna la orden a OP-2
  Then la asignación vigente es OP-2
  And el historial conserva la asignación anterior y registra la actualización
```

Pruebas: `test_casos_de_uso.py::test_cu03_reasignar_conserva_el_historial`, `test_paquete_de_datos.py::test_diferencia_documentada_repetir_aprobacion_es_una_reasignacion_valida`, `test_maquina_de_estados.py::test_reasignar_deja_el_servicio_en_unidad_asignada`

## US-09: Recepción y validación de mercancía

**Como** operador, **quiero** registrar la recepción y validar la mercancía contra lo declarado, **para** detectar diferencias desde el origen y conservar la evidencia.

- Requisitos: RF-10 · Necesidades: N4, N5 · BPMN: T9, G3, T10, T14
- API: `POST /ordenes/{orden_id}/recepcion`, `POST /ordenes/{orden_id}/incidencias`
- Componentes: `domain.orden_de_servicio.OrdenDeServicio.registrar_recepcion`, `domain.especificaciones.recepcion_documentada`, `application.handlers.RegistrarRecepcionHandler`

```gherkin
Scenario: Recepción con evidencia
  Given una orden UNIDAD_ASIGNADA
  When el operador registra la recepción con una fotografía de recepción
  Then la orden pasa a RECOLECTADO
  And la evidencia queda asociada a la orden

Scenario: Recepción sin evidencia válida
  Given una orden UNIDAD_ASIGNADA
  When el operador registra la recepción con una evidencia de otro evento
  Then la API responde 400 con el código DatosInvalidos

Scenario: Mercancía diferente a la declarada
  Given mercancía distinta a lo declarado
  When el operador registra una incidencia MERCANCIA_DIFERENTE con evidencia
  Then la incidencia queda en el historial sin cambiar el estado
```

Pruebas: `test_dominio.py::test_la_recepcion_exige_evidencia_de_recepcion_y_deja_la_orden_recolectada`, `test_dominio.py::test_mercancia_diferente_a_la_declarada_se_registra_como_incidencia_con_evidencia`, `test_catalogos_y_cambios.py::test_recorrido_operativo_por_handlers_y_listado_por_estado`

## US-10: Actualización de estados

**Como** Ventas, Operaciones u Operador, **quiero** registrar los cambios de estado según la actividad realizada, **para** conocer en qué etapa se encuentra cada servicio.

- Requisitos: RF-11 · Necesidades: N2 · BPMN: T4, T8, T10, T11, T16, T19
- API: `POST /ordenes/{orden_id}/traslado`, `POST /ordenes/{orden_id}/llegada`
- Componentes: `domain.maquina_de_estados.CICLO_DE_VIDA_DEL_SERVICIO`, `domain.orden_de_servicio.OrdenDeServicio.iniciar_traslado`, `domain.orden_de_servicio.OrdenDeServicio.registrar_llegada_a_destino`, `application.handlers.IniciarTrasladoHandler`, `application.handlers.RegistrarLlegadaHandler`

```gherkin
Scenario: Recorrido normal de estados
  Given una orden CONFIRMADA
  When se asignan recursos, se recibe la mercancía, inicia el traslado, llega a destino y se entrega
  Then los estados son UNIDAD_ASIGNADA, RECOLECTADO, EN_TRANSITO, LLEGADA_A_DESTINO y ENTREGADO
  And cada cambio queda en el historial

Scenario: Transición inválida
  Given una orden CONFIRMADA
  When se intenta registrar la llegada a destino
  Then la API responde 409 con el código TransicionDeEstadoInvalida y "se requiere EN_TRANSITO"
  And el estado no cambia
```

Pruebas: `test_maquina_de_estados.py::test_camino_feliz_recorre_los_ocho_estados_del_brd_en_orden`, `test_maquina_de_estados.py::test_transicion_invalida_explica_que_se_requeria`, `test_dominio.py::test_la_orden_exige_el_orden_de_los_estados`, `test_api.py::test_409_duplicado_y_transicion_invalida`, `test_paquete_de_datos.py::test_las_20_transiciones_se_ejecutan_con_el_codigo_real_y_cumplen_el_oraculo`

## US-11: Registro de incidencias

**Como** operador, **quiero** reportar incidencias y retrasos ocurridos durante el servicio, **para** que Operaciones conozca la situación sin depender de WhatsApp.

- Requisitos: RF-12 · Necesidades: N3, N5 · BPMN: B1, T12, T13, G4, T20, T21
- API: `POST /ordenes/{orden_id}/incidencias`, `POST /ordenes/{orden_id}/entrega`
- Componentes: `domain.orden_de_servicio.OrdenDeServicio.registrar_incidencia`, `domain.orden_de_servicio.Incidencia`, `application.handlers.RegistrarIncidenciaHandler`

```gherkin
Scenario: Incidencia durante el traslado
  Given una orden EN_TRANSITO
  When el operador reporta un RETRASO por tráfico
  Then la incidencia queda registrada y disponible para Operaciones
  And el estado sigue EN_TRANSITO

Scenario: Destinatario ausente
  Given una orden en LLEGADA_A_DESTINO
  When el operador registra DESTINATARIO_AUSENTE con evidencia
  Then la orden NO pasa a ENTREGADO
  And la incidencia queda con su evidencia

Scenario: Servicio terminado no admite incidencias
  Given una orden CANCELADA
  When se intenta registrar una incidencia
  Then la API responde 409
```

Pruebas: `test_dominio.py::test_toda_incidencia_queda_en_el_historial_sin_cambiar_estado`, `test_dominio.py::test_no_se_registran_incidencias_en_un_servicio_terminado`, `test_catalogos_y_cambios.py::test_incidencia_durante_el_servicio_no_cambia_el_estado`, `test_api.py::test_incidencia_en_destino_no_entrega_el_servicio`, `test_casos_de_uso.py::test_cu04_destinatario_ausente_registra_incidencia_y_no_entrega`

## US-12: Registro de llegada y entrega

**Como** operador, **quiero** registrar la llegada al destino y la realización de la entrega, **para** cerrar el servicio con los eventos correspondientes.

- Requisitos: RF-13 · Necesidades: N2, N4 · BPMN: T16, T17, T18, G4, T19
- API: `POST /ordenes/{orden_id}/llegada`, `POST /ordenes/{orden_id}/entrega`
- Componentes: `domain.orden_de_servicio.OrdenDeServicio.registrar_entrega`, `application.handlers.RegistrarEntregaHandler`, `domain.eventos.EntregaRegistrada`

```gherkin
Scenario: Entrega completa
  Given una orden en LLEGADA_A_DESTINO
  When el operador registra la entrega con receptor y evidencia
  Then la orden queda ENTREGADA
  And se publica el evento EntregaRegistrada

Scenario: No se entrega sin haber llegado
  Given una orden en CONFIRMADA
  When el operador intenta registrar la entrega
  Then la API responde 409 con el código TransicionDeEstadoInvalida
```

Pruebas: `test_casos_de_uso.py::test_cu04_entrega_completa`, `test_casos_de_uso.py::test_cu04_no_se_entrega_si_no_ha_llegado_a_destino`, `test_api.py::test_flujo_completo_desde_la_cotizacion_hasta_la_entrega_y_los_indicadores`

## US-13: Evidencia y receptor

**Como** operador, **quiero** asociar la evidencia de recepción y entrega y registrar quién recibió, **para** que las evidencias permanezcan ligadas al servicio.

- Requisitos: RF-13, RF-10 · Necesidades: N4 · BPMN: T10, T14, T19, T20
- API: `POST /ordenes/{orden_id}/recepcion`, `POST /ordenes/{orden_id}/entrega`
- Componentes: `domain.valores.Evidencia`, `domain.valores.Destinatario`, `domain.especificaciones.entrega_documentada`, `domain.especificaciones.ReceptorIdentificado`, `domain.especificaciones.EvidenciaDelEvento`

```gherkin
Scenario: Entrega con receptor y evidencia
  Given una orden en LLEGADA_A_DESTINO
  When el operador registra la entrega indicando quién recibió (INE-9) y una fotografía
  Then ambos quedan asociados a la orden y se conservan al recargarla

Scenario: Entrega sin receptor
  Given una orden en LLEGADA_A_DESTINO
  When el operador registra la entrega sin identificar a quien recibe
  Then la API responde 400 con el código DatosInvalidos
  And la orden sigue en LLEGADA_A_DESTINO
```

Pruebas: `test_casos_de_uso.py::test_cu04_entrega_sin_identificar_receptor_se_rechaza`, `test_especificaciones.py::test_entrega_documentada_exige_receptor_y_evidencia_de_entrega`, `test_especificaciones.py::test_evidencia_debe_corresponder_al_evento`, `test_persistencia_sql.py::test_la_orden_completa_sobrevive_a_guardar_y_cargar`, `test_supuestos_pendientes.py::test_s03_con_plazo_solo_se_conservan_las_vigentes`

## US-14: Consulta para Atención al Cliente

**Como** personal de Atención al Cliente, **quiero** consultar el estado, eventos, retrasos e incidencias de un servicio, **para** informar al cliente sin depender de Operaciones.

- Requisitos: RF-14 · Necesidades: N3, N6 · BPMN: S3, T22, E8, DS1
- API: `GET /ordenes/{orden_id}/estado`, `GET /ordenes`
- Componentes: `application.handlers.ConsultarEstadoDelServicioHandler`, `application.dto.EstadoDelServicioDTO`, `application.puertos.IConsultaDeServicios`, `infrastructure.sql.consulta.SqlConsultaDeServicios`

```gherkin
Scenario: Consulta de un servicio
  Given una orden con eventos y una incidencia RETRASO
  When Atención al Cliente consulta el estado
  Then ve el estado actual, los eventos, los retrasos, las incidencias y las acciones permitidas

Scenario: Servicio inexistente
  Given un identificador que no existe
  When Atención al Cliente lo consulta
  Then la API responde 404
```

Pruebas: `test_casos_de_uso.py::test_cu05_atencion_al_cliente_consulta_estado_eventos_e_incidencias`, `test_api.py::test_404_recursos_inexistentes`

## US-15: Indicadores históricos

**Como** responsable de Operaciones, **quiero** consultar información histórica sobre tiempos, retrasos, incidencias y cumplimiento, **para** medir el desempeño de la operación.

- Requisitos: RF-15 · Necesidades: N7 · BPMN: S4, T23, E7, DS1
- API: `GET /indicadores`
- Componentes: `application.handlers.ConsultarIndicadoresHandler`, `application.dto.IndicadoresDTO`, `infrastructure.vistas.dto_indicadores`

```gherkin
Scenario: Indicadores del periodo
  Given una entrega en plazo y otra tardía respecto de su fecha requerida
  When Operaciones consulta los indicadores del periodo
  Then entregas realizadas = 2, entregas a tiempo = 1 y cumplimiento = 0.5 (S-05)

Scenario: Sin entregas no hay cumplimiento
  Given un periodo sin entregas
  When se consultan los indicadores
  Then el cumplimiento no está definido (null)
```

Pruebas: `test_casos_de_uso.py::test_cu05_indicadores_historicos`, `test_supuestos_pendientes.py::test_s05_cumplimiento_es_entregas_a_tiempo_sobre_entregas_realizadas`, `test_supuestos_pendientes.py::test_s05_sin_entregas_el_cumplimiento_no_esta_definido`

## US-16: Controles para carga de alto valor

**Como** responsable de Operaciones, **quiero** aplicar controles adicionales de seguimiento a las cargas de alto valor, **para** reducir el riesgo de pérdida; condiciones definitivas pendientes (supuesto S-02).

- Requisitos: RF-16 · Necesidades: N8 · BPMN: G2 (S-02)
- API: `POST /ordenes/{orden_id}/autorizacion-alto-valor`, `POST /ordenes/{orden_id}/asignacion`
- Componentes: `domain.especificaciones.control_de_alto_valor_cumplido`, `domain.especificaciones.CargaDeAltoValor`, `domain.especificaciones.AltoValorAutorizado`, `application.handlers.AutorizarCargaDeAltoValorHandler`

```gherkin
Scenario: Alto valor sin autorizar
  Given una orden con carga de alto valor
  When Operaciones intenta asignar recursos sin autorizarla
  Then la API responde 422 con el código ControlDeAltoValorPendiente

Scenario: Alto valor autorizado
  Given una orden con carga de alto valor
  When Operaciones la autoriza y después asigna recursos
  Then la asignación se realiza y la autorización queda en el historial

Scenario: Carga normal no requiere autorización
  Given una orden con carga que no es de alto valor
  When Operaciones intenta autorizarla
  Then se rechaza porque no aplica
```

Pruebas: `test_supuestos_pendientes.py::test_s02_alto_valor_exige_autorizacion_antes_de_asignar`, `test_supuestos_pendientes.py::test_s02_no_se_autoriza_una_carga_que_no_es_de_alto_valor`, `test_especificaciones.py::test_control_de_alto_valor_combina_no_y_o`, `test_api.py::test_422_reglas_de_negocio`

## US-17: Respuesta a la cotización

**Como** cliente, **quiero** aceptar, rechazar o solicitar ajustes a la cotización recibida, **para** decidir si contrato el servicio.

- Requisitos: RF-04, RF-03 · Necesidades: N1, N2 · BPMN: G1, E1, T3
- API: `POST /cotizaciones/{cotizacion_id}/respuesta`, `PUT /cotizaciones/{cotizacion_id}/solicitud`
- Componentes: `domain.cotizacion.Cotizacion.aceptar`, `domain.cotizacion.Cotizacion.rechazar`, `application.comandos.RespuestaDelCliente`, `application.handlers.ResponderCotizacionHandler`

```gherkin
Scenario: El cliente acepta
  Given una cotización elaborada (COTIZADO)
  When el cliente la acepta
  Then la cotización queda ACEPTADA y puede generarse la orden
  And se publica el evento CotizacionAceptada

Scenario: El cliente rechaza
  Given una cotización elaborada
  When el cliente la rechaza
  Then la cotización queda RECHAZADA y no admite otra respuesta

Scenario: El cliente pide ajustes
  Given una cotización elaborada
  When el cliente pide ajustes y Ventas modifica la solicitud
  Then el importe debe elaborarse de nuevo antes de poder aceptarla

Scenario: No se acepta una cotización sin elaborar
  Given una cotización en estado SOLICITADO
  When el cliente intenta aceptarla
  Then la API responde 422 con el código CotizacionNoElaborada
```

Pruebas: `test_casos_de_uso.py::test_cu01_cliente_acepta_la_cotizacion`, `test_casos_de_uso.py::test_cu01_cliente_rechaza_y_no_puede_responder_de_nuevo`, `test_catalogos_y_cambios.py::test_solicitar_ajustes_es_modificar_la_cotizacion_y_volver_a_elaborarla`, `test_api.py::test_422_no_se_genera_orden_de_una_cotizacion_sin_aceptar`
