"""Fixtures compartidas. Las pruebas de comportamiento corren contra TODOS los backends disponibles:
memoria, SQLite y, si se define TEST_DATABASE_URL (CI / docker compose), PostgreSQL."""
from __future__ import annotations

import os
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from application.comandos import (
    GenerarOrdenDeServicioCommand, ResponderCotizacionCommand, RespuestaDelCliente as R, AsignarRecursosCommand,
)
from domain.cliente import Cliente
from domain.cotizacion import Cotizacion
from domain.recursos import Operador, Unidad
from domain.valores import (
    Capacidad, Dimensiones, EventoAsociado, Mercancia, Peso, SolicitudDeCotizacion, Ubicacion, Volumen,
)
from infrastructure.composicion import construir_aplicacion_en_memoria, construir_aplicacion_sql
from infrastructure.configuracion import Configuracion

from helpers import HORARIO, cambiar_orden, evidencia as _evidencia, sembrar

BACKENDS = ["memoria", "sqlite"] + (["postgres"] if os.getenv("TEST_DATABASE_URL") else [])


def configuracion(**cambios) -> Configuracion:
    base = Configuracion(database_url="sqlite:///:memory:", entorno="pruebas", nivel_de_log="WARNING",
                         peso_maximo_kg=None, volumen_maximo_m3=None, dias_de_conservacion=None,
                         roles_que_cancelan=frozenset({"Operaciones"}))
    return Configuracion(**{**base.__dict__, **cambios})


def crear_app(backend: str, **cambios):
    if backend == "memoria":
        return construir_aplicacion_en_memoria(configuracion(**cambios))
    if backend == "sqlite":
        return construir_aplicacion_sql(configuracion(**cambios))
    app = construir_aplicacion_sql(configuracion(database_url=os.environ["TEST_DATABASE_URL"], **cambios),
                                   crear_esquema=True)
    _vaciar(app)
    return app


def _vaciar(app) -> None:
    from sqlalchemy import text
    with app.motor.begin() as c:
        c.execute(text("TRUNCATE eventos_de_dominio, orden_evidencias, orden_incidencias, orden_historial, "
                       "ordenes, cotizaciones, operadores, unidades, clientes RESTART IDENTITY CASCADE"))


@pytest.fixture(params=BACKENDS)
def backend(request) -> str:
    return request.param


@pytest.fixture
def fabrica_de_app(backend):
    """Permite construir una app con supuestos distintos (S-01, S-03, S-04) sobre el backend en curso."""
    return lambda **cambios: crear_app(backend, **cambios)


@pytest.fixture
def app(fabrica_de_app):
    return fabrica_de_app()


@pytest.fixture
def solicitud():
    return SolicitudDeCotizacion(
        origen=Ubicacion("Monterrey"), destino=Ubicacion("Querétaro"),
        mercancia=Mercancia("Refacciones", Peso(800), Dimensiones(2, 1.5, 1.5)),
        fecha_requerida=date(2026, 11, 1),
    )


@pytest.fixture
def evidencia():
    return _evidencia


def preparar_mundo(app, solicitud, cotizaciones=("COT-1",)):
    """Cliente, cotizaciones ya elaboradas, una unidad adecuada, una pequeña y dos operadores."""
    cots = []
    for id in cotizaciones:
        c = Cotizacion(id, "CLI-1", solicitud)
        c.elaborar(Decimal("15000.00"))
        c.extraer_eventos()
        cots.append(c)
    sembrar(
        app,
        clientes=[Cliente("CLI-1", "Refacciones del Norte", "Monterrey")],
        cotizaciones=cots,
        unidades=[Unidad("U-GRANDE", "Caja seca", Capacidad(Peso(5000), Volumen(30))),
                  Unidad("U-CHICA", "Pick-up", Capacidad(Peso(500), Volumen(4)))],
        operadores=[Operador("OP-1", "Operador uno", True), Operador("OP-2", "Operador dos", False)],
    )
    return app


@pytest.fixture
def mundo(app, solicitud):
    return preparar_mundo(app, solicitud)


@pytest.fixture
def orden_confirmada(mundo):
    mundo.responder_cotizacion.handle(ResponderCotizacionCommand("COT-1", R.ACEPTA))
    r = mundo.generar_orden.handle(GenerarOrdenDeServicioCommand("COT-1", "MTY-QRO", HORARIO))
    return mundo, r.datos["orden_id"]


@pytest.fixture
def orden_en_destino(orden_confirmada):
    app, orden_id = orden_confirmada
    assert app.asignar_recursos.handle(AsignarRecursosCommand(orden_id, "U-GRANDE", "OP-1")).exito

    def avanzar(o):
        o.registrar_recepcion(_evidencia(EventoAsociado.RECEPCION))
        o.iniciar_traslado()
        o.registrar_llegada_a_destino()
    cambiar_orden(app, orden_id, avanzar)
    return app, orden_id
