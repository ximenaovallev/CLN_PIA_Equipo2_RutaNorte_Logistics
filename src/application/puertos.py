"""Puertos de la aplicación: el dominio y los casos de uso dependen de abstracciones (DIP)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from domain.comunes import EventoDeDominio
from domain.repositorios import (
    IClienteRepository,
    ICotizacionRepository,
    IOperadorRepository,
    IOrdenServicioRepository,
    IUnidadRepository,
)

from .dto import (
    ClienteDTO,
    CotizacionDTO,
    EstadoDelServicioDTO,
    IndicadoresDTO,
    OperadorDTO,
    OrdenResumenDTO,
    UnidadDTO,
)


class IUnitOfWork(ABC):
    """Una transacción por caso de uso: inicia en `with`, termina con confirmar() o revierte."""
    clientes: IClienteRepository
    cotizaciones: ICotizacionRepository
    ordenes: IOrdenServicioRepository
    unidades: IUnidadRepository
    operadores: IOperadorRepository

    @abstractmethod
    def __enter__(self) -> "IUnitOfWork": ...

    @abstractmethod
    def __exit__(self, tipo, valor, traza) -> None: ...

    @abstractmethod
    def confirmar(self) -> None: ...

    @abstractmethod
    def revertir(self) -> None: ...


class IPublicadorDeEventos(ABC):
    @abstractmethod
    def publicar(self, eventos: list[EventoDeDominio]) -> None: ...


class IConsultaDeServicios(ABC):
    """Puerto de lectura (lado Query de CQRS)."""

    @abstractmethod
    def estado_del_servicio(self, orden_id: str) -> EstadoDelServicioDTO: ...

    @abstractmethod
    def indicadores(self, desde: date, hasta: date) -> IndicadoresDTO: ...

    @abstractmethod
    def cotizacion(self, cotizacion_id: str) -> CotizacionDTO: ...

    @abstractmethod
    def ordenes(self, estado: str | None, limite: int) -> list[OrdenResumenDTO]: ...

    @abstractmethod
    def cliente(self, cliente_id: str) -> ClienteDTO: ...

    @abstractmethod
    def unidad(self, unidad_id: str) -> UnidadDTO: ...

    @abstractmethod
    def operador(self, operador_id: str) -> OperadorDTO: ...
