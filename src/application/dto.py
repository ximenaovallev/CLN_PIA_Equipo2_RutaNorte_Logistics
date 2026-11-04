"""Resultados de la aplicación y View Models de lectura (no se reutilizan para escribir)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class Resultado:
    exito: bool
    mensaje_de_negocio: str = ""
    datos: dict[str, Any] = field(default_factory=dict)
    codigo_de_error: str | None = None  # nombre del error de dominio; la API lo traduce a HTTP

    @classmethod
    def ok(cls, mensaje: str = "", **datos: Any) -> "Resultado":
        return cls(True, mensaje, datos)

    @classmethod
    def fallo(cls, mensaje: str, codigo: str | None = None) -> "Resultado":
        return cls(False, mensaje, codigo_de_error=codigo)


@dataclass(frozen=True)
class EstadoDelServicioDTO:
    orden_id: str
    estado_actual: str
    eventos: list[str]
    retrasos: list[str]
    incidencias: list[str]
    acciones_permitidas: list[str] = field(default_factory=list)
    cambio_operativo_pendiente: str | None = None
    unidad_id: str | None = None
    operador_id: str | None = None


@dataclass(frozen=True)
class IndicadoresDTO:
    tiempos_reales_de_entrega_horas: list[float]
    retrasos: int
    incidencias: int
    entregas_realizadas: int
    ordenes_en_el_periodo: int
    entregas_a_tiempo: int
    # SUPUESTO S-05 (pendiente de validar): cumplimiento = entregas realizadas en o antes de la
    # fecha requerida por el cliente / entregas realizadas. None si aún no hay entregas.
    cumplimiento_de_entregas: float | None


@dataclass(frozen=True)
class CotizacionDTO:
    cotizacion_id: str
    cliente_id: str
    estado: str
    estado_del_servicio: str | None
    importe_mxn: Decimal | None
    origen: str
    destino: str
    mercancia: str
    peso_kg: float
    alto_valor: bool
    fecha_requerida: date


@dataclass(frozen=True)
class OrdenResumenDTO:
    orden_id: str
    cliente_id: str
    estado: str
    ruta: str
    alto_valor: bool
    fecha_requerida: date | None


@dataclass(frozen=True)
class ClienteDTO:
    id: str
    nombre: str
    ciudad: str


@dataclass(frozen=True)
class UnidadDTO:
    id: str
    tipo: str
    peso_kg: float
    volumen_m3: float


@dataclass(frozen=True)
class OperadorDTO:
    id: str
    nombre: str
    disponible: bool
