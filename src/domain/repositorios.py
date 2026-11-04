"""Interfaces de Repository en términos del dominio (sin SQL ni detalles de infraestructura)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from .cliente import Cliente
from .cotizacion import Cotizacion
from .orden_de_servicio import OrdenDeServicio
from .recursos import Operador, Unidad


class IClienteRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, id: str) -> Cliente: ...

    @abstractmethod
    def existe(self, id: str) -> bool: ...

    @abstractmethod
    def guardar(self, cliente: Cliente) -> None: ...


class ICotizacionRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, id: str) -> Cotizacion: ...

    @abstractmethod
    def guardar(self, cotizacion: Cotizacion) -> None: ...


class IOrdenServicioRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, id: str) -> OrdenDeServicio: ...

    @abstractmethod
    def guardar(self, orden: OrdenDeServicio) -> None: ...


class IUnidadRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, id: str) -> Unidad: ...

    @abstractmethod
    def existe(self, id: str) -> bool: ...

    @abstractmethod
    def guardar(self, unidad: Unidad) -> None: ...


class IOperadorRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, id: str) -> Operador: ...

    @abstractmethod
    def existe(self, id: str) -> bool: ...

    @abstractmethod
    def guardar(self, operador: Operador) -> None: ...
