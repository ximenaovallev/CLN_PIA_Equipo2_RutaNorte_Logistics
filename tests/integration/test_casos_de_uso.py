"""Un recorrido por cada caso de uso (CU-01 a CU-05) con su flujo normal y su excepción."""
from datetime import date, datetime, timezone

from application.comandos import (
    AsignarRecursosCommand, CambiarDisponibilidadDeOperadorCommand, ConsultarEstadoDelServicioQuery, ConsultarIndicadoresQuery, ListarOrdenesQuery,
    GenerarOrdenDeServicioCommand, RegistrarEntregaCommand, RespuestaDelCliente as R,
    ResponderCotizacionCommand,
)
from domain.cotizacion import EstadoCotizacion
from domain.eventos import (
    CotizacionAceptada, EntregaRegistrada, IncidenciaRegistrada, OrdenDeServicioGenerada, RecursosAsignados,
)
from domain.orden_de_servicio import EstadoServicio, TipoDeIncidencia
from domain.valores import Destinatario
from helpers import cambiar_orden, contar_eventos, leer_cotizacion, leer_operador, leer_orden


# ---------------- CU-01 Responder cotización ----------------
def test_cu01_cliente_acepta_la_cotizacion(mundo):
    r = mundo.responder_cotizacion.handle(ResponderCotizacionCommand("COT-1", R.ACEPTA))
    assert r.exito
    assert leer_cotizacion(mundo, "COT-1").estado is EstadoCotizacion.ACEPTADA
    assert contar_eventos(mundo, CotizacionAceptada) > 0


def test_cu01_cliente_rechaza_y_no_puede_responder_de_nuevo(mundo):
    assert mundo.responder_cotizacion.handle(ResponderCotizacionCommand("COT-1", R.RECHAZA)).exito
    r = mundo.responder_cotizacion.handle(ResponderCotizacionCommand("COT-1", R.ACEPTA))
    assert not r.exito and "RECHAZADA" in r.mensaje_de_negocio


# ---------------- CU-02 Generar orden de servicio ----------------
def test_cu02_orden_se_genera_solo_tras_aceptacion(mundo):
    cmd = GenerarOrdenDeServicioCommand("COT-1", "MTY-QRO", datetime(2026, 11, 2, 8, tzinfo=timezone.utc))
    antes = mundo.generar_orden.handle(cmd)
    assert not antes.exito
    assert not mundo.listar_ordenes.handle(ListarOrdenesQuery(None, 10))
    mundo.responder_cotizacion.handle(ResponderCotizacionCommand("COT-1", R.ACEPTA))
    r = mundo.generar_orden.handle(cmd)
    assert r.exito
    orden = leer_orden(mundo, r.datos["orden_id"])
    assert orden.estado_actual() is EstadoServicio.CONFIRMADO
    assert len(orden.historial) == 1
    assert contar_eventos(mundo, OrdenDeServicioGenerada) > 0


# ---------------- CU-03 Asignar unidad y operador ----------------
def test_cu03_asigna_unidad_y_operador_adecuados(orden_confirmada):
    app, orden_id = orden_confirmada
    r = app.asignar_recursos.handle(AsignarRecursosCommand(orden_id, "U-GRANDE", "OP-1"))
    assert r.exito
    orden = leer_orden(app, orden_id)
    assert orden.estado_actual() is EstadoServicio.UNIDAD_ASIGNADA
    assert orden.asignacion.operador_id == "OP-1"
    assert contar_eventos(app, RecursosAsignados) > 0


def test_cu03_operador_no_disponible_no_cambia_nada(orden_confirmada):
    app, orden_id = orden_confirmada
    r = app.asignar_recursos.handle(AsignarRecursosCommand(orden_id, "U-GRANDE", "OP-2"))
    assert not r.exito and "no está disponible" in r.mensaje_de_negocio
    orden = leer_orden(app, orden_id)
    assert orden.estado_actual() is EstadoServicio.CONFIRMADO and orden.asignacion is None


def test_cu03_unidad_sin_capacidad_suficiente_se_rechaza(orden_confirmada):
    app, orden_id = orden_confirmada
    r = app.asignar_recursos.handle(AsignarRecursosCommand(orden_id, "U-CHICA", "OP-1"))
    assert not r.exito and "no es adecuada" in r.mensaje_de_negocio


def test_cu03_reasignar_conserva_el_historial(orden_confirmada):
    app, orden_id = orden_confirmada
    app.asignar_recursos.handle(AsignarRecursosCommand(orden_id, "U-GRANDE", "OP-1"))
    assert app.cambiar_disponibilidad.handle(CambiarDisponibilidadDeOperadorCommand("OP-2", True)).exito
    r = app.asignar_recursos.handle(AsignarRecursosCommand(orden_id, "U-GRANDE", "OP-2"))
    assert r.exito
    historial = [e.descripcion for e in leer_orden(app, orden_id).historial]
    assert any("Asignación actualizada" in d for d in historial)
    assert any("asignados" in d for d in historial)  # la primera asignación sigue registrada


def test_cu03_recurso_inexistente_es_error_de_negocio(orden_confirmada):
    app, orden_id = orden_confirmada
    r = app.asignar_recursos.handle(AsignarRecursosCommand(orden_id, "NO-EXISTE", "OP-1"))
    assert not r.exito and "No existe la unidad" in r.mensaje_de_negocio


# ---------------- CU-04 Registrar entrega o incidencia ----------------
def test_cu04_entrega_completa(orden_en_destino, evidencia):
    app, orden_id = orden_en_destino
    r = app.registrar_entrega.handle(RegistrarEntregaCommand(orden_id, Destinatario("INE-123"), evidencia()))
    assert r.exito
    orden = leer_orden(app, orden_id)
    assert orden.estado_actual() is EstadoServicio.ENTREGADO
    assert orden.destinatario == Destinatario("INE-123") and len(orden.evidencias_entrega) == 1
    assert contar_eventos(app, EntregaRegistrada) > 0


def test_cu04_destinatario_ausente_registra_incidencia_y_no_entrega(orden_en_destino, evidencia):
    app, orden_id = orden_en_destino
    r = app.registrar_entrega.handle(RegistrarEntregaCommand(
        orden_id, None, evidencia(), TipoDeIncidencia.DESTINATARIO_AUSENTE, "Nadie recibió"))
    assert r.exito
    orden = leer_orden(app, orden_id)
    assert orden.estado_actual() is EstadoServicio.LLEGADA_A_DESTINO  # no pasa a ENTREGADO
    assert orden.incidencias[0].tipo is TipoDeIncidencia.DESTINATARIO_AUSENTE
    assert len(orden.incidencias[0].evidencias) == 1
    assert contar_eventos(app, IncidenciaRegistrada) > 0


def test_cu04_no_se_entrega_si_no_ha_llegado_a_destino(orden_confirmada, evidencia):
    app, orden_id = orden_confirmada
    r = app.registrar_entrega.handle(RegistrarEntregaCommand(orden_id, Destinatario("X"), evidencia()))
    assert not r.exito and "LLEGADA_A_DESTINO" in r.mensaje_de_negocio


def test_cu04_entrega_sin_identificar_receptor_se_rechaza(orden_en_destino, evidencia):
    app, orden_id = orden_en_destino
    r = app.registrar_entrega.handle(RegistrarEntregaCommand(orden_id, None, evidencia()))
    assert not r.exito
    assert leer_orden(app, orden_id).estado_actual() is EstadoServicio.LLEGADA_A_DESTINO


# ---------------- CU-05 Consultar estado (Query) ----------------
def test_cu05_atencion_al_cliente_consulta_estado_eventos_e_incidencias(orden_en_destino, evidencia):
    app, orden_id = orden_en_destino
    app.registrar_entrega.handle(RegistrarEntregaCommand(
        orden_id, None, evidencia(), TipoDeIncidencia.RETRASO, "Tráfico en carretera"))
    dto = app.consultar_estado.handle(ConsultarEstadoDelServicioQuery(orden_id))
    assert dto.estado_actual == "LLEGADA_A_DESTINO"
    assert dto.retrasos == ["Tráfico en carretera"]
    assert len(dto.eventos) >= 5 and dto.incidencias[0].startswith("RETRASO")


def test_cu05_indicadores_historicos(orden_en_destino, evidencia):
    app, orden_id = orden_en_destino
    app.registrar_entrega.handle(RegistrarEntregaCommand(orden_id, Destinatario("INE-1"), evidencia()))
    ind = app.consultar_indicadores.handle(ConsultarIndicadoresQuery(date(2020, 1, 1), date(2100, 1, 1)))
    assert ind.ordenes_en_el_periodo == 1 and ind.entregas_realizadas == 1
    assert len(ind.tiempos_reales_de_entrega_horas) == 1
