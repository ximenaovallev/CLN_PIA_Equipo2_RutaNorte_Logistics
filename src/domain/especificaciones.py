"""Specification (patrón): reglas de negocio como objetos combinables con AND, OR y NOT.

Cada regla del BRD se escribe una sola vez como una `Especificacion` pequeña; las reglas compuestas
(p. ej. «unidad adecuada Y operador disponible») se arman combinando, sin editar condicionales (ADR-007).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from .valores import EventoAsociado

if TYPE_CHECKING:  # solo para anotaciones; evita ciclos de importación
    from .cotizacion import Cotizacion
    from .orden_de_servicio import OrdenDeServicio
    from .recursos import Operador, Unidad
    from .valores import Destinatario, Evidencia

T = TypeVar("T")


class Especificacion(ABC, Generic[T]):
    @abstractmethod
    def es_satisfecha_por(self, candidato: T) -> bool: ...

    @property
    def descripcion(self) -> str:
        return type(self).__name__

    def motivos_de_incumplimiento(self, candidato: T) -> list[str]:
        """Mensajes de negocio de las reglas que fallaron (vacío si se cumple)."""
        if self.es_satisfecha_por(candidato):
            return []
        return [self.mensaje_de_incumplimiento(candidato)]

    def mensaje_de_incumplimiento(self, candidato: T) -> str:
        return f"No se cumple: {self.descripcion}."

    def __and__(self, otra: "Especificacion[T]") -> "Especificacion[T]":
        return Y(self, otra)

    def __or__(self, otra: "Especificacion[T]") -> "Especificacion[T]":
        return O(self, otra)

    def __invert__(self) -> "Especificacion[T]":
        return No(self)


class Y(Especificacion[T]):
    def __init__(self, izquierda: Especificacion[T], derecha: Especificacion[T]):
        self._i, self._d = izquierda, derecha

    def es_satisfecha_por(self, candidato: T) -> bool:
        return self._i.es_satisfecha_por(candidato) and self._d.es_satisfecha_por(candidato)

    @property
    def descripcion(self) -> str:
        return f"({self._i.descripcion} Y {self._d.descripcion})"

    def motivos_de_incumplimiento(self, candidato: T) -> list[str]:
        return [*self._i.motivos_de_incumplimiento(candidato), *self._d.motivos_de_incumplimiento(candidato)]


class O(Especificacion[T]):
    def __init__(self, izquierda: Especificacion[T], derecha: Especificacion[T]):
        self._i, self._d = izquierda, derecha

    def es_satisfecha_por(self, candidato: T) -> bool:
        return self._i.es_satisfecha_por(candidato) or self._d.es_satisfecha_por(candidato)

    @property
    def descripcion(self) -> str:
        return f"({self._i.descripcion} O {self._d.descripcion})"

    def motivos_de_incumplimiento(self, candidato: T) -> list[str]:
        if self.es_satisfecha_por(candidato):
            return []
        return [*self._i.motivos_de_incumplimiento(candidato), *self._d.motivos_de_incumplimiento(candidato)]


class No(Especificacion[T]):
    def __init__(self, interna: Especificacion[T]):
        self._interna = interna

    def es_satisfecha_por(self, candidato: T) -> bool:
        return not self._interna.es_satisfecha_por(candidato)

    @property
    def descripcion(self) -> str:
        return f"NO {self._interna.descripcion}"

    def mensaje_de_incumplimiento(self, candidato: T) -> str:
        return f"No debe cumplirse: {self._interna.descripcion}."


# ====================== Asignación de recursos (compuerta G2 del BPMN) ======================
@dataclass(frozen=True)
class CandidatoDeAsignacion:
    orden: "OrdenDeServicio"
    unidad: "Unidad"
    operador: "Operador"


class UnidadConCapacidadSuficiente(Especificacion[CandidatoDeAsignacion]):
    """BRD: la unidad asignada debe tener capacidad suficiente para la carga."""

    descripcion = "la unidad tiene capacidad suficiente"  # type: ignore[assignment]

    def es_satisfecha_por(self, c: CandidatoDeAsignacion) -> bool:
        m, u = c.orden.mercancia, c.unidad.capacidad
        return (m.peso.kilogramos <= u.peso.kilogramos
                and m.dimensiones.volumen.metros_cubicos <= u.volumen.metros_cubicos)

    def mensaje_de_incumplimiento(self, c: CandidatoDeAsignacion) -> str:
        return f"La unidad {c.unidad.id} no es adecuada para la mercancía de la orden {c.orden.id}."


class DentroDeLosLimitesDeLaEmpresa(Especificacion[CandidatoDeAsignacion]):
    """SUPUESTO S-01 (pendiente de validar): topes propios de la empresa; `None` = sin tope adicional."""

    descripcion = "la carga está dentro de los límites de la empresa"  # type: ignore[assignment]

    def __init__(self, peso_maximo_kg: float | None = None, volumen_maximo_m3: float | None = None):
        self._peso, self._volumen = peso_maximo_kg, volumen_maximo_m3

    def es_satisfecha_por(self, c: CandidatoDeAsignacion) -> bool:
        m = c.orden.mercancia
        if self._peso is not None and m.peso.kilogramos > self._peso:
            return False
        return not (self._volumen is not None and m.dimensiones.volumen.metros_cubicos > self._volumen)

    def mensaje_de_incumplimiento(self, c: CandidatoDeAsignacion) -> str:
        return (f"La unidad {c.unidad.id} no es adecuada para la mercancía de la orden {c.orden.id}: "
                "excede el límite propio de la empresa (S-01).")


class OperadorDisponible(Especificacion[CandidatoDeAsignacion]):
    descripcion = "el operador está disponible"  # type: ignore[assignment]

    def es_satisfecha_por(self, c: CandidatoDeAsignacion) -> bool:
        return c.operador.esta_disponible()

    def mensaje_de_incumplimiento(self, c: CandidatoDeAsignacion) -> str:
        return f"El operador {c.operador.id} no está disponible."


def unidad_adecuada(peso_maximo_kg: float | None = None,
                    volumen_maximo_m3: float | None = None) -> Especificacion[CandidatoDeAsignacion]:
    return UnidadConCapacidadSuficiente() & DentroDeLosLimitesDeLaEmpresa(peso_maximo_kg, volumen_maximo_m3)


def asignacion_permitida(peso_maximo_kg: float | None = None,
                         volumen_maximo_m3: float | None = None) -> Especificacion[CandidatoDeAsignacion]:
    """G2: ¿unidad adecuada y operador disponible?"""
    return unidad_adecuada(peso_maximo_kg, volumen_maximo_m3) & OperadorDisponible()


# ====================== Carga de alto valor (SUPUESTO S-02) ======================
class CargaDeAltoValor(Especificacion["OrdenDeServicio"]):
    descripcion = "la carga es de alto valor"  # type: ignore[assignment]

    def es_satisfecha_por(self, orden: "OrdenDeServicio") -> bool:
        return orden.mercancia.alto_valor


class AltoValorAutorizado(Especificacion["OrdenDeServicio"]):
    descripcion = "Operaciones autorizó la carga de alto valor"  # type: ignore[assignment]

    def es_satisfecha_por(self, orden: "OrdenDeServicio") -> bool:
        return orden.alto_valor_autorizado

    def mensaje_de_incumplimiento(self, orden: "OrdenDeServicio") -> str:
        return (f"La orden {orden.id} es de alto valor: Operaciones debe autorizarla antes de asignar recursos.")


class _ControlDeAltoValor(O["OrdenDeServicio"]):
    """(NO alto valor) O (autorizada). Si falla, el único motivo útil para el usuario es la falta de autorización."""

    def motivos_de_incumplimiento(self, orden: "OrdenDeServicio") -> list[str]:
        return [] if self.es_satisfecha_por(orden) else self._d.motivos_de_incumplimiento(orden)


def control_de_alto_valor_cumplido() -> Especificacion["OrdenDeServicio"]:
    """NO alto valor, O ya autorizada (combina NOT y OR)."""
    return _ControlDeAltoValor(~CargaDeAltoValor(), AltoValorAutorizado())


# ====================== Cambios operativos (US-04) ======================
class CambioOperativoPendiente(Especificacion["OrdenDeServicio"]):
    descripcion = "hay un cambio operativo pendiente de revisión"  # type: ignore[assignment]

    def es_satisfecha_por(self, orden: "OrdenDeServicio") -> bool:
        return orden.cambio_pendiente is not None


def sin_cambio_pendiente() -> Especificacion["OrdenDeServicio"]:
    return ~CambioOperativoPendiente()


# ====================== Evidencia y receptor (US-09, US-12, US-13) ======================
@dataclass(frozen=True)
class DatosDeEntrega:
    destinatario: "Destinatario | None"
    evidencia: "Evidencia | None"


class ReceptorIdentificado(Especificacion[DatosDeEntrega]):
    descripcion = "se identificó a quien recibe"  # type: ignore[assignment]

    def es_satisfecha_por(self, d: DatosDeEntrega) -> bool:
        return d.destinatario is not None

    def mensaje_de_incumplimiento(self, d: DatosDeEntrega) -> str:
        return "La entrega requiere identificar a quien recibe."


class EvidenciaDelEvento(Especificacion[DatosDeEntrega]):
    def __init__(self, evento: EventoAsociado):
        self._evento = evento

    @property
    def descripcion(self) -> str:  # type: ignore[override]
        return f"hay evidencia de {self._evento.value.lower()}"

    def es_satisfecha_por(self, d: DatosDeEntrega) -> bool:
        return d.evidencia is not None and d.evidencia.evento_asociado is self._evento

    def mensaje_de_incumplimiento(self, d: DatosDeEntrega) -> str:
        return f"Se requiere evidencia asociada a la {self._evento.value.lower()}."


def entrega_documentada() -> Especificacion[DatosDeEntrega]:
    return ReceptorIdentificado() & EvidenciaDelEvento(EventoAsociado.ENTREGA)


def recepcion_documentada() -> Especificacion[DatosDeEntrega]:
    return EvidenciaDelEvento(EventoAsociado.RECEPCION)


# ====================== Cotización (US-03, US-06, US-17) ======================
class CotizacionEnProceso(Especificacion["Cotizacion"]):
    descripcion = "la cotización está en proceso"  # type: ignore[assignment]

    def es_satisfecha_por(self, c: "Cotizacion") -> bool:
        return c.estado.value == "EN_PROCESO"


class CotizacionConImporte(Especificacion["Cotizacion"]):
    descripcion = "Ventas elaboró la cotización"  # type: ignore[assignment]

    def es_satisfecha_por(self, c: "Cotizacion") -> bool:
        return c.importe_mxn is not None


class AceptadaPorElCliente(Especificacion["Cotizacion"]):
    descripcion = "el cliente aceptó la cotización"  # type: ignore[assignment]

    def es_satisfecha_por(self, c: "Cotizacion") -> bool:
        return c.estado.value == "ACEPTADA"
