"""Aplicación FastAPI: Swagger UI en /docs, OpenAPI en /openapi.json."""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from domain.comunes import ErrorDeDominio
from infrastructure.composicion import Aplicacion, construir_aplicacion
from infrastructure.configuracion import Configuracion

from .errores import codigo_http
from .rutas import router

DESCRIPCION = """
API del sistema de **RutaNorte Logistics**: cotización, orden de servicio, asignación de recursos,
seguimiento, entrega con evidencia e indicadores.

**Códigos de respuesta**: `200` operación correcta · `201` recurso creado · `400` datos inválidos ·
`404` no existe · `409` conflicto con el estado actual · `422` regla de negocio no cumplida.
"""


def crear_app(aplicacion: Aplicacion | None = None, config: Configuracion | None = None) -> FastAPI:
    config = config or Configuracion.desde_entorno()
    logging.basicConfig(level=config.nivel_de_log, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    app = FastAPI(title="RutaNorte Logistics API", version="1.0.0", description=DESCRIPCION)
    app.state.aplicacion = aplicacion or construir_aplicacion(config)
    app.include_router(router)

    @app.get("/health", tags=["Operación"], summary="Estado del servicio")
    def health() -> dict:
        return {"estado": "ok", "entorno": config.entorno}

    @app.exception_handler(RequestValidationError)
    async def solicitud_invalida(_: Request, error: RequestValidationError) -> JSONResponse:
        detalle = "; ".join(f"{'.'.join(str(p) for p in x['loc'][1:])}: {x['msg']}" for x in error.errors())
        return JSONResponse(status_code=400, content={"codigo": "SolicitudInvalida", "mensaje": detalle})

    @app.exception_handler(ErrorDeDominio)
    async def error_de_dominio(_: Request, error: ErrorDeDominio) -> JSONResponse:
        # Cubre los errores que el dominio lanza al construir Value Objects en el borde (p. ej. peso <= 0).
        nombre = type(error).__name__
        return JSONResponse(status_code=codigo_http(nombre), content={"codigo": nombre, "mensaje": str(error)})

    @app.exception_handler(HTTPException)
    async def error_http(_: Request, error: HTTPException) -> JSONResponse:
        d = error.detail
        cuerpo = d if isinstance(d, dict) else {"codigo": "Error", "mensaje": str(d)}
        return JSONResponse(status_code=error.status_code, content=cuerpo)

    return app


def app_de_produccion() -> FastAPI:
    """Fábrica para uvicorn: `uvicorn --factory api.main:app_de_produccion`."""
    return crear_app()
