"""Lectura del paquete de datos (CSV UTF-8 con BOM) y cálculo de totales con Decimal."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

RUTA = Path(__file__).resolve().parent.parent / "data" / "paquete"


def _leer(nombre: str) -> list[dict[str, str]]:
    with open(RUTA / nombre, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


@dataclass(frozen=True)
class Actor:
    id: str
    nombre: str
    preferente: bool
    activo: bool
    ciudad: str


@dataclass(frozen=True)
class Recurso:
    id: str
    descripcion: str
    precio_mxn: Decimal
    capacidad_o_stock: int
    habilitado: bool


@dataclass(frozen=True)
class Linea:
    recurso: Recurso
    cantidad: int

    @property
    def subtotal(self) -> Decimal:
        return self.recurso.precio_mxn * self.cantidad


@dataclass(frozen=True)
class Operacion:
    id: str
    actor: Actor
    estado_inicial: str
    fecha_solicitud: str
    promocion_activa: bool
    autorizado: bool
    referencia: str
    lineas: tuple[Linea, ...]

    @property
    def total(self) -> Decimal:
        return sum((l.subtotal for l in self.lineas), Decimal("0"))


@dataclass(frozen=True)
class Paquete:
    actores: dict[str, Actor]
    recursos: dict[str, Recurso]
    operaciones: dict[str, Operacion]
    casos_prueba: list[dict[str, str]]
    transiciones: list[dict[str, str]]


def cargar_paquete() -> Paquete:
    actores = {r["actor_id"]: Actor(r["actor_id"], r["nombre"], r["es_preferente"] == "1", r["activo"] == "1", r["ciudad"])
               for r in _leer("actores.csv")}
    recursos = {r["recurso_id"]: Recurso(r["recurso_id"], r["descripcion"], Decimal(r["precio_mxn"]),
                                         int(r["capacidad_o_stock"]), r["habilitado"] == "1")
                for r in _leer("catalogo.csv")}
    lineas: dict[str, list[Linea]] = {}
    for r in _leer("detalle_operaciones.csv"):
        lineas.setdefault(r["operacion_id"], []).append(Linea(recursos[r["recurso_id"]], int(r["cantidad"])))
    operaciones = {
        r["operacion_id"]: Operacion(r["operacion_id"], actores[r["actor_id"]], r["estado_inicial"], r["fecha_solicitud"],
                                     r["promocion_activa"] == "1", r["autorizado"] == "1", r["referencia"],
                                     tuple(lineas.get(r["operacion_id"], ())))
        for r in _leer("operaciones.csv")
    }
    return Paquete(actores, recursos, operaciones, _leer("casos_prueba.csv"), _leer("transiciones_prueba.csv"))
