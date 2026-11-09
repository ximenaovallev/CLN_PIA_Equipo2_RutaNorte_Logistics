"""La pantalla amigable debe existir y cubrir todas las operaciones de la API."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import crear_app
from conftest import BACKENDS, crear_app as crear_aplicacion


@pytest.fixture(params=BACKENDS)
def cliente(request):
    return TestClient(crear_app(crear_aplicacion(request.param)))


def test_interfaz_se_sirve_como_html(cliente):
    r = cliente.get("/interfaz")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")


def test_interfaz_cubre_todas_las_operaciones_del_openapi(cliente):
    html = cliente.get("/interfaz").text
    faltan = []
    for ruta, ops in cliente.get("/openapi.json").json()["paths"].items():
        for metodo in ops:
            if f'm:"{metodo.upper()}",p:"{ruta}"' not in html:
                faltan.append(f"{metodo.upper()} {ruta}")
    assert not faltan, faltan
