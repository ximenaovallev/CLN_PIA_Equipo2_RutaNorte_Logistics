"""Entity: Cliente (quien solicita el servicio; identidad propia)."""
from __future__ import annotations

from .comunes import DatosInvalidos


class Cliente:
    def __init__(self, id: str, nombre: str, ciudad: str = ""):
        if not id or not id.strip():
            raise DatosInvalidos("El cliente requiere un identificador.")
        if not nombre or not nombre.strip():
            raise DatosInvalidos("El cliente requiere un nombre.")
        self.id = id
        self.nombre = nombre
        self.ciudad = ciudad
