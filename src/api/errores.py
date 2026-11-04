"""Contrato de códigos HTTP del equipo (la API traduce, el dominio no sabe de HTTP):

* 400 — datos mal formados o inválidos (formato, tipos, valores fuera de rango).
* 404 — el recurso no existe.
* 409 — conflicto con el estado actual del recurso (transición inválida, duplicado, cotización no modificable).
* 422 — datos válidos pero una regla de negocio no se cumple (recursos no adecuados, alto valor sin autorizar…).
"""
from __future__ import annotations

HTTP_POR_ERROR_DE_DOMINIO: dict[str, int] = {
    "DatosInvalidos": 400,
    "EntidadNoEncontrada": 404,
    "TransicionDeEstadoInvalida": 409,
    "EntidadYaExiste": 409,
    "CotizacionNoModificable": 409,
    "CambioPendienteDeRevision": 409,
    "RecursosNoDisponibles": 422,
    "ControlDeAltoValorPendiente": 422,
    "SinAutoridadParaCancelar": 422,
    "OrdenNoGenerable": 422,
    "CotizacionNoElaborada": 422,
}


def codigo_http(codigo_de_error: str | None) -> int:
    return HTTP_POR_ERROR_DE_DOMINIO.get(codigo_de_error or "", 422)
