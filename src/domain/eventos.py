"""Domain Events: hechos del negocio que ya ocurrieron."""
from __future__ import annotations

from dataclasses import dataclass

from decimal import Decimal

from .comunes import EventoDeDominio
from .maquina_de_estados import Disparador, EstadoServicio
from .valores import Asignacion, Destinatario


@dataclass(frozen=True, kw_only=True)
class CotizacionAceptada(EventoDeDominio):
    cotizacion_id: str


@dataclass(frozen=True, kw_only=True)
class OrdenDeServicioGenerada(EventoDeDominio):
    orden_id: str
    cotizacion_id: str


@dataclass(frozen=True, kw_only=True)
class RecursosAsignados(EventoDeDominio):
    orden_id: str
    asignacion: Asignacion
    es_reasignacion: bool


@dataclass(frozen=True, kw_only=True)
class CargaDeAltoValorAutorizada(EventoDeDominio):
    orden_id: str
    autorizado_por: str


@dataclass(frozen=True, kw_only=True)
class ServicioCancelado(EventoDeDominio):
    orden_id: str
    solicitado_por: str
    motivo: str


@dataclass(frozen=True, kw_only=True)
class EntregaRegistrada(EventoDeDominio):
    orden_id: str
    destinatario: Destinatario


@dataclass(frozen=True, kw_only=True)
class IncidenciaRegistrada(EventoDeDominio):
    orden_id: str
    tipo: "TipoDeIncidencia"  # noqa: F821 (definido en orden_de_servicio)


@dataclass(frozen=True, kw_only=True)
class CotizacionElaborada(EventoDeDominio):
    cotizacion_id: str
    importe_mxn: Decimal


@dataclass(frozen=True, kw_only=True)
class EstadoDelServicioCambiado(EventoDeDominio):
    orden_id: str
    desde: EstadoServicio
    hasta: EstadoServicio
    disparador: Disparador


@dataclass(frozen=True, kw_only=True)
class CambioOperativoSolicitado(EventoDeDominio):
    orden_id: str
    solicitado_por: str
    descripcion: str


@dataclass(frozen=True, kw_only=True)
class CambioOperativoRevisado(EventoDeDominio):
    orden_id: str
    revisado_por: str
    aprobado: bool
