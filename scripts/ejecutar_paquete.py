"""Ejecuta el paquete de datos del profesor y escribe la evidencia en docs/evidencias/.

Uso:  python scripts/ejecutar_paquete.py            (SQLite en memoria)
      DATABASE_URL=postgresql://... python scripts/ejecutar_paquete.py
"""
from __future__ import annotations

import csv
import os
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ / "src"), str(RAIZ / "tests")]

from dataset.cargador import cargar_paquete  # noqa: E402
from dataset.escenarios import ejecutar_casos, ejecutar_transicion, preparar_recursos  # noqa: E402
from infrastructure.composicion import construir_aplicacion_sql  # noqa: E402
from infrastructure.configuracion import Configuracion  # noqa: E402


def _escribir(ruta: Path, filas: list[dict[str, str]]) -> None:
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)


def main() -> int:
    paquete = cargar_paquete()
    destino = RAIZ / "docs" / "evidencias"
    destino.mkdir(parents=True, exist_ok=True)
    casos = ejecutar_casos(paquete)
    app = construir_aplicacion_sql(Configuracion.desde_entorno())
    preparar_recursos(app)
    transiciones = [ejecutar_transicion(app, paquete, f) for f in paquete.transiciones]
    _escribir(destino / "casos_prueba_resultados.csv", casos)
    _escribir(destino / "transiciones_resultados.csv", transiciones)
    for nombre, filas in (("casos_prueba", casos), ("transiciones", transiciones)):
        print(f"{nombre}: {dict(Counter(f['resultado_alumno'] for f in filas))}")
    return 0 if all(f["resultado_alumno"] == "PASA" for f in casos + transiciones) else 1


if __name__ == "__main__":
    raise SystemExit(main())
