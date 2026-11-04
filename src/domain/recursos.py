"""Entities: Unidad y Operador (identidad propia, ciclo de vida independiente de la orden)."""
from __future__ import annotations

from .comunes import DatosInvalidos
from .valores import Capacidad


def _id_valido(id: str, que: str) -> None:
    if not id or not id.strip():
        raise DatosInvalidos(f"{que} requiere un identificador.")


class Unidad:
    def __init__(self, id: str, tipo: str, capacidad: Capacidad):
        _id_valido(id, "La unidad")
        self.id = id
        self.tipo = tipo
        self.capacidad = capacidad


class Operador:
    def __init__(self, id: str, nombre: str, disponible: bool = True):
        _id_valido(id, "El operador")
        self.id = id
        self.nombre = nombre
        self._disponible = disponible

    def esta_disponible(self) -> bool:
        return self._disponible

    def marcar_disponibilidad(self, disponible: bool) -> None:
        self._disponible = disponible
