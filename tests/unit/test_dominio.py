"""Invariantes del dominio y comportamiento de la Unit of Work."""
import pytest

from domain.comunes import CotizacionNoModificable, TransicionDeEstadoInvalida
from domain.cotizacion import Cotizacion
from domain.orden_de_servicio import EstadoServicio, OrdenDeServicio, TipoDeIncidencia
from domain.valores import Asignacion, Horario
from infrastructure.en_memoria import AlmacenEnMemoria, EnMemoriaUnitOfWork
from datetime import datetime, timezone
from decimal import Decimal


def test_cotizacion_solo_se_modifica_mientras_esta_en_proceso(solicitud):
    c = Cotizacion("C", "CLI", solicitud)
    c.modificar(solicitud)
    c.elaborar(Decimal('100'))
    c.aceptar()
    with pytest.raises(CotizacionNoModificable):
        c.modificar(solicitud)


def _orden(solicitud):
    c = Cotizacion("C", "CLI", solicitud)
    c.elaborar(Decimal('100'))
    c.aceptar()
    return OrdenDeServicio.generar_desde("O-1", c, "ruta", Horario(datetime.now(timezone.utc)))


def test_la_orden_exige_el_orden_de_los_estados(solicitud):
    o = _orden(solicitud)
    with pytest.raises(TransicionDeEstadoInvalida):
        o.registrar_recepcion(None)  # aún no tiene unidad asignada
    o.asignar_recursos(Asignacion("U", "OP"))
    assert o.estado_actual() is EstadoServicio.UNIDAD_ASIGNADA


def test_toda_incidencia_queda_en_el_historial_sin_cambiar_estado(solicitud):
    o = _orden(solicitud)
    antes = o.estado_actual()
    o.registrar_incidencia(TipoDeIncidencia.UNIDAD_AVERIADA, "Falla mecánica")
    assert o.estado_actual() is antes
    assert "UNIDAD_AVERIADA" in o.historial[-1].descripcion


def test_unit_of_work_revierte_si_no_se_confirma(solicitud):
    almacen = AlmacenEnMemoria()
    uow = EnMemoriaUnitOfWork(almacen)
    with uow:
        uow.cotizaciones.guardar(Cotizacion("C", "CLI", solicitud))
    assert almacen.cotizaciones == {}  # sin confirmar() no queda nada

    with uow:
        uow.cotizaciones.guardar(Cotizacion("C", "CLI", solicitud))
        uow.confirmar()
    assert "C" in almacen.cotizaciones


def test_la_recepcion_exige_evidencia_de_recepcion_y_deja_la_orden_recolectada(solicitud):
    from domain.comunes import DatosInvalidos
    from domain.valores import Evidencia, EventoAsociado, TipoDeEvidencia
    o = _orden(solicitud)
    o.asignar_recursos(Asignacion("U", "OP"))
    with pytest.raises(DatosInvalidos):
        o.registrar_recepcion(None)
    ev_entrega = Evidencia(TipoDeEvidencia.FOTOGRAFIA, "f.jpg", datetime.now(timezone.utc), EventoAsociado.ENTREGA)
    with pytest.raises(DatosInvalidos):  # evidencia de otro evento
        o.registrar_recepcion(ev_entrega)
    o.registrar_recepcion(Evidencia(TipoDeEvidencia.FOTOGRAFIA, "r.jpg", datetime.now(timezone.utc), EventoAsociado.RECEPCION))
    assert o.estado_actual() is EstadoServicio.RECOLECTADO and len(o.evidencias_recepcion) == 1


def test_mercancia_diferente_a_la_declarada_se_registra_como_incidencia_con_evidencia(solicitud):
    from domain.valores import Evidencia, EventoAsociado, TipoDeEvidencia
    o = _orden(solicitud)
    ev = Evidencia(TipoDeEvidencia.FOTOGRAFIA, "dif.jpg", datetime.now(timezone.utc), EventoAsociado.INCIDENCIA)
    o.registrar_incidencia(TipoDeIncidencia.MERCANCIA_DIFERENTE, "Llegaron 3 cajas menos", ev)
    assert o.incidencias[0].tipo is TipoDeIncidencia.MERCANCIA_DIFERENTE and o.incidencias[0].evidencias == [ev]


def test_no_se_registran_incidencias_en_un_servicio_terminado(solicitud):
    o = _orden(solicitud)
    o.cancelar("Cliente", "Ya no lo necesita")
    with pytest.raises(TransicionDeEstadoInvalida):
        o.registrar_incidencia(TipoDeIncidencia.RETRASO, "Tarde")
