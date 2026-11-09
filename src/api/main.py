"""Aplicación FastAPI: Swagger UI en /docs, OpenAPI en /openapi.json."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from domain.comunes import ErrorDeDominio
from infrastructure.composicion import Aplicacion, construir_aplicacion
from infrastructure.configuracion import Configuracion

from . import lenguaje
from .errores import codigo_http
from .rutas import ETIQUETAS, T_SISTEMA, router

DESCRIPCION = """
## ¿Qué es esta página?
Aquí puede **probar el sistema de RutaNorte Logistics** sin saber de programación: pedir una cotización, crear una orden de
transporte, seguir el viaje paso a paso y registrar la entrega. Todo lo que haga aquí queda guardado de verdad.

## ¿Cómo se usa? (3 pasos)
1. Elija una sección de abajo y haga clic en la acción que necesita (por ejemplo, *Registrar un cliente*).
2. Pulse el botón **Try it out** (probar). El formulario ya viene con un ejemplo escrito; cámbielo por sus datos.
3. Pulse el botón azul **Execute** (ejecutar). Más abajo verá el resultado, con un mensaje que explica qué pasó y **qué hacer después**.

## El camino completo, en orden
| Paso | Qué se hace | Sección |
|---|---|---|
| 1 | Registrar al cliente, un camión y un operador | 1. Registros básicos |
| 2 | Pedir la cotización (**guarde el número de cotización**) | 2. Cotizaciones |
| 3 | Poner el precio y que el cliente acepte | 2. Cotizaciones |
| 4 | Crear la orden (**guarde el número de orden**) | 3. Órdenes de servicio |
| 5 | Asignar camión y operador | 3. Órdenes de servicio |
| 6 | Registrar recolección, salida, llegada y entrega | 3. Órdenes de servicio |
| 7 | Consultar cómo va el servicio, en cualquier momento | 3. Órdenes de servicio |

## ¿Qué significan los números de respuesta?
| Número | Significado |
|---|---|
| **200** o **201** | Todo salió bien |
| **400** | Faltan datos o están mal escritos; el mensaje dice cuál corregir |
| **404** | No se encontró lo que buscó (revise el código que escribió) |
| **409** | Ese paso no se puede hacer ahora (ya existe o va fuera de orden) |
| **422** | El negocio no lo permite todavía (por ejemplo, falta autorizar una carga de alto valor) |

Si algo sale mal, **no se preocupe: no se pierde nada**. Lea el mensaje, que siempre explica qué pasó y qué hacer.
"""


def crear_app(aplicacion: Aplicacion | None = None, config: Configuracion | None = None) -> FastAPI:
    config = config or Configuracion.desde_entorno()
    logging.basicConfig(level=config.nivel_de_log, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    app = FastAPI(title="RutaNorte Logistics API", version="1.0.0", description=DESCRIPCION,
                  openapi_tags=ETIQUETAS)
    app.state.aplicacion = aplicacion or construir_aplicacion(config)
    app.include_router(router)

    @app.get("/health", tags=[T_SISTEMA], summary="Comprobar que el sistema funciona",
             description="Responde «ok» si el sistema está en marcha. No necesita datos.")
    def health() -> dict:
        return {"estado": "ok", "entorno": config.entorno}

    @app.get("/interfaz", include_in_schema=False, response_class=HTMLResponse)
    def interfaz() -> HTMLResponse:
        """Pantalla amigable para usar todo el sistema sin Swagger."""
        return HTMLResponse((Path(__file__).parent / "interfaz.html").read_text(encoding="utf-8"))

    @app.get("/", include_in_schema=False)
    def inicio() -> RedirectResponse:
        """Quien abre la dirección principal llega directo a la página de pruebas."""
        return RedirectResponse(url="/docs")

    @app.exception_handler(RequestValidationError)
    async def solicitud_invalida(_: Request, error: RequestValidationError) -> JSONResponse:
        mensaje, que_hacer = lenguaje.validacion(error.errors())
        return JSONResponse(status_code=400, content={"codigo": "SolicitudInvalida", "mensaje": mensaje, "que_hacer": que_hacer})

    @app.exception_handler(ErrorDeDominio)
    async def error_de_dominio(_: Request, error: ErrorDeDominio) -> JSONResponse:
        # Cubre los errores que el dominio lanza al construir Value Objects en el borde (p. ej. peso <= 0).
        nombre = type(error).__name__
        mensaje, que_hacer = lenguaje.error(nombre, str(error))
        return JSONResponse(status_code=codigo_http(nombre),
                            content={"codigo": nombre, "mensaje": mensaje, "que_hacer": que_hacer})

    @app.exception_handler(StarletteHTTPException)  # incluye los 404/405 de direcciones que no existen
    async def error_http(_: Request, error: StarletteHTTPException) -> JSONResponse:
        d = error.detail
        if isinstance(d, dict):
            cuerpo = d
        else:
            mensaje, que_hacer = lenguaje.http(error.status_code, str(d))
            cuerpo = {"codigo": "Error", "mensaje": mensaje, "que_hacer": que_hacer}
        return JSONResponse(status_code=error.status_code, content=cuerpo)

    return app


def app_de_produccion() -> FastAPI:
    """Fábrica para uvicorn: `uvicorn --factory api.main:app_de_produccion`."""
    return crear_app()
