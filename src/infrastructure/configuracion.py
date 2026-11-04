"""Configuración 12-Factor: todo valor de entorno se lee aquí y solo aquí."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _entero(nombre: str) -> int | None:
    v = os.getenv(nombre, "").strip()
    return int(v) if v else None


def _decimal_float(nombre: str) -> float | None:
    v = os.getenv(nombre, "").strip()
    return float(v) if v else None


@dataclass(frozen=True)
class Configuracion:
    database_url: str
    entorno: str
    nivel_de_log: str
    # Supuestos pendientes de validar (S-01, S-03, S-04): configurables sin tocar código.
    peso_maximo_kg: float | None
    volumen_maximo_m3: float | None
    dias_de_conservacion: int | None
    roles_que_cancelan: frozenset[str]

    @classmethod
    def desde_entorno(cls) -> "Configuracion":
        roles = os.getenv("ROLES_QUE_CANCELAN", "Operaciones")
        return cls(
            database_url=os.getenv("DATABASE_URL", "sqlite:///:memory:"),
            entorno=os.getenv("APP_ENV", "desarrollo"),
            nivel_de_log=os.getenv("LOG_LEVEL", "INFO").upper(),
            peso_maximo_kg=_decimal_float("LIMITE_PESO_KG"),
            volumen_maximo_m3=_decimal_float("LIMITE_VOLUMEN_M3"),
            dias_de_conservacion=_entero("DIAS_CONSERVACION_EVIDENCIAS"),
            roles_que_cancelan=frozenset(r.strip() for r in roles.split(",") if r.strip()),
        )
