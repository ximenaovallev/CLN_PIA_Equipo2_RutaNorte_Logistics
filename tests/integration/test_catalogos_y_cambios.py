"""Casos de uso de apoyo: catálogos, modificación de cotización, incidencias, cambios operativos y consultas."""
from datetime import date
from decimal import Decimal

from application.comandos import (
    CambiarDisponibilidadDeOperadorCommand, ConsultarClienteQuery, ConsultarCotizacionQuery, ConsultarEstadoDelServicioQuery,
    ConsultarOperadorQuery, ConsultarUnidadQuery, ElaborarCotizacionCommand, ListarOrdenesQuery,
    ModificarCotizacionCommand, RegistrarClienteCommand, RegistrarIncidenciaCommand, RegistrarOperadorCommand,
    RegistrarUnidadCommand, ResponderCotizacionCommand, RespuestaDelCliente as R, RevisarCambioOperativoCommand,
    SolicitarCambioOperativoCommand, SolicitarCotizacionCommand, AsignarRecursosCommand, IniciarTrasladoCommand,
    RegistrarLlegadaCommand, RegistrarRecepcionCommand,
)
from domain.orden_de_servicio import TipoDeIncidencia
from domain.valores import EventoAsociado
from helpers import evidencia, leer_orden


def test_registrar_catalogos_y_consultarlos(app):
    assert app.registrar_cliente.handle(RegistrarClienteCommand("C1", "ACME", "Monterrey")).exito
    assert app.registrar_unidad.handle(RegistrarUnidadCommand("U1", "Torton", 8000, 40)).exito
    assert app.registrar_operador.handle(RegistrarOperadorCommand("O1", "Luis")).exito
    assert app.consultar_cliente.handle(ConsultarClienteQuery("C1")).nombre == "ACME"
    assert app.consultar_unidad.handle(ConsultarUnidadQuery("U1")).volumen_m3 == 40
    assert app.consultar_operador.handle(ConsultarOperadorQuery("O1")).disponible is True
    assert app.cambiar_disponibilidad.handle(CambiarDisponibilidadDeOperadorCommand("O1", False)).exito
    assert app.consultar_operador.handle(ConsultarOperadorQuery("O1")).disponible is False


def test_catalogos_rechazan_duplicados_y_datos_invalidos(app):
    app.registrar_cliente.handle(RegistrarClienteCommand("C1", "ACME"))
    assert app.registrar_cliente.handle(RegistrarClienteCommand("C1", "Otro")).codigo_de_error == "EntidadYaExiste"
    assert app.registrar_unidad.handle(RegistrarUnidadCommand("U1", "Torton", 0, 40)).codigo_de_error == "DatosInvalidos"
    assert app.registrar_operador.handle(RegistrarOperadorCommand("", "Sin id")).codigo_de_error == "DatosInvalidos"
    app.registrar_unidad.handle(RegistrarUnidadCommand("U1", "Torton", 100, 4))
    assert app.registrar_unidad.handle(RegistrarUnidadCommand("U1", "Torton", 100, 4)).codigo_de_error == "EntidadYaExiste"
    app.registrar_operador.handle(RegistrarOperadorCommand("O1", "Luis"))
    assert app.registrar_operador.handle(RegistrarOperadorCommand("O1", "Luis")).codigo_de_error == "EntidadYaExiste"
    assert not app.cambiar_disponibilidad.handle(CambiarDisponibilidadDeOperadorCommand("NO", True)).exito


def test_solicitar_cotizacion_exige_cliente_registrado(app, solicitud):
    r = app.solicitar_cotizacion.handle(SolicitarCotizacionCommand("NO-EXISTE", solicitud))
    assert not r.exito and r.codigo_de_error == "EntidadNoEncontrada"


def test_ciclo_de_cotizacion_solicitada_cotizada_aceptada(app, solicitud):
    app.registrar_cliente.handle(RegistrarClienteCommand("C1", "ACME"))
    cid = app.solicitar_cotizacion.handle(SolicitarCotizacionCommand("C1", solicitud)).datos["cotizacion_id"]
    dto = app.consultar_cotizacion.handle(ConsultarCotizacionQuery(cid))
    assert dto.estado_del_servicio == "SOLICITADO" and dto.importe_mxn is None
    assert not app.responder_cotizacion.handle(ResponderCotizacionCommand(cid, R.ACEPTA)).exito  # aún sin importe
    assert app.elaborar_cotizacion.handle(ElaborarCotizacionCommand(cid, Decimal("1234.56"))).exito
    assert not app.elaborar_cotizacion.handle(ElaborarCotizacionCommand(cid, Decimal("0"))).exito
    dto = app.consultar_cotizacion.handle(ConsultarCotizacionQuery(cid))
    assert dto.estado_del_servicio == "COTIZADO" and dto.importe_mxn == Decimal("1234.56")
    assert app.responder_cotizacion.handle(ResponderCotizacionCommand(cid, R.ACEPTA)).exito
    assert app.consultar_cotizacion.handle(ConsultarCotizacionQuery(cid)).estado == "ACEPTADA"


def test_modificar_cotizacion_mientras_esta_en_proceso(app, solicitud):
    from dataclasses import replace
    from domain.valores import Ubicacion
    app.registrar_cliente.handle(RegistrarClienteCommand("C1", "ACME"))
    cid = app.solicitar_cotizacion.handle(SolicitarCotizacionCommand("C1", solicitud)).datos["cotizacion_id"]
    nueva = replace(solicitud, destino=Ubicacion("Guadalajara"))
    assert app.modificar_cotizacion.handle(ModificarCotizacionCommand(cid, nueva)).exito
    assert app.consultar_cotizacion.handle(ConsultarCotizacionQuery(cid)).destino == "Guadalajara"
    app.elaborar_cotizacion.handle(ElaborarCotizacionCommand(cid, Decimal("10")))
    app.responder_cotizacion.handle(ResponderCotizacionCommand(cid, R.ACEPTA))
    r = app.modificar_cotizacion.handle(ModificarCotizacionCommand(cid, solicitud))
    assert not r.exito and r.codigo_de_error == "CotizacionNoModificable"


def test_incidencia_durante_el_servicio_no_cambia_el_estado(orden_confirmada):
    app, oid = orden_confirmada
    r = app.registrar_incidencia.handle(RegistrarIncidenciaCommand(
        oid, TipoDeIncidencia.UNIDAD_AVERIADA, "Falla mecánica", evidencia(EventoAsociado.INCIDENCIA)))
    assert r.exito and r.datos["estado"] == "CONFIRMADO"
    dto = app.consultar_estado.handle(ConsultarEstadoDelServicioQuery(oid))
    assert dto.incidencias == ["UNIDAD_AVERIADA: Falla mecánica"] and dto.estado_actual == "CONFIRMADO"
    assert "ASIGNAR_RECURSOS" in dto.acciones_permitidas and "CANCELAR" in dto.acciones_permitidas


def test_cambio_operativo_pendiente_bloquea_las_operaciones_hasta_revisarse(orden_confirmada):
    app, oid = orden_confirmada
    assert app.solicitar_cambio.handle(SolicitarCambioOperativoCommand(oid, "Cliente", "Otro horario")).exito
    assert not app.solicitar_cambio.handle(SolicitarCambioOperativoCommand(oid, "Cliente", "Otro más")).exito
    r = app.asignar_recursos.handle(AsignarRecursosCommand(oid, "U-GRANDE", "OP-1"))
    assert r.codigo_de_error == "CambioPendienteDeRevision"
    assert app.consultar_estado.handle(ConsultarEstadoDelServicioQuery(oid)).cambio_operativo_pendiente == "Otro horario"
    assert app.revisar_cambio.handle(RevisarCambioOperativoCommand(oid, "Operaciones", False, "No es viable")).exito
    assert not app.revisar_cambio.handle(RevisarCambioOperativoCommand(oid, "Operaciones", True)).exito  # ya no hay cambio
    assert app.asignar_recursos.handle(AsignarRecursosCommand(oid, "U-GRANDE", "OP-1")).exito


def test_recorrido_operativo_por_handlers_y_listado_por_estado(orden_confirmada):
    app, oid = orden_confirmada
    assert not app.iniciar_traslado.handle(IniciarTrasladoCommand(oid)).exito
    app.asignar_recursos.handle(AsignarRecursosCommand(oid, "U-GRANDE", "OP-1"))
    assert app.registrar_recepcion.handle(RegistrarRecepcionCommand(oid, evidencia(EventoAsociado.RECEPCION))).exito
    assert app.iniciar_traslado.handle(IniciarTrasladoCommand(oid)).exito
    assert app.registrar_llegada.handle(RegistrarLlegadaCommand(oid)).exito
    assert [o.orden_id for o in app.listar_ordenes.handle(ListarOrdenesQuery("LLEGADA_A_DESTINO", 10))] == [oid]
    assert app.listar_ordenes.handle(ListarOrdenesQuery("ENTREGADO", 10)) == []
    assert len(app.listar_ordenes.handle(ListarOrdenesQuery(None, 10))) == 1
    assert leer_orden(app, oid).estado_actual().value == "LLEGADA_A_DESTINO"


def test_solicitar_ajustes_es_modificar_la_cotizacion_y_volver_a_elaborarla(app, solicitud):
    """US-17: si el cliente pide ajustes, Ventas modifica la solicitud (US-03) y debe elaborar un nuevo importe."""
    from dataclasses import replace
    from domain.valores import Ubicacion
    app.registrar_cliente.handle(RegistrarClienteCommand("C1", "ACME"))
    cid = app.solicitar_cotizacion.handle(SolicitarCotizacionCommand("C1", solicitud)).datos["cotizacion_id"]
    app.elaborar_cotizacion.handle(ElaborarCotizacionCommand(cid, Decimal("1000")))
    assert app.modificar_cotizacion.handle(
        ModificarCotizacionCommand(cid, replace(solicitud, destino=Ubicacion("Saltillo")))).exito
    dto = app.consultar_cotizacion.handle(ConsultarCotizacionQuery(cid))
    assert dto.estado == "EN_PROCESO" and dto.estado_del_servicio == "SOLICITADO" and dto.importe_mxn is None
    assert not app.responder_cotizacion.handle(ResponderCotizacionCommand(cid, R.ACEPTA)).exito  # falta nuevo importe
    assert app.elaborar_cotizacion.handle(ElaborarCotizacionCommand(cid, Decimal("1100"))).exito
    assert app.responder_cotizacion.handle(ResponderCotizacionCommand(cid, R.ACEPTA)).exito
