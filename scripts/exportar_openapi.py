"""Exporta el contrato OpenAPI a docs/api/openapi.json (o, con --verificar, comprueba que está al día)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from api.main import crear_app  # noqa: E402
from infrastructure.composicion import construir_aplicacion_en_memoria  # noqa: E402
from infrastructure.configuracion import Configuracion  # noqa: E402

DESTINO = RAIZ / "docs" / "api" / "openapi.json"


def generar() -> str:
    config = Configuracion.desde_entorno()
    app = crear_app(construir_aplicacion_en_memoria(config), config)
    return json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    actual = generar()
    if "--verificar" in sys.argv:
        if not DESTINO.exists() or DESTINO.read_text(encoding="utf-8") != actual:
            print("docs/api/openapi.json está desactualizado: ejecuta `python scripts/exportar_openapi.py`.")
            raise SystemExit(1)
        print("OpenAPI al día.")
    else:
        DESTINO.write_text(actual, encoding="utf-8")
        print(f"Escrito {DESTINO.relative_to(RAIZ)}")
