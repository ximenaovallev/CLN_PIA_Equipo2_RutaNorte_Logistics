"""Publicación de Domain Events: se registran en la tabla `eventos_de_dominio` (bitácora auditable)."""
from __future__ import annotations

import dataclasses
import json
import logging
from enum import Enum

from sqlalchemy import insert
from sqlalchemy.orm import Session, sessionmaker

from application.puertos import IPublicadorDeEventos
from domain.comunes import EventoDeDominio

from . import tablas as t
from .repositorios import a_utc

_log = logging.getLogger("rutanorte.eventos")


def _serializable(valor):
    if isinstance(valor, Enum):
        return valor.value
    if dataclasses.is_dataclass(valor):
        return dataclasses.asdict(valor)
    return str(valor)


class SqlPublicadorDeEventos(IPublicadorDeEventos):
    def __init__(self, fabrica_de_sesiones: sessionmaker[Session]):
        self._fabrica = fabrica_de_sesiones

    def publicar(self, eventos: list[EventoDeDominio]) -> None:
        if not eventos:
            return
        with self._fabrica() as sesion:
            for e in eventos:
                datos = {k: v for k, v in dataclasses.asdict(e).items() if k != "ocurrio_en"}
                agregado = datos.get("orden_id") or datos.get("cotizacion_id")
                sesion.execute(insert(t.eventos_de_dominio).values(
                    tipo=type(e).__name__, agregado_id=agregado,
                    datos=json.dumps(datos, default=_serializable, ensure_ascii=False),
                    ocurrio_en=a_utc(e.ocurrio_en)))
                _log.info("evento %s agregado=%s", type(e).__name__, agregado)
            sesion.commit()
