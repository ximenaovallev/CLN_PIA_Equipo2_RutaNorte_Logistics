"""Commands y Queries (CQRS básico): cada uno expresa una intención completa."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from domain.orden_de_servicio import TipoDeIncidencia
from domain.valores import Destinatario, Evidencia, SolicitudDeCotizacion


class RespuestaDelCliente(Enum):
    ACEPTA = "ACEPTA"
    RECHAZA = "RECHAZA"


# ------------------------------- Commands: catálogos de apoyo -------------------------------
@dataclass(frozen=True)
class RegistrarClienteCommand:
    id: str
    nombre: str
    ciudad: str = ""


@dataclass(frozen=True)
class RegistrarUnidadCommand:
    id: str
    tipo: str
    peso_kg: float
    volumen_m3: float


@dataclass(frozen=True)
class RegistrarOperadorCommand:
    id: str
    nombre: str
    disponible: bool = True


@dataclass(frozen=True)
class CambiarDisponibilidadDeOperadorCommand:
    operador_id: str
    disponible: bool


# ------------------------------- Commands: cotización (US-01, 02, 03, 17) -------------------------------
@dataclass(frozen=True)
class SolicitarCotizacionCommand:
    cliente_id: str
    solicitud: SolicitudDeCotizacion


@dataclass(frozen=True)
class ElaborarCotizacionCommand:
    cotizacion_id: str
    importe_mxn: Decimal


@dataclass(frozen=True)
class ModificarCotizacionCommand:
    cotizacion_id: str
    solicitud: SolicitudDeCotizacion


@dataclass(frozen=True)
class ResponderCotizacionCommand:
    cotizacion_id: str
    respuesta: RespuestaDelCliente


# ------------------------------- Commands: orden de servicio -------------------------------
@dataclass(frozen=True)
class GenerarOrdenDeServicioCommand:
    cotizacion_id: str
    ruta: str
    horario_recoleccion: datetime


@dataclass(frozen=True)
class AsignarRecursosCommand:
    orden_id: str
    unidad_id: str
    operador_id: str


@dataclass(frozen=True)
class RegistrarRecepcionCommand:
    orden_id: str
    evidencia: Evidencia


@dataclass(frozen=True)
class IniciarTrasladoCommand:
    orden_id: str


@dataclass(frozen=True)
class RegistrarLlegadaCommand:
    orden_id: str


@dataclass(frozen=True)
class RegistrarEntregaCommand:
    """Si `incidencia` es None la entrega fue posible, completa y sin daño."""
    orden_id: str
    destinatario: Destinatario | None
    evidencia: Evidencia
    incidencia: TipoDeIncidencia | None = None
    descripcion_incidencia: str = ""


@dataclass(frozen=True)
class RegistrarIncidenciaCommand:
    orden_id: str
    tipo: TipoDeIncidencia
    descripcion: str
    evidencia: Evidencia | None = None


@dataclass(frozen=True)
class AutorizarCargaDeAltoValorCommand:
    orden_id: str
    autorizado_por: str


@dataclass(frozen=True)
class CancelarServicioCommand:
    orden_id: str
    solicitado_por: str
    motivo: str
    rol_que_autoriza: str = "Operaciones"


@dataclass(frozen=True)
class SolicitarCambioOperativoCommand:
    orden_id: str
    solicitado_por: str
    descripcion: str


@dataclass(frozen=True)
class RevisarCambioOperativoCommand:
    orden_id: str
    revisado_por: str
    aprobado: bool
    comentario: str = ""


# ------------------------------- Queries -------------------------------
@dataclass(frozen=True)
class ConsultarEstadoDelServicioQuery:
    orden_id: str


@dataclass(frozen=True)
class ConsultarIndicadoresQuery:
    desde: date
    hasta: date


@dataclass(frozen=True)
class ConsultarCotizacionQuery:
    cotizacion_id: str


@dataclass(frozen=True)
class ListarOrdenesQuery:
    estado: str | None = None
    limite: int = 50


@dataclass(frozen=True)
class ConsultarClienteQuery:
    cliente_id: str


@dataclass(frozen=True)
class ConsultarUnidadQuery:
    unidad_id: str


@dataclass(frozen=True)
class ConsultarOperadorQuery:
    operador_id: str
