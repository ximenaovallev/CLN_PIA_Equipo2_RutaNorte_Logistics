"""Reglas de dependencia entre capas (api → application → domain ← infrastructure)."""
import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"


def _importaciones(capa: str) -> set[str]:
    modulos = set()
    for archivo in (SRC / capa).rglob("*.py"):
        for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
            if isinstance(nodo, ast.Import):
                modulos |= {a.name.split(".")[0] for a in nodo.names}
            elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and nodo.module:
                modulos.add(nodo.module.split(".")[0])
    return modulos


def test_el_dominio_no_depende_de_nada_externo_ni_de_otras_capas():
    assert not _importaciones("domain") & {"sqlalchemy", "fastapi", "pydantic", "psycopg", "application", "infrastructure", "api"}


def test_la_aplicacion_solo_depende_del_dominio():
    assert not _importaciones("application") & {"sqlalchemy", "fastapi", "pydantic", "psycopg", "infrastructure", "api"}


def test_la_infraestructura_no_depende_de_la_api():
    assert "api" not in _importaciones("infrastructure")
