"""Implementaciones en memoria de los puertos.

Sirven para pruebas rápidas y para demostrar que el dominio y la aplicación no dependen de la
tecnología de almacenamiento (ADR-002): cualquier implementación debe cumplir el mismo contrato
(las pruebas de contrato se ejecutan contra esta y contra la implementación SQL).
"""
from __future__ import annotations

import copy
from datetime import date

from application.dto import (
    ClienteDTO,
    CotizacionDTO,
    EstadoDelServicioDTO,
    IndicadoresDTO,
    OperadorDTO,
    OrdenResumenDTO,
    UnidadDTO,
)
from application.puertos import IConsultaDeServicios, IPublicadorDeEventos, IUnitOfWork
from domain.cliente import Cliente
from domain.comunes import EntidadNoEncontrada, EventoDeDominio
from domain.cotizacion import Cotizacion
from domain.orden_de_servicio import OrdenDeServicio
from domain.recursos import Operador, Unidad
from domain.repositorios import (
    IClienteRepository,
    ICotizacionRepository,
    IOperadorRepository,
    IOrdenServicioRepository,
    IUnidadRepository,
)

from .vistas import dto_cotizacion, dto_estado, dto_indicadores, dto_resumen


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.clientes: dict[str, Cliente] = {}
        self.cotizaciones: dict[str, Cotizacion] = {}
        self.ordenes: dict[str, OrdenDeServicio] = {}
        self.unidades: dict[str, Unidad] = {}
        self.operadores: dict[str, Operador] = {}

    def _tablas(self) -> tuple[dict, ...]:
        return self.clientes, self.cotizaciones, self.ordenes, self.unidades, self.operadores

    def instantanea(self) -> tuple[dict, ...]:
        return tuple(copy.deepcopy(t) for t in self._tablas())

    def restaurar(self, instantanea: tuple[dict, ...]) -> None:
        for tabla, copia in zip(self._tablas(), instantanea):
            tabla.clear()
            tabla.update(copia)


def _obtener(tabla: dict, id: str, nombre: str):
    try:
        return tabla[id]
    except KeyError:
        raise EntidadNoEncontrada(f"No existe {nombre} con identificador {id}.") from None


class _RepositorioEnMemoria:
    nombre = ""
    tabla_de = staticmethod(lambda a: {})

    def __init__(self, almacen: AlmacenEnMemoria):
        self._a = almacen

    def obtener_por_id(self, id: str):
        return _obtener(self.tabla_de(self._a), id, self.nombre)

    def existe(self, id: str) -> bool:
        return id in self.tabla_de(self._a)

    def guardar(self, entidad) -> None:
        self.tabla_de(self._a)[entidad.id] = entidad


class EnMemoriaClienteRepository(_RepositorioEnMemoria, IClienteRepository):
    nombre, tabla_de = "el cliente", staticmethod(lambda a: a.clientes)


class EnMemoriaCotizacionRepository(_RepositorioEnMemoria, ICotizacionRepository):
    nombre, tabla_de = "la cotización", staticmethod(lambda a: a.cotizaciones)


class EnMemoriaOrdenServicioRepository(_RepositorioEnMemoria, IOrdenServicioRepository):
    nombre, tabla_de = "la orden de servicio", staticmethod(lambda a: a.ordenes)


class EnMemoriaUnidadRepository(_RepositorioEnMemoria, IUnidadRepository):
    nombre, tabla_de = "la unidad", staticmethod(lambda a: a.unidades)


class EnMemoriaOperadorRepository(_RepositorioEnMemoria, IOperadorRepository):
    nombre, tabla_de = "el operador", staticmethod(lambda a: a.operadores)


class EnMemoriaUnitOfWork(IUnitOfWork):
    """Transacción simulada: instantánea al entrar; se restaura si no se confirmó."""

    def __init__(self, almacen: AlmacenEnMemoria):
        self._almacen = almacen
        self.clientes = EnMemoriaClienteRepository(almacen)
        self.cotizaciones = EnMemoriaCotizacionRepository(almacen)
        self.ordenes = EnMemoriaOrdenServicioRepository(almacen)
        self.unidades = EnMemoriaUnidadRepository(almacen)
        self.operadores = EnMemoriaOperadorRepository(almacen)
        self._instantanea = None
        self._confirmada = False

    def __enter__(self) -> "EnMemoriaUnitOfWork":
        self._instantanea = self._almacen.instantanea()
        self._confirmada = False
        return self

    def __exit__(self, tipo, valor, traza) -> None:
        if not self._confirmada:
            self.revertir()

    def confirmar(self) -> None:
        self._confirmada = True
        self._instantanea = None

    def revertir(self) -> None:
        if self._instantanea is not None:
            self._almacen.restaurar(self._instantanea)
            self._instantanea = None


class PublicadorDeEventosEnMemoria(IPublicadorDeEventos):
    def __init__(self) -> None:
        self.publicados: list[EventoDeDominio] = []

    def publicar(self, eventos: list[EventoDeDominio]) -> None:
        self.publicados.extend(eventos)


class EnMemoriaConsultaDeServicios(IConsultaDeServicios):
    """Lado de lectura: construye View Models sin exponer el modelo de escritura."""

    def __init__(self, almacen: AlmacenEnMemoria):
        self._a = almacen

    def estado_del_servicio(self, orden_id: str) -> EstadoDelServicioDTO:
        return dto_estado(_obtener(self._a.ordenes, orden_id, "la orden de servicio"))

    def indicadores(self, desde: date, hasta: date) -> IndicadoresDTO:
        return dto_indicadores(list(self._a.ordenes.values()), desde, hasta)

    def cotizacion(self, cotizacion_id: str) -> CotizacionDTO:
        return dto_cotizacion(_obtener(self._a.cotizaciones, cotizacion_id, "la cotización"))

    def ordenes(self, estado: str | None, limite: int) -> list[OrdenResumenDTO]:
        todas = [o for o in self._a.ordenes.values() if estado is None or o.estado_actual().value == estado]
        return [dto_resumen(o) for o in todas[:limite]]

    def cliente(self, cliente_id: str) -> ClienteDTO:
        c = _obtener(self._a.clientes, cliente_id, "el cliente")
        return ClienteDTO(c.id, c.nombre, c.ciudad)

    def unidad(self, unidad_id: str) -> UnidadDTO:
        u = _obtener(self._a.unidades, unidad_id, "la unidad")
        return UnidadDTO(u.id, u.tipo, u.capacidad.peso.kilogramos, u.capacidad.volumen.metros_cubicos)

    def operador(self, operador_id: str) -> OperadorDTO:
        o = _obtener(self._a.operadores, operador_id, "el operador")
        return OperadorDTO(o.id, o.nombre, o.esta_disponible())
