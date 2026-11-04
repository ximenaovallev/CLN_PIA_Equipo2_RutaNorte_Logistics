"""Supuestos S-01 a S-05 (pendientes de validar con el stakeholder): se prueban como parámetros, no como hechos."""
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from application.comandos import (
    AsignarRecursosCommand, AutorizarCargaDeAltoValorCommand, CancelarServicioCommand, ConsultarIndicadoresQuery,
    GenerarOrdenDeServicioCommand, RegistrarEntregaCommand, RespuestaDelCliente as R, ResponderCotizacionCommand,
)
from domain.cotizacion import Cotizacion
from domain.orden_de_servicio import EstadoServicio, TipoDeIncidencia
from domain.valores import Asignacion, Destinatario, EventoAsociado, PoliticaDeConservacion
from helpers import HORARIO, cambiar_orden, evidencia, leer_orden
from conftest import preparar_mundo


def _orden(app, solicitud, **cambios_mercancia):
    """Cotización aceptada y orden generada; devuelve el id de la orden."""
    if cambios_mercancia:
        solicitud = replace(solicitud, mercancia=replace(solicitud.mercancia, **cambios_mercancia))
    preparar_mundo(app, solicitud, cotizaciones=("C",))
    assert app.responder_cotizacion.handle(ResponderCotizacionCommand("C", R.ACEPTA)).exito
    return app.generar_orden.handle(GenerarOrdenDeServicioCommand("C", "ruta", HORARIO)).datos["orden_id"]


# S-01 límites propios de capacidad
def test_s01_limite_propio_de_peso_rechaza_aunque_la_unidad_tenga_capacidad(fabrica_de_app, solicitud):
    app = fabrica_de_app(peso_maximo_kg=500)
    orden_id = _orden(app, solicitud)  # carga de 800 kg
    r = app.asignar_recursos.handle(AsignarRecursosCommand(orden_id, "U-GRANDE", "OP-1"))
    assert not r.exito and "no es adecuada" in r.mensaje_de_negocio


def test_s01_limite_propio_de_volumen_tambien_rechaza(fabrica_de_app, solicitud):
    app = fabrica_de_app(volumen_maximo_m3=1)
    orden_id = _orden(app, solicitud)  # 2 x 1.5 x 1.5 = 4.5 m³
    assert not app.asignar_recursos.handle(AsignarRecursosCommand(orden_id, "U-GRANDE", "OP-1")).exito


def test_s01_sin_limite_propio_solo_cuenta_la_capacidad_de_la_unidad(app, solicitud):
    orden_id = _orden(app, solicitud)
    assert app.asignar_recursos.handle(AsignarRecursosCommand(orden_id, "U-GRANDE", "OP-1")).exito


# S-02 carga de alto valor
def test_s02_alto_valor_exige_autorizacion_antes_de_asignar(app, solicitud):
    orden_id = _orden(app, solicitud, alto_valor=True)
    r = app.asignar_recursos.handle(AsignarRecursosCommand(orden_id, "U-GRANDE", "OP-1"))
    assert not r.exito and "alto valor" in r.mensaje_de_negocio
    assert app.autorizar_alto_valor.handle(AutorizarCargaDeAltoValorCommand(orden_id, "Operaciones")).exito
    assert app.asignar_recursos.handle(AsignarRecursosCommand(orden_id, "U-GRANDE", "OP-1")).exito
    assert any("alto valor autorizada" in e.descripcion for e in leer_orden(app, orden_id).historial)


def test_s02_no_se_autoriza_una_carga_que_no_es_de_alto_valor(app, solicitud):
    orden_id = _orden(app, solicitud)
    assert not app.autorizar_alto_valor.handle(AutorizarCargaDeAltoValorCommand(orden_id, "Operaciones")).exito


# S-03 conservación de evidencias
def test_s03_sin_plazo_las_evidencias_no_caducan(app, solicitud):
    orden_id = _orden(app, solicitud)
    cambiar_orden(app, orden_id, lambda o: (
        o.asignar_recursos(Asignacion("U-GRANDE", "OP-1")),
        o.registrar_recepcion(evidencia(EventoAsociado.RECEPCION, datetime(2000, 1, 1, tzinfo=timezone.utc)))))
    assert len(leer_orden(app, orden_id).evidencias(app.politica_de_conservacion)) == 1


def test_s03_con_plazo_solo_se_conservan_las_vigentes(fabrica_de_app, solicitud):
    app = fabrica_de_app(dias_de_conservacion=30)
    orden_id = _orden(app, solicitud)
    cambiar_orden(app, orden_id, lambda o: (
        o.asignar_recursos(Asignacion("U-GRANDE", "OP-1")),
        o.registrar_recepcion(evidencia(EventoAsociado.RECEPCION, datetime.now(timezone.utc) - timedelta(days=90))),
        o.registrar_incidencia(TipoDeIncidencia.RETRASO, "Demora", evidencia(EventoAsociado.INCIDENCIA))))
    o = leer_orden(app, orden_id)
    assert len(o.evidencias()) == 2
    assert len(o.evidencias(app.politica_de_conservacion)) == 1
    assert len(o.evidencias(PoliticaDeConservacion(30))) == 1


# S-04 cancelación
def test_s04_cancelacion_registra_quien_y_motivo(app, solicitud):
    orden_id = _orden(app, solicitud)
    r = app.cancelar_servicio.handle(CancelarServicioCommand(orden_id, "Cliente ACME", "Ya no requiere el envío"))
    assert r.exito
    o = leer_orden(app, orden_id)
    assert o.estado_actual() is EstadoServicio.CANCELADO
    assert o.cancelacion.solicitado_por == "Cliente ACME" and o.cancelacion.motivo == "Ya no requiere el envío"


def test_s04_rol_sin_autoridad_no_cancela(app, solicitud):
    orden_id = _orden(app, solicitud)
    r = app.cancelar_servicio.handle(CancelarServicioCommand(orden_id, "Ventas", "Prueba", rol_que_autoriza="Ventas"))
    assert not r.exito and "autoridad" in r.mensaje_de_negocio
    assert leer_orden(app, orden_id).estado_actual() is EstadoServicio.CONFIRMADO


def test_s04_la_autoridad_es_configurable(fabrica_de_app, solicitud):
    app = fabrica_de_app(roles_que_cancelan=frozenset({"Operaciones", "Ventas"}))
    orden_id = _orden(app, solicitud)
    assert app.cancelar_servicio.handle(CancelarServicioCommand(orden_id, "Ventas", "Duplicado", "Ventas")).exito


def test_s04_exige_motivo_y_no_cancela_un_servicio_ya_cancelado(app, solicitud):
    orden_id = _orden(app, solicitud)
    assert not app.cancelar_servicio.handle(CancelarServicioCommand(orden_id, "Cliente", "  ")).exito
    assert app.cancelar_servicio.handle(CancelarServicioCommand(orden_id, "Cliente", "Motivo")).exito
    assert not app.cancelar_servicio.handle(CancelarServicioCommand(orden_id, "Cliente", "Otra vez")).exito
    assert not app.asignar_recursos.handle(AsignarRecursosCommand(orden_id, "U-GRANDE", "OP-1")).exito


# S-05 cumplimiento de entregas
def _entregar(app, orden_id):
    assert app.asignar_recursos.handle(AsignarRecursosCommand(orden_id, "U-GRANDE", "OP-1")).exito
    def avanzar(o):
        o.registrar_recepcion(evidencia(EventoAsociado.RECEPCION))
        o.iniciar_traslado()
        o.registrar_llegada_a_destino()
    cambiar_orden(app, orden_id, avanzar)
    return app.registrar_entrega.handle(RegistrarEntregaCommand(orden_id, Destinatario("INE"), evidencia()))


def test_s05_cumplimiento_es_entregas_a_tiempo_sobre_entregas_realizadas(app, solicitud):
    en_plazo = replace(solicitud, fecha_requerida=date(2100, 1, 1))
    tarde = replace(solicitud, fecha_requerida=date(2000, 1, 1))
    ids = []
    for nombre, sol in (("A", en_plazo), ("B", tarde)):
        preparar_mundo_sin_duplicar(app, nombre, sol)
        app.responder_cotizacion.handle(ResponderCotizacionCommand(nombre, R.ACEPTA))
        ids.append(app.generar_orden.handle(GenerarOrdenDeServicioCommand(nombre, "ruta", HORARIO)).datos["orden_id"])
    for oid in ids:
        assert _entregar(app, oid).exito
        # la unidad vuelve a quedar libre para la siguiente orden (el operador sigue disponible)
    ind = app.consultar_indicadores.handle(ConsultarIndicadoresQuery(date(2000, 1, 1), date(2200, 1, 1)))
    assert ind.entregas_realizadas == 2 and ind.entregas_a_tiempo == 1
    assert ind.cumplimiento_de_entregas == 0.5


def preparar_mundo_sin_duplicar(app, cotizacion_id, solicitud):
    """El catálogo se registra una vez; después solo se agregan cotizaciones."""
    from helpers import sembrar
    from domain.cliente import Cliente
    if cotizacion_id == "A":
        preparar_mundo(app, solicitud, cotizaciones=("A",))
        return
    c = Cotizacion(cotizacion_id, "CLI-1", solicitud)
    c.elaborar(Decimal("9000.00"))
    c.extraer_eventos()
    sembrar(app, cotizaciones=[c])


def test_s05_sin_entregas_el_cumplimiento_no_esta_definido(app):
    ind = app.consultar_indicadores.handle(ConsultarIndicadoresQuery(date(2000, 1, 1), date(2200, 1, 1)))
    assert ind.cumplimiento_de_entregas is None
