"""Genera desde el código los diagramas que NO se dibujan a mano: estados (máquina real) y entidad-relación (tablas reales)."""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from domain.maquina_de_estados import CICLO_DE_VIDA_DEL_SERVICIO as CICLO, EstadoServicio  # noqa: E402
from infrastructure.sql.tablas import metadata  # noqa: E402

DESTINO = RAIZ / "docs" / "architecture" / "diagramas"


def estados_puml() -> str:
    o = ["@startuml 02_estados_del_servicio", "title Ciclo de vida del servicio (generado desde CICLO_DE_VIDA_DEL_SERVICIO)",
         "skinparam shadowing false", "hide empty description", ""]
    o.append(f"[*] --> {CICLO.inicial.value}")
    for origen, disparador, destino in sorted(CICLO.transiciones(), key=lambda t: (list(EstadoServicio).index(t[0]), t[1].value)):
        o.append(f"{origen.value} --> {destino.value} : {disparador.value}")
    for e in EstadoServicio:
        if CICLO.es_terminal(e):
            o.append(f"{e.value} --> [*]")
    o.append("@enduml")
    return "\n".join(o) + "\n"


def er_puml() -> str:
    o = ["@startuml 03_modelo_relacional", "title Modelo relacional (generado desde infrastructure/sql/tablas.py)",
         "skinparam shadowing false", "hide circle", "skinparam linetype ortho", ""]
    for t in metadata.sorted_tables:
        o.append(f"entity {t.name} {{")
        for c in t.columns:
            marca = "*" if c.primary_key else " "
            o.append(f"  {marca} {c.name} : {str(c.type).split('(')[0]}")
        o.append("}")
    for t in metadata.sorted_tables:
        for c in t.columns:
            for fk in c.foreign_keys:
                o.append(f"{fk.column.table.name} ||--o{{ {t.name} : {c.name}")
    o.append("@enduml")
    return "\n".join(o) + "\n"


if __name__ == "__main__":
    (DESTINO / "02_estados_del_servicio.puml").write_text(estados_puml(), encoding="utf-8")
    (DESTINO / "03_modelo_relacional.puml").write_text(er_puml(), encoding="utf-8")
    print("Diagramas generados.")
