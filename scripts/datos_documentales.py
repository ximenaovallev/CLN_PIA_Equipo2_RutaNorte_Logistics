"""Fuente única de la documentación de análisis: requisitos, historias de usuario con Gherkin y matriz de trazabilidad.

`scripts/generar_docs.py` produce los .md y .feature a partir de este archivo y `tests/test_trazabilidad.py` verifica
que cada referencia (prueba, componente de código, endpoint, elemento BPMN) exista de verdad.
"""
from __future__ import annotations

T = "tests/"
U, I = T + "unit/", T + "integration/"

# ------------------------------------------------------------------ Requisitos (BRD refinado)
REQUISITOS = [
    # id, necesidad(es), descripción
    ("RF-01", "N1", "Registrar la solicitud de cotización con origen, destino, mercancía, peso, dimensiones, fecha requerida y características especiales."),
    ("RF-02", "N1, N2", "Ventas elabora la cotización capturando su importe en MXN; el servicio pasa de SOLICITADO a COTIZADO."),
    ("RF-03", "N1", "Ventas puede modificar la solicitud solo mientras la cotización está en proceso; al modificarla debe elaborarse de nuevo el importe."),
    ("RF-04", "N1, N2", "El cliente acepta o rechaza la cotización elaborada; solo una cotización aceptada puede originar una orden. Pedir ajustes equivale a RF-03."),
    ("RF-05", "N1, N2", "La orden de servicio se genera después de la aceptación, queda CONFIRMADA y registra el primer evento en su historial."),
    ("RF-06", "N2, N5", "Operaciones asigna unidad y operador: la unidad debe tener capacidad suficiente y el operador debe estar disponible."),
    ("RF-07", "N2, N5", "Si el operador no está disponible, Operaciones reasigna y la asignación anterior permanece en el historial."),
    ("RF-08", "N2, N5", "Un cambio que afecta la operación se solicita a Operaciones y bloquea la orden hasta que se revise."),
    ("RF-09", "N1, N2, N5", "La cancelación de un servicio aceptado registra quién la solicita y el motivo; la autoridad es configurable (S-04)."),
    ("RF-10", "N4, N5", "El operador registra la recepción de la mercancía con evidencia; el servicio pasa a RECOLECTADO. Las diferencias respecto a lo declarado se registran como incidencia."),
    ("RF-11", "N2", "Todo cambio de estado sigue el ciclo de vida del servicio (máquina de estados) y queda en el historial."),
    ("RF-12", "N3, N5", "Las incidencias y retrasos se registran en el sistema, sin cambiar el estado, con evidencia opcional, disponibles para Operaciones."),
    ("RF-13", "N4", "La entrega exige llegada a destino, receptor identificado y evidencia; si no es posible, se registra una incidencia y el servicio no se entrega."),
    ("RF-14", "N3, N6", "Atención al Cliente consulta estado, eventos, retrasos e incidencias de un servicio sin depender de Operaciones."),
    ("RF-15", "N7", "Se consultan indicadores históricos: tiempos reales de entrega, retrasos, incidencias y cumplimiento (S-05)."),
    ("RF-16", "N8", "Una carga de alto valor requiere la autorización de Operaciones antes de asignar recursos (S-02)."),
    ("RNF-01", "N1", "Los importes son Decimal con dos decimales (nunca float)."),
    ("RNF-02", "—", "La API REST responde con 200/201/400/404/409/422 y está documentada con OpenAPI (Swagger UI en /docs). Todo mensaje al usuario está en lenguaje sencillo: dice qué pasó y qué hacer (campos `mensaje`, `que_sigue`, `que_hacer`), y cada formulario trae un ejemplo escrito."),
    ("RNF-03", "—", "La configuración (BD, supuestos S-01/S-03/S-04) llega por variables de entorno (12-Factor); no hay secretos en el repositorio."),
    ("RNF-04", "—", "Cobertura de pruebas de al menos 80 % verificada en CI."),
    ("RNF-05", "N1, N4", "Cada caso de uso es una transacción: si falla, no queda ningún cambio (Unit of Work)."),
    ("RNF-06", "—", "Trazabilidad verificable BRD → regla → componente → prueba."),
]

# ------------------------------------------------------------------ Historias de usuario
# Cada historia: id, título, rol (Como), quiero, para, RF, BPMN, endpoints, componentes, pruebas, escenarios
HISTORIAS = [
    dict(id="US-01", titulo="Solicitud de cotización", rf=["RF-01"], necesidades="N1, N2", bpmn="S1, T1",
         como="cliente", quiero="solicitar una cotización proporcionando origen, destino, mercancía, peso, dimensiones, fecha requerida y características especiales cuando sean necesarias",
         para="obtener una propuesta de transporte adecuada",
         api=["POST /cotizaciones"], componentes=["domain.cotizacion.Cotizacion", "domain.valores.SolicitudDeCotizacion", "application.handlers.SolicitarCotizacionHandler"],
         pruebas=[I + "test_catalogos_y_cambios.py::test_ciclo_de_cotizacion_solicitada_cotizada_aceptada", I + "test_catalogos_y_cambios.py::test_solicitar_cotizacion_exige_cliente_registrado", I + "test_api.py::test_400_cuerpo_incompleto_o_valores_invalidos"],
         escenarios=[
             ("Solicitud registrada con los datos proporcionados", ["Given que el cliente CLI-1 está registrado", "When solicita una cotización de Monterrey a Querétaro con 800 kg de refacciones de 2 x 1.5 x 1.5 m para el 2026-12-01", "Then se registra la solicitud en estado SOLICITADO", "And se devuelve el identificador de la cotización con código 201"]),
             ("Datos inválidos no se registran", ["Given que el cliente CLI-1 está registrado", "When solicita una cotización con peso de -5 kg", "Then la API responde 400 con el código DatosInvalidos", "And no se crea ninguna cotización"]),
             ("El solicitante debe existir", ["Given que el cliente NO-EXISTE no está registrado", "When solicita una cotización", "Then la API responde 404 con el código EntidadNoEncontrada"]),
         ]),
    dict(id="US-02", titulo="Elaboración de cotización", rf=["RF-02", "RNF-01"], necesidades="N1, N2", bpmn="T2",
         como="vendedor", quiero="elaborar una cotización utilizando la información proporcionada por el cliente", para="presentar al cliente una propuesta con su importe",
         api=["PUT /cotizaciones/{cotizacion_id}/importe"], componentes=["domain.cotizacion.Cotizacion.elaborar", "domain.maquina_de_estados.MaquinaDeEstados", "application.handlers.ElaborarCotizacionHandler"],
         pruebas=[I + "test_catalogos_y_cambios.py::test_ciclo_de_cotizacion_solicitada_cotizada_aceptada", I + "test_api.py::test_cotizacion_conserva_el_importe_decimal_exacto"],
         escenarios=[
             ("Cotización elaborada", ["Given una solicitud de cotización en estado SOLICITADO", "When Ventas registra el importe 1234.56 MXN", "Then el servicio pasa a COTIZADO", "And el importe se conserva exacto como Decimal"]),
             ("El importe debe ser positivo", ["Given una solicitud de cotización en estado SOLICITADO", "When Ventas registra el importe 0", "Then la API responde 400 y la cotización sigue en SOLICITADO"]),
         ]),
    dict(id="US-03", titulo="Modificación de cotización", rf=["RF-03"], necesidades="N1", bpmn="G1, T3",
         como="vendedor", quiero="modificar una cotización mientras está en proceso", para="corregir o ajustar la información antes de que el cliente responda",
         api=["PUT /cotizaciones/{cotizacion_id}/solicitud"], componentes=["domain.cotizacion.Cotizacion.modificar", "domain.especificaciones.CotizacionEnProceso", "application.handlers.ModificarCotizacionHandler"],
         pruebas=[U + "test_dominio.py::test_cotizacion_solo_se_modifica_mientras_esta_en_proceso", I + "test_catalogos_y_cambios.py::test_modificar_cotizacion_mientras_esta_en_proceso", I + "test_api.py::test_modificar_solicitud_solo_mientras_esta_en_proceso"],
         escenarios=[
             ("Modificación mientras está en proceso", ["Given una cotización en proceso", "When Ventas cambia el destino a Guadalajara", "Then la información actualizada queda registrada"]),
             ("No se modifica una cotización ya respondida", ["Given una cotización que el cliente rechazó", "When Ventas intenta modificarla", "Then la API responde 409 con el código CotizacionNoModificable"]),
         ]),
    dict(id="US-04", titulo="Revisión de cambios operativos", rf=["RF-08"], necesidades="N2, N5", bpmn="S2, T5, G5, T5B",
         como="responsable de Operaciones", quiero="revisar los cambios que afectan una orden de servicio", para="evitar que la operación continúe con condiciones no validadas",
         api=["POST /ordenes/{orden_id}/cambios-operativos", "PUT /ordenes/{orden_id}/cambios-operativos/revision"],
         componentes=["domain.orden_de_servicio.OrdenDeServicio.solicitar_cambio_operativo", "domain.orden_de_servicio.OrdenDeServicio.revisar_cambio_operativo", "domain.especificaciones.CambioOperativoPendiente", "application.handlers.SolicitarCambioOperativoHandler", "application.handlers.RevisarCambioOperativoHandler"],
         pruebas=[I + "test_catalogos_y_cambios.py::test_cambio_operativo_pendiente_bloquea_las_operaciones_hasta_revisarse", I + "test_api.py::test_cambio_operativo_bloquea_y_se_revisa", U + "test_especificaciones.py::test_sin_cambio_pendiente"],
         escenarios=[
             ("Un cambio pendiente bloquea la orden", ["Given una orden CONFIRMADA", "When el cliente solicita cambiar el horario de recolección", "Then el cambio queda pendiente de revisión", "And asignar recursos responde 409 con el código CambioPendienteDeRevision"]),
             ("Operaciones revisa y la orden continúa", ["Given una orden con un cambio pendiente", "When Operaciones aprueba o rechaza el cambio", "Then el cambio deja de estar pendiente y la orden puede continuar"]),
         ]),
    dict(id="US-05", titulo="Confirmación y registro de cancelación", rf=["RF-09", "RF-05"], necesidades="N1, N2, N5", bpmn="S2, T5, G5, T5A, E2, E2B",
         como="responsable del servicio", quiero="que la confirmación y las cancelaciones queden registradas", para="conservar quién solicitó la acción y por qué",
         api=["POST /ordenes/{orden_id}/cancelacion", "POST /ordenes"], componentes=["domain.orden_de_servicio.OrdenDeServicio.cancelar", "domain.servicios.AutoridadDeCancelacion", "application.handlers.CancelarServicioHandler"],
         pruebas=[I + "test_supuestos_pendientes.py::test_s04_cancelacion_registra_quien_y_motivo", I + "test_supuestos_pendientes.py::test_s04_rol_sin_autoridad_no_cancela", I + "test_supuestos_pendientes.py::test_s04_la_autoridad_es_configurable", I + "test_supuestos_pendientes.py::test_s04_exige_motivo_y_no_cancela_un_servicio_ya_cancelado", U + "test_maquina_de_estados.py::test_se_puede_cancelar_un_servicio_aceptado_que_no_ha_terminado"],
         escenarios=[
             ("Cancelación registrada con solicitante y motivo", ["Given una orden CONFIRMADA", "When Cliente ACME solicita cancelar por \"Ya no requiere el envío\" y Operaciones la autoriza", "Then la orden queda CANCELADA", "And se conservan quién la solicitó y el motivo"]),
             ("Un rol sin autoridad no cancela", ["Given una orden CONFIRMADA y que solo Operaciones puede cancelar", "When Ventas intenta autorizar la cancelación", "Then la API responde 422 con el código SinAutoridadParaCancelar", "And la orden sigue CONFIRMADA"]),
             ("Un servicio terminado no se cancela", ["Given una orden ya CANCELADA o ENTREGADA", "When se solicita cancelar de nuevo", "Then la API responde 409 con el código TransicionDeEstadoInvalida"]),
         ]),
    dict(id="US-06", titulo="Generación de orden", rf=["RF-05"], necesidades="N1, N2", bpmn="T4",
         como="responsable de Operaciones", quiero="generar una orden de servicio después de la aceptación de la cotización", para="iniciar formalmente la operación",
         api=["POST /ordenes"], componentes=["domain.orden_de_servicio.OrdenDeServicio.generar_desde", "domain.eventos.OrdenDeServicioGenerada", "application.handlers.GenerarOrdenDeServicioHandler"],
         pruebas=[I + "test_casos_de_uso.py::test_cu02_orden_se_genera_solo_tras_aceptacion", I + "test_api.py::test_422_no_se_genera_orden_de_una_cotizacion_sin_aceptar"],
         escenarios=[
             ("Orden generada tras la aceptación", ["Given una cotización ACEPTADA", "When Operaciones genera la orden con la ruta MTY-QRO y el horario de recolección", "Then la orden queda CONFIRMADA con un evento en su historial", "And se publica el evento OrdenDeServicioGenerada"]),
             ("Sin aceptación no hay orden", ["Given una cotización que el cliente no ha aceptado", "When Operaciones intenta generar la orden", "Then la API responde 422 con el código OrdenNoGenerable", "And no se crea ninguna orden"]),
         ]),
    dict(id="US-07", titulo="Asignación de recursos", rf=["RF-06"], necesidades="N2", bpmn="T6, G2, T8",
         como="responsable de Operaciones", quiero="asignar una unidad y un operador considerando carga, capacidad y disponibilidad", para="garantizar que el servicio se ejecute con recursos adecuados",
         api=["POST /ordenes/{orden_id}/asignacion"], componentes=["domain.servicios.AsignadorDeRecursos", "domain.especificaciones.UnidadConCapacidadSuficiente", "domain.especificaciones.OperadorDisponible", "domain.especificaciones.asignacion_permitida", "application.handlers.AsignarRecursosHandler"],
         pruebas=[I + "test_casos_de_uso.py::test_cu03_asigna_unidad_y_operador_adecuados", I + "test_casos_de_uso.py::test_cu03_unidad_sin_capacidad_suficiente_se_rechaza", I + "test_casos_de_uso.py::test_cu03_operador_no_disponible_no_cambia_nada", U + "test_especificaciones.py::test_y_exige_ambas_y_reporta_los_motivos_de_las_que_fallan", I + "test_supuestos_pendientes.py::test_s01_limite_propio_de_peso_rechaza_aunque_la_unidad_tenga_capacidad"],
         escenarios=[
             ("Asignación adecuada", ["Given una orden CONFIRMADA de 800 kg y una unidad de 5000 kg / 30 m³ y un operador disponible", "When Operaciones asigna la unidad y el operador", "Then la orden pasa a UNIDAD_ASIGNADA", "And se publica el evento RecursosAsignados"]),
             ("Unidad sin capacidad suficiente", ["Given una orden de 800 kg y una unidad de 500 kg", "When Operaciones intenta asignarla", "Then la API responde 422 con el código RecursosNoDisponibles y el motivo \"no es adecuada\"", "And la orden sigue CONFIRMADA"]),
             ("Operador no disponible", ["Given un operador marcado como no disponible", "When Operaciones intenta asignarlo", "Then la API responde 422 con el motivo \"no está disponible\""]),
         ]),
    dict(id="US-08", titulo="Reasignación de operador", rf=["RF-07"], necesidades="N2, N5", bpmn="G2, T7",
         como="responsable de Operaciones", quiero="actualizar la asignación cuando un operador no está disponible", para="mantener la continuidad del servicio y conservar el historial del cambio",
         api=["POST /ordenes/{orden_id}/asignacion", "PUT /operadores/{operador_id}/disponibilidad"], componentes=["domain.orden_de_servicio.OrdenDeServicio.asignar_recursos", "application.handlers.CambiarDisponibilidadDeOperadorHandler"],
         pruebas=[I + "test_casos_de_uso.py::test_cu03_reasignar_conserva_el_historial", I + "test_paquete_de_datos.py::test_diferencia_documentada_repetir_aprobacion_es_una_reasignacion_valida", U + "test_maquina_de_estados.py::test_reasignar_deja_el_servicio_en_unidad_asignada"],
         escenarios=[
             ("Reasignación con historial", ["Given una orden UNIDAD_ASIGNADA con el operador OP-1", "And el operador OP-2 está disponible", "When Operaciones reasigna la orden a OP-2", "Then la asignación vigente es OP-2", "And el historial conserva la asignación anterior y registra la actualización"]),
         ]),
    dict(id="US-09", titulo="Recepción y validación de mercancía", rf=["RF-10"], necesidades="N4, N5", bpmn="T9, G3, T10, T14",
         como="operador", quiero="registrar la recepción y validar la mercancía contra lo declarado", para="detectar diferencias desde el origen y conservar la evidencia",
         api=["POST /ordenes/{orden_id}/recepcion", "POST /ordenes/{orden_id}/incidencias"], componentes=["domain.orden_de_servicio.OrdenDeServicio.registrar_recepcion", "domain.especificaciones.recepcion_documentada", "application.handlers.RegistrarRecepcionHandler"],
         pruebas=[U + "test_dominio.py::test_la_recepcion_exige_evidencia_de_recepcion_y_deja_la_orden_recolectada", U + "test_dominio.py::test_mercancia_diferente_a_la_declarada_se_registra_como_incidencia_con_evidencia", I + "test_catalogos_y_cambios.py::test_recorrido_operativo_por_handlers_y_listado_por_estado"],
         escenarios=[
             ("Recepción con evidencia", ["Given una orden UNIDAD_ASIGNADA", "When el operador registra la recepción con una fotografía de recepción", "Then la orden pasa a RECOLECTADO", "And la evidencia queda asociada a la orden"]),
             ("Recepción sin evidencia válida", ["Given una orden UNIDAD_ASIGNADA", "When el operador registra la recepción con una evidencia de otro evento", "Then la API responde 400 con el código DatosInvalidos"]),
             ("Mercancía diferente a la declarada", ["Given mercancía distinta a lo declarado", "When el operador registra una incidencia MERCANCIA_DIFERENTE con evidencia", "Then la incidencia queda en el historial sin cambiar el estado"]),
         ]),
    dict(id="US-10", titulo="Actualización de estados", rf=["RF-11"], necesidades="N2", bpmn="T4, T8, T10, T11, T16, T19",
         como="Ventas, Operaciones u Operador", quiero="registrar los cambios de estado según la actividad realizada", para="conocer en qué etapa se encuentra cada servicio",
         api=["POST /ordenes/{orden_id}/traslado", "POST /ordenes/{orden_id}/llegada"], componentes=["domain.maquina_de_estados.CICLO_DE_VIDA_DEL_SERVICIO", "domain.orden_de_servicio.OrdenDeServicio.iniciar_traslado", "domain.orden_de_servicio.OrdenDeServicio.registrar_llegada_a_destino", "application.handlers.IniciarTrasladoHandler", "application.handlers.RegistrarLlegadaHandler"],
         pruebas=[U + "test_maquina_de_estados.py::test_camino_feliz_recorre_los_ocho_estados_del_brd_en_orden", U + "test_maquina_de_estados.py::test_transicion_invalida_explica_que_se_requeria", U + "test_dominio.py::test_la_orden_exige_el_orden_de_los_estados", I + "test_api.py::test_409_duplicado_y_transicion_invalida", I + "test_paquete_de_datos.py::test_las_20_transiciones_se_ejecutan_con_el_codigo_real_y_cumplen_el_oraculo"],
         escenarios=[
             ("Recorrido normal de estados", ["Given una orden CONFIRMADA", "When se asignan recursos, se recibe la mercancía, inicia el traslado, llega a destino y se entrega", "Then los estados son UNIDAD_ASIGNADA, RECOLECTADO, EN_TRANSITO, LLEGADA_A_DESTINO y ENTREGADO", "And cada cambio queda en el historial"]),
             ("Transición inválida", ["Given una orden CONFIRMADA", "When se intenta registrar la llegada a destino", "Then la API responde 409 con el código TransicionDeEstadoInvalida y \"se requiere EN_TRANSITO\"", "And el estado no cambia"]),
         ]),
    dict(id="US-11", titulo="Registro de incidencias", rf=["RF-12"], necesidades="N3, N5", bpmn="B1, T12, T13, G4, T20, T21",
         como="operador", quiero="reportar incidencias y retrasos ocurridos durante el servicio", para="que Operaciones conozca la situación sin depender de WhatsApp",
         api=["POST /ordenes/{orden_id}/incidencias", "POST /ordenes/{orden_id}/entrega"], componentes=["domain.orden_de_servicio.OrdenDeServicio.registrar_incidencia", "domain.orden_de_servicio.Incidencia", "application.handlers.RegistrarIncidenciaHandler"],
         pruebas=[U + "test_dominio.py::test_toda_incidencia_queda_en_el_historial_sin_cambiar_estado", U + "test_dominio.py::test_no_se_registran_incidencias_en_un_servicio_terminado", I + "test_catalogos_y_cambios.py::test_incidencia_durante_el_servicio_no_cambia_el_estado", I + "test_api.py::test_incidencia_en_destino_no_entrega_el_servicio", I + "test_casos_de_uso.py::test_cu04_destinatario_ausente_registra_incidencia_y_no_entrega"],
         escenarios=[
             ("Incidencia durante el traslado", ["Given una orden EN_TRANSITO", "When el operador reporta un RETRASO por tráfico", "Then la incidencia queda registrada y disponible para Operaciones", "And el estado sigue EN_TRANSITO"]),
             ("Destinatario ausente", ["Given una orden en LLEGADA_A_DESTINO", "When el operador registra DESTINATARIO_AUSENTE con evidencia", "Then la orden NO pasa a ENTREGADO", "And la incidencia queda con su evidencia"]),
             ("Servicio terminado no admite incidencias", ["Given una orden CANCELADA", "When se intenta registrar una incidencia", "Then la API responde 409"]),
         ]),
    dict(id="US-12", titulo="Registro de llegada y entrega", rf=["RF-13"], necesidades="N2, N4", bpmn="T16, T17, T18, G4, T19",
         como="operador", quiero="registrar la llegada al destino y la realización de la entrega", para="cerrar el servicio con los eventos correspondientes",
         api=["POST /ordenes/{orden_id}/llegada", "POST /ordenes/{orden_id}/entrega"], componentes=["domain.orden_de_servicio.OrdenDeServicio.registrar_entrega", "application.handlers.RegistrarEntregaHandler", "domain.eventos.EntregaRegistrada"],
         pruebas=[I + "test_casos_de_uso.py::test_cu04_entrega_completa", I + "test_casos_de_uso.py::test_cu04_no_se_entrega_si_no_ha_llegado_a_destino", I + "test_api.py::test_flujo_completo_desde_la_cotizacion_hasta_la_entrega_y_los_indicadores"],
         escenarios=[
             ("Entrega completa", ["Given una orden en LLEGADA_A_DESTINO", "When el operador registra la entrega con receptor y evidencia", "Then la orden queda ENTREGADA", "And se publica el evento EntregaRegistrada"]),
             ("No se entrega sin haber llegado", ["Given una orden en CONFIRMADA", "When el operador intenta registrar la entrega", "Then la API responde 409 con el código TransicionDeEstadoInvalida"]),
         ]),
    dict(id="US-13", titulo="Evidencia y receptor", rf=["RF-13", "RF-10"], necesidades="N4", bpmn="T10, T14, T19, T20",
         como="operador", quiero="asociar la evidencia de recepción y entrega y registrar quién recibió", para="que las evidencias permanezcan ligadas al servicio",
         api=["POST /ordenes/{orden_id}/recepcion", "POST /ordenes/{orden_id}/entrega"], componentes=["domain.valores.Evidencia", "domain.valores.Destinatario", "domain.especificaciones.entrega_documentada", "domain.especificaciones.ReceptorIdentificado", "domain.especificaciones.EvidenciaDelEvento"],
         pruebas=[I + "test_casos_de_uso.py::test_cu04_entrega_sin_identificar_receptor_se_rechaza", U + "test_especificaciones.py::test_entrega_documentada_exige_receptor_y_evidencia_de_entrega", U + "test_especificaciones.py::test_evidencia_debe_corresponder_al_evento", I + "test_persistencia_sql.py::test_la_orden_completa_sobrevive_a_guardar_y_cargar", I + "test_supuestos_pendientes.py::test_s03_con_plazo_solo_se_conservan_las_vigentes"],
         escenarios=[
             ("Entrega con receptor y evidencia", ["Given una orden en LLEGADA_A_DESTINO", "When el operador registra la entrega indicando quién recibió (INE-9) y una fotografía", "Then ambos quedan asociados a la orden y se conservan al recargarla"]),
             ("Entrega sin receptor", ["Given una orden en LLEGADA_A_DESTINO", "When el operador registra la entrega sin identificar a quien recibe", "Then la API responde 400 con el código DatosInvalidos", "And la orden sigue en LLEGADA_A_DESTINO"]),
         ]),
    dict(id="US-14", titulo="Consulta para Atención al Cliente", rf=["RF-14"], necesidades="N3, N6", bpmn="S3, T22, E8, DS1",
         como="personal de Atención al Cliente", quiero="consultar el estado, eventos, retrasos e incidencias de un servicio", para="informar al cliente sin depender de Operaciones",
         api=["GET /ordenes/{orden_id}/estado", "GET /ordenes"], componentes=["application.handlers.ConsultarEstadoDelServicioHandler", "application.dto.EstadoDelServicioDTO", "application.puertos.IConsultaDeServicios", "infrastructure.sql.consulta.SqlConsultaDeServicios"],
         pruebas=[I + "test_casos_de_uso.py::test_cu05_atencion_al_cliente_consulta_estado_eventos_e_incidencias", I + "test_api.py::test_404_recursos_inexistentes"],
         escenarios=[
             ("Consulta de un servicio", ["Given una orden con eventos y una incidencia RETRASO", "When Atención al Cliente consulta el estado", "Then ve el estado actual, los eventos, los retrasos, las incidencias y las acciones permitidas"]),
             ("Servicio inexistente", ["Given un identificador que no existe", "When Atención al Cliente lo consulta", "Then la API responde 404"]),
         ]),
    dict(id="US-15", titulo="Indicadores históricos", rf=["RF-15"], necesidades="N7", bpmn="S4, T23, E7, DS1",
         como="responsable de Operaciones", quiero="consultar información histórica sobre tiempos, retrasos, incidencias y cumplimiento", para="medir el desempeño de la operación",
         api=["GET /indicadores"], componentes=["application.handlers.ConsultarIndicadoresHandler", "application.dto.IndicadoresDTO", "infrastructure.vistas.dto_indicadores"],
         pruebas=[I + "test_casos_de_uso.py::test_cu05_indicadores_historicos", I + "test_supuestos_pendientes.py::test_s05_cumplimiento_es_entregas_a_tiempo_sobre_entregas_realizadas", I + "test_supuestos_pendientes.py::test_s05_sin_entregas_el_cumplimiento_no_esta_definido"],
         escenarios=[
             ("Indicadores del periodo", ["Given una entrega en plazo y otra tardía respecto de su fecha requerida", "When Operaciones consulta los indicadores del periodo", "Then entregas realizadas = 2, entregas a tiempo = 1 y cumplimiento = 0.5 (S-05)"]),
             ("Sin entregas no hay cumplimiento", ["Given un periodo sin entregas", "When se consultan los indicadores", "Then el cumplimiento no está definido (null)"]),
         ]),
    dict(id="US-16", titulo="Controles para carga de alto valor", rf=["RF-16"], necesidades="N8", bpmn="G2 (S-02)",
         como="responsable de Operaciones", quiero="aplicar controles adicionales de seguimiento a las cargas de alto valor", para="reducir el riesgo de pérdida; condiciones definitivas pendientes (supuesto S-02)",
         api=["POST /ordenes/{orden_id}/autorizacion-alto-valor", "POST /ordenes/{orden_id}/asignacion"], componentes=["domain.especificaciones.control_de_alto_valor_cumplido", "domain.especificaciones.CargaDeAltoValor", "domain.especificaciones.AltoValorAutorizado", "application.handlers.AutorizarCargaDeAltoValorHandler"],
         pruebas=[I + "test_supuestos_pendientes.py::test_s02_alto_valor_exige_autorizacion_antes_de_asignar", I + "test_supuestos_pendientes.py::test_s02_no_se_autoriza_una_carga_que_no_es_de_alto_valor", U + "test_especificaciones.py::test_control_de_alto_valor_combina_no_y_o", I + "test_api.py::test_422_reglas_de_negocio"],
         escenarios=[
             ("Alto valor sin autorizar", ["Given una orden con carga de alto valor", "When Operaciones intenta asignar recursos sin autorizarla", "Then la API responde 422 con el código ControlDeAltoValorPendiente"]),
             ("Alto valor autorizado", ["Given una orden con carga de alto valor", "When Operaciones la autoriza y después asigna recursos", "Then la asignación se realiza y la autorización queda en el historial"]),
             ("Carga normal no requiere autorización", ["Given una orden con carga que no es de alto valor", "When Operaciones intenta autorizarla", "Then se rechaza porque no aplica"]),
         ]),
    dict(id="US-17", titulo="Respuesta a la cotización", rf=["RF-04", "RF-03"], necesidades="N1, N2", bpmn="G1, E1, T3",
         como="cliente", quiero="aceptar, rechazar o solicitar ajustes a la cotización recibida", para="decidir si contrato el servicio",
         api=["POST /cotizaciones/{cotizacion_id}/respuesta", "PUT /cotizaciones/{cotizacion_id}/solicitud"], componentes=["domain.cotizacion.Cotizacion.aceptar", "domain.cotizacion.Cotizacion.rechazar", "application.comandos.RespuestaDelCliente", "application.handlers.ResponderCotizacionHandler"],
         pruebas=[I + "test_casos_de_uso.py::test_cu01_cliente_acepta_la_cotizacion", I + "test_casos_de_uso.py::test_cu01_cliente_rechaza_y_no_puede_responder_de_nuevo", I + "test_catalogos_y_cambios.py::test_solicitar_ajustes_es_modificar_la_cotizacion_y_volver_a_elaborarla", I + "test_api.py::test_422_no_se_genera_orden_de_una_cotizacion_sin_aceptar"],
         escenarios=[
             ("El cliente acepta", ["Given una cotización elaborada (COTIZADO)", "When el cliente la acepta", "Then la cotización queda ACEPTADA y puede generarse la orden", "And se publica el evento CotizacionAceptada"]),
             ("El cliente rechaza", ["Given una cotización elaborada", "When el cliente la rechaza", "Then la cotización queda RECHAZADA y no admite otra respuesta"]),
             ("El cliente pide ajustes", ["Given una cotización elaborada", "When el cliente pide ajustes y Ventas modifica la solicitud", "Then el importe debe elaborarse de nuevo antes de poder aceptarla"]),
             ("No se acepta una cotización sin elaborar", ["Given una cotización en estado SOLICITADO", "When el cliente intenta aceptarla", "Then la API responde 422 con el código CotizacionNoElaborada"]),
         ]),
]

# ------------------------------------------------------------------ Reglas del negocio → componente → prueba
REGLAS = [
    ("R-01", "La cotización solo se modifica mientras está en proceso", "RF-03", ["US-03"], "domain.especificaciones.CotizacionEnProceso", [U + "test_especificaciones.py::test_especificaciones_de_cotizacion_siguen_su_ciclo", U + "test_dominio.py::test_cotizacion_solo_se_modifica_mientras_esta_en_proceso"]),
    ("R-02", "Solo una cotización elaborada puede aceptarse", "RF-04", ["US-17"], "domain.especificaciones.CotizacionConImporte", [I + "test_catalogos_y_cambios.py::test_ciclo_de_cotizacion_solicitada_cotizada_aceptada"]),
    ("R-03", "La orden solo se genera tras la aceptación", "RF-05", ["US-06"], "domain.orden_de_servicio.OrdenDeServicio.generar_desde", [I + "test_casos_de_uso.py::test_cu02_orden_se_genera_solo_tras_aceptacion"]),
    ("R-04", "La unidad debe tener capacidad suficiente (peso y volumen)", "RF-06", ["US-07"], "domain.especificaciones.UnidadConCapacidadSuficiente", [I + "test_casos_de_uso.py::test_cu03_unidad_sin_capacidad_suficiente_se_rechaza", U + "test_especificaciones.py::test_la_unidad_sin_volumen_suficiente_no_es_adecuada"]),
    ("R-05", "El operador debe estar disponible", "RF-06", ["US-07", "US-08"], "domain.especificaciones.OperadorDisponible", [I + "test_casos_de_uso.py::test_cu03_operador_no_disponible_no_cambia_nada"]),
    ("R-06", "Topes propios de la empresa (supuesto S-01, configurable)", "RF-06", ["US-07"], "domain.especificaciones.DentroDeLosLimitesDeLaEmpresa", [U + "test_especificaciones.py::test_unidad_adecuada_considera_capacidad_de_la_unidad_y_limites_de_la_empresa", I + "test_supuestos_pendientes.py::test_s01_limite_propio_de_volumen_tambien_rechaza"]),
    ("R-07", "Reasignar conserva el historial", "RF-07", ["US-08"], "domain.orden_de_servicio.OrdenDeServicio.asignar_recursos", [I + "test_casos_de_uso.py::test_cu03_reasignar_conserva_el_historial"]),
    ("R-08", "Carga de alto valor: NO alto valor O autorizada (supuesto S-02)", "RF-16", ["US-16"], "domain.especificaciones.control_de_alto_valor_cumplido", [U + "test_especificaciones.py::test_control_de_alto_valor_combina_no_y_o"]),
    ("R-09", "Un cambio operativo pendiente bloquea la orden hasta su revisión", "RF-08", ["US-04"], "domain.especificaciones.sin_cambio_pendiente", [U + "test_especificaciones.py::test_sin_cambio_pendiente", I + "test_catalogos_y_cambios.py::test_cambio_operativo_pendiente_bloquea_las_operaciones_hasta_revisarse"]),
    ("R-10", "Los estados siguen el ciclo de vida del servicio (máquina de estados)", "RF-11", ["US-10"], "domain.maquina_de_estados.CICLO_DE_VIDA_DEL_SERVICIO", [U + "test_maquina_de_estados.py::test_todos_los_estados_son_alcanzables_desde_el_inicial", U + "test_maquina_de_estados.py::test_ningun_estado_no_terminal_es_callejon_sin_salida", U + "test_maquina_de_estados.py::test_no_se_cancela_antes_de_aceptar_ni_despues_de_terminar"]),
    ("R-11", "La recepción exige evidencia de recepción", "RF-10", ["US-09", "US-13"], "domain.especificaciones.recepcion_documentada", [U + "test_dominio.py::test_la_recepcion_exige_evidencia_de_recepcion_y_deja_la_orden_recolectada"]),
    ("R-12", "La entrega exige receptor y evidencia de entrega", "RF-13", ["US-12", "US-13"], "domain.especificaciones.entrega_documentada", [U + "test_especificaciones.py::test_entrega_documentada_exige_receptor_y_evidencia_de_entrega", I + "test_casos_de_uso.py::test_cu04_entrega_sin_identificar_receptor_se_rechaza"]),
    ("R-13", "Una incidencia no cambia el estado ni entrega el servicio", "RF-12", ["US-11"], "domain.orden_de_servicio.OrdenDeServicio.registrar_incidencia", [U + "test_dominio.py::test_toda_incidencia_queda_en_el_historial_sin_cambiar_estado", I + "test_casos_de_uso.py::test_cu04_destinatario_ausente_registra_incidencia_y_no_entrega"]),
    ("R-14", "La cancelación registra solicitante y motivo; la autoridad es configurable (S-04)", "RF-09", ["US-05"], "domain.servicios.AutoridadDeCancelacion", [I + "test_supuestos_pendientes.py::test_s04_la_autoridad_es_configurable", I + "test_supuestos_pendientes.py::test_s04_rol_sin_autoridad_no_cancela"]),
    ("R-15", "Las evidencias se conservan según el plazo configurable (S-03)", "RF-13", ["US-13"], "domain.valores.PoliticaDeConservacion", [I + "test_supuestos_pendientes.py::test_s03_sin_plazo_las_evidencias_no_caducan", I + "test_supuestos_pendientes.py::test_s03_con_plazo_solo_se_conservan_las_vigentes"]),
    ("R-16", "Cumplimiento = entregas en o antes de la fecha requerida ÷ entregas (S-05)", "RF-15", ["US-15"], "infrastructure.vistas.dto_indicadores", [I + "test_supuestos_pendientes.py::test_s05_cumplimiento_es_entregas_a_tiempo_sobre_entregas_realizadas"]),
    ("R-17", "Importes en Decimal", "RNF-01", ["US-02"], "domain.cotizacion.Cotizacion.elaborar", [I + "test_persistencia_sql.py::test_el_importe_se_guarda_como_decimal_exacto", I + "test_paquete_de_datos.py::test_total_se_calcula_con_decimal_sin_error_de_punto_flotante"]),
    ("R-18", "Cada caso de uso es una transacción atómica", "RNF-05", ["US-07"], "infrastructure.sql.unit_of_work.SqlUnitOfWork", [I + "test_persistencia_sql.py::test_error_de_dominio_revierte_la_transaccion", I + "test_persistencia_sql.py::test_salir_sin_confirmar_no_deja_nada", U + "test_dominio.py::test_unit_of_work_revierte_si_no_se_confirma"]),
    ("R-19", "Contrato de códigos HTTP 200/201/400/404/409/422", "RNF-02", ["US-01"], "api.errores.HTTP_POR_ERROR_DE_DOMINIO", [I + "test_api.py::test_400_cuerpo_incompleto_o_valores_invalidos", I + "test_api.py::test_404_recursos_inexistentes", I + "test_api.py::test_409_duplicado_y_transicion_invalida", I + "test_api.py::test_422_reglas_de_negocio", I + "test_api.py::test_health_y_openapi_documentado", I + "test_api.py::test_las_respuestas_correctas_explican_que_paso_y_que_sigue", I + "test_api.py::test_todo_error_trae_mensaje_claro_y_que_hacer_sin_terminos_tecnicos", I + "test_api.py::test_400_indica_en_palabras_cual_dato_falta_o_esta_mal", I + "test_api.py::test_direccion_inexistente_y_pagina_principal_llevan_a_la_ayuda", I + "test_api.py::test_swagger_esta_en_lenguaje_sencillo_con_ejemplos_y_sin_claves_tecnicas"]),
    ("R-21", "La cobertura mínima de 80 % se exige en CI y en docker compose", "RNF-04", [], ".github/workflows/ci.yml", [T + "test_trazabilidad.py::test_ci_y_compose_exigen_cobertura_minima_de_80"]),
    ("R-22", "Ninguna referencia de la matriz puede estar rota", "RNF-06", [], "tests/test_trazabilidad.py", [T + "test_trazabilidad.py::test_todo_requisito_esta_cubierto_por_una_historia_o_una_regla", T + "test_trazabilidad.py::test_todo_endpoint_de_la_api_esta_asociado_a_una_historia"]),
    ("R-20", "Configuración solo por variables de entorno", "RNF-03", [], "infrastructure.configuracion.Configuracion", [I + "test_persistencia_sql.py::test_configuracion_se_lee_solo_del_entorno"]),
]

ENDPOINTS_NO_HISTORIAS = ["GET /clientes/{cliente_id}", "POST /clientes", "POST /unidades", "GET /unidades/{unidad_id}", "POST /operadores", "GET /operadores/{operador_id}", "GET /cotizaciones/{cotizacion_id}", "GET /health"]
