"""Lado de lectura (Query de CQRS) sobre SQL: sesiones de solo lectura que devuelven View Models."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from application.dto import (
    ClienteDTO, CotizacionDTO, EstadoDelServicioDTO, IndicadoresDTO, OperadorDTO, OrdenResumenDTO, UnidadDTO,
)
from application.puertos import IConsultaDeServicios

from ..vistas import dto_cotizacion, dto_estado, dto_indicadores, dto_resumen
from . import tablas as t
from .repositorios import (
    SqlClienteRepository, SqlCotizacionRepository, SqlOperadorRepository, SqlOrdenServicioRepository,
    SqlUnidadRepository,
)


class SqlConsultaDeServicios(IConsultaDeServicios):
    def __init__(self, fabrica_de_sesiones: sessionmaker[Session]):
        self._fabrica = fabrica_de_sesiones

    def estado_del_servicio(self, orden_id: str) -> EstadoDelServicioDTO:
        with self._fabrica() as s:
            return dto_estado(SqlOrdenServicioRepository(s).obtener_por_id(orden_id))

    def indicadores(self, desde: date, hasta: date) -> IndicadoresDTO:
        with self._fabrica() as s:
            repo = SqlOrdenServicioRepository(s)
            ids = [r.id for r in s.execute(select(t.ordenes.c.id))]
            return dto_indicadores([repo.obtener_por_id(i) for i in ids], desde, hasta)

    def cotizacion(self, cotizacion_id: str) -> CotizacionDTO:
        with self._fabrica() as s:
            return dto_cotizacion(SqlCotizacionRepository(s).obtener_por_id(cotizacion_id))

    def ordenes(self, estado: str | None, limite: int) -> list[OrdenResumenDTO]:
        with self._fabrica() as s:
            consulta = select(t.ordenes.c.id).order_by(t.ordenes.c.id).limit(limite)
            if estado is not None:
                consulta = consulta.where(t.ordenes.c.estado == estado)
            repo = SqlOrdenServicioRepository(s)
            return [dto_resumen(repo.obtener_por_id(r.id)) for r in s.execute(consulta).all()]

    def cliente(self, cliente_id: str) -> ClienteDTO:
        with self._fabrica() as s:
            c = SqlClienteRepository(s).obtener_por_id(cliente_id)
            return ClienteDTO(c.id, c.nombre, c.ciudad)

    def unidad(self, unidad_id: str) -> UnidadDTO:
        with self._fabrica() as s:
            u = SqlUnidadRepository(s).obtener_por_id(unidad_id)
            return UnidadDTO(u.id, u.tipo, u.capacidad.peso.kilogramos, u.capacidad.volumen.metros_cubicos)

    def operador(self, operador_id: str) -> OperadorDTO:
        with self._fabrica() as s:
            o = SqlOperadorRepository(s).obtener_por_id(operador_id)
            return OperadorDTO(o.id, o.nombre, o.esta_disponible())
