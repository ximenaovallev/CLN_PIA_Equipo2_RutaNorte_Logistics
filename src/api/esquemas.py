"""Contratos HTTP (pydantic). Son el borde de la API: se traducen a Commands/Queries y nunca llegan al dominio."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from domain.orden_de_servicio import TipoDeIncidencia
from domain.valores import (
    Destinatario, Dimensiones, Evidencia, EventoAsociado, Mercancia, Peso, SolicitudDeCotizacion, TipoDeEvidencia,
    Ubicacion,
)


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ----------------------------- entrada -----------------------------
class ClienteIn(_Base):
    id: str = Field(examples=["CLI-001"])
    nombre: str
    ciudad: str = ""


class UnidadIn(_Base):
    id: str = Field(examples=["UNI-001"])
    tipo: str = Field(examples=["Camión torton"])
    peso_kg: float = Field(description="Capacidad de peso en kg", examples=[8000])
    volumen_m3: float = Field(description="Capacidad de volumen en m³", examples=[40])


class OperadorIn(_Base):
    id: str = Field(examples=["OPE-001"])
    nombre: str
    disponible: bool = True


class DisponibilidadIn(_Base):
    disponible: bool


class UbicacionIn(_Base):
    ciudad: str
    direccion: str = ""


class MercanciaIn(_Base):
    descripcion: str
    peso_kg: float
    largo_m: float
    ancho_m: float
    alto_m: float
    caracteristicas_especiales: str = ""
    alto_valor: bool = False


class SolicitudIn(_Base):
    origen: UbicacionIn
    destino: UbicacionIn
    mercancia: MercanciaIn
    fecha_requerida: date

    def a_dominio(self) -> SolicitudDeCotizacion:
        m = self.mercancia
        return SolicitudDeCotizacion(
            origen=Ubicacion(self.origen.ciudad, self.origen.direccion),
            destino=Ubicacion(self.destino.ciudad, self.destino.direccion),
            mercancia=Mercancia(m.descripcion, Peso(m.peso_kg), Dimensiones(m.largo_m, m.ancho_m, m.alto_m),
                                m.caracteristicas_especiales, m.alto_valor),
            fecha_requerida=self.fecha_requerida,
        )


class CotizacionIn(_Base):
    cliente_id: str
    solicitud: SolicitudIn


class ImporteIn(_Base):
    importe_mxn: Decimal = Field(examples=["12500.00"])


class RespuestaIn(_Base):
    respuesta: Literal["ACEPTA", "RECHAZA"]


class OrdenIn(_Base):
    cotizacion_id: str
    ruta: str = Field(examples=["MTY-CDMX"])
    horario_recoleccion: datetime


class AsignacionIn(_Base):
    unidad_id: str
    operador_id: str


class EvidenciaIn(_Base):
    tipo: TipoDeEvidencia = TipoDeEvidencia.FOTOGRAFIA
    referencia: str = Field(description="URL o folio del archivo de evidencia")
    fecha: datetime | None = None

    def a_dominio(self, evento: EventoAsociado) -> Evidencia:
        return Evidencia(self.tipo, self.referencia, self.fecha or datetime.now(timezone.utc), evento)


class RecepcionIn(_Base):
    evidencia: EvidenciaIn


class EntregaIn(_Base):
    """Sin `incidencia`: entrega completa. Con `incidencia`: la entrega no se concreta y se registra el motivo."""
    destinatario: str | None = Field(default=None, description="Identificación de quien recibe")
    evidencia: EvidenciaIn
    incidencia: TipoDeIncidencia | None = None
    descripcion_incidencia: str = ""

    def destinatario_de_dominio(self) -> Destinatario | None:
        return Destinatario(self.destinatario) if self.destinatario is not None else None


class IncidenciaIn(_Base):
    tipo: TipoDeIncidencia
    descripcion: str
    evidencia: EvidenciaIn | None = None


class AutorizacionAltoValorIn(_Base):
    autorizado_por: str


class CancelacionIn(_Base):
    solicitado_por: str
    motivo: str
    rol_que_autoriza: str = "Operaciones"


class CambioOperativoIn(_Base):
    solicitado_por: str
    descripcion: str


class RevisionDeCambioIn(_Base):
    revisado_por: str
    aprobado: bool
    comentario: str = ""


# ----------------------------- salida -----------------------------
class ErrorOut(BaseModel):
    codigo: str = Field(description="Nombre del error de negocio o 'SolicitudInvalida'")
    mensaje: str


class OperacionOut(BaseModel):
    mensaje: str
    datos: dict = Field(default_factory=dict)


class EstadoDeEntidad(str, Enum):
    ok = "ok"
