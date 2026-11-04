"""Reglas ILUSTRATIVAS del paquete (LEEME) expresadas con el mismo patrón Specification del dominio.

No sustituyen los requerimientos del BRD: sirven para ejecutar los 120 casos del paquete y comparar contra un
oráculo independiente (ver docs/arquitectura/paquete_de_datos.md).
"""
from __future__ import annotations

from decimal import Decimal

from domain.especificaciones import Especificacion

from .cargador import Operacion

UMBRAL_BENEFICIO_MXN = Decimal("1500")


class ActorActivo(Especificacion[Operacion]):
    descripcion = "el cliente está activo"  # type: ignore[assignment]

    def es_satisfecha_por(self, op: Operacion) -> bool:
        return op.actor.activo


class DetalleNoVacio(Especificacion[Operacion]):
    descripcion = "la operación tiene al menos una línea"  # type: ignore[assignment]

    def es_satisfecha_por(self, op: Operacion) -> bool:
        return len(op.lineas) > 0


class Autorizada(Especificacion[Operacion]):
    descripcion = "la operación está autorizada"  # type: ignore[assignment]

    def es_satisfecha_por(self, op: Operacion) -> bool:
        return op.autorizado


class ActorPreferente(Especificacion[Operacion]):
    descripcion = "el cliente es preferente"  # type: ignore[assignment]

    def es_satisfecha_por(self, op: Operacion) -> bool:
        return op.actor.preferente


class TotalMinimo(Especificacion[Operacion]):
    def __init__(self, minimo: Decimal):
        self._minimo = minimo

    @property
    def descripcion(self) -> str:  # type: ignore[override]
        return f"el total es de al menos {self._minimo} MXN"

    def es_satisfecha_por(self, op: Operacion) -> bool:
        return op.total >= self._minimo


class PromocionActiva(Especificacion[Operacion]):
    descripcion = "hay una promoción activa"  # type: ignore[assignment]

    def es_satisfecha_por(self, op: Operacion) -> bool:
        return op.promocion_activa


class ServiciosHabilitados(Especificacion[Operacion]):
    descripcion = "todos los servicios de las líneas están habilitados"  # type: ignore[assignment]

    def es_satisfecha_por(self, op: Operacion) -> bool:
        return all(l.recurso.habilitado for l in op.lineas)


class CantidadesDentroDeLaCapacidad(Especificacion[Operacion]):
    descripcion = "cada cantidad está dentro de la capacidad del servicio"  # type: ignore[assignment]

    def es_satisfecha_por(self, op: Operacion) -> bool:
        return all(0 < l.cantidad <= l.recurso.capacidad_o_stock for l in op.lineas)


def puede_procesarse() -> Especificacion[Operacion]:
    """actor activo AND detalle no vacío AND autorización (regla 1 del LEEME)."""
    return ActorActivo() & DetalleNoVacio() & Autorizada()


def beneficio_referencia() -> Especificacion[Operacion]:
    """preferente AND total >= 1500 AND NOT promoción (regla 2 del LEEME)."""
    return ActorPreferente() & TotalMinimo(UMBRAL_BENEFICIO_MXN) & ~PromocionActiva()


# ---- Oráculos independientes: expresiones planas, sin usar Specification, calculadas desde los CSV ----
def oraculo_puede_procesarse(op: Operacion) -> bool:
    return bool(op.actor.activo and len(op.lineas) >= 1 and op.autorizado)


def oraculo_beneficio(op: Operacion) -> bool:
    total = sum(l.recurso.precio_mxn * l.cantidad for l in op.lineas)
    return bool(op.actor.preferente and total >= Decimal("1500") and not op.promocion_activa)
