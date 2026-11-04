"""Unit of Work SQL: una sesión (transacción) por caso de uso.

El mismo objeto se comparte entre los handlers, y FastAPI atiende peticiones en varios hilos; por eso el estado
de la transacción vive en un `threading.local`: cada hilo tiene su propia sesión y no se mezclan transacciones.
"""
from __future__ import annotations

import threading

from sqlalchemy.orm import Session, sessionmaker

from application.puertos import IUnitOfWork

from .repositorios import (
    SqlClienteRepository,
    SqlCotizacionRepository,
    SqlOperadorRepository,
    SqlOrdenServicioRepository,
    SqlUnidadRepository,
)


class SqlUnitOfWork(IUnitOfWork):
    """La transacción inicia en `with`, `confirmar()` hace commit y cualquier salida sin confirmar hace rollback."""

    def __init__(self, fabrica_de_sesiones: sessionmaker[Session]):
        self._fabrica = fabrica_de_sesiones
        self._local = threading.local()

    # Los repositorios se exponen como propiedades de la transacción del hilo actual.
    @property
    def clientes(self) -> SqlClienteRepository:  # type: ignore[override]
        return self._local.clientes

    @property
    def cotizaciones(self) -> SqlCotizacionRepository:  # type: ignore[override]
        return self._local.cotizaciones

    @property
    def ordenes(self) -> SqlOrdenServicioRepository:  # type: ignore[override]
        return self._local.ordenes

    @property
    def unidades(self) -> SqlUnidadRepository:  # type: ignore[override]
        return self._local.unidades

    @property
    def operadores(self) -> SqlOperadorRepository:  # type: ignore[override]
        return self._local.operadores

    def __enter__(self) -> "SqlUnitOfWork":
        sesion = self._fabrica()
        loc = self._local
        loc.sesion, loc.confirmada = sesion, False
        loc.clientes = SqlClienteRepository(sesion)
        loc.cotizaciones = SqlCotizacionRepository(sesion)
        loc.ordenes = SqlOrdenServicioRepository(sesion)
        loc.unidades = SqlUnidadRepository(sesion)
        loc.operadores = SqlOperadorRepository(sesion)
        return self

    def __exit__(self, tipo, valor, traza) -> None:
        loc = self._local
        sesion: Session | None = getattr(loc, "sesion", None)
        try:
            if sesion is not None and not loc.confirmada:
                sesion.rollback()
        finally:
            if sesion is not None:
                sesion.close()
            loc.sesion = None

    def confirmar(self) -> None:
        loc = self._local
        assert loc.sesion is not None, "confirmar() solo se usa dentro de `with`"
        loc.sesion.commit()
        loc.confirmada = True

    def revertir(self) -> None:
        sesion = getattr(self._local, "sesion", None)
        if sesion is not None:
            sesion.rollback()
