"""State Machine del ciclo de vida del servicio (BRD: ocho estados + CANCELADO por el supuesto S-04).

La tabla de transiciones es el único lugar donde se declara qué cambio de estado es válido. Los
agregados la consultan en lugar de repetir condiciones `if estado == ...` en cada operación.
"""
from __future__ import annotations

from enum import Enum
from typing import Generic, Hashable, TypeVar

from .comunes import TransicionDeEstadoInvalida


class EstadoServicio(Enum):
    SOLICITADO = "SOLICITADO"
    COTIZADO = "COTIZADO"
    CONFIRMADO = "CONFIRMADO"
    UNIDAD_ASIGNADA = "UNIDAD_ASIGNADA"
    RECOLECTADO = "RECOLECTADO"
    EN_TRANSITO = "EN_TRANSITO"
    LLEGADA_A_DESTINO = "LLEGADA_A_DESTINO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"  # SUPUESTO S-04: terminación de un servicio aceptado (glosario: Cancelación)


class Disparador(Enum):
    """Hechos del proceso que provocan un cambio de estado (cada uno corresponde a una tarea del BPMN)."""

    ELABORAR_COTIZACION = "ELABORAR_COTIZACION"    # T2
    CONFIRMAR_SERVICIO = "CONFIRMAR_SERVICIO"      # T4 (cliente acepta y se genera la orden)
    ASIGNAR_RECURSOS = "ASIGNAR_RECURSOS"          # T8 (también reasigna: T7)
    REGISTRAR_RECEPCION = "REGISTRAR_RECEPCION"    # T10
    INICIAR_TRASLADO = "INICIAR_TRASLADO"          # T11
    REGISTRAR_LLEGADA = "REGISTRAR_LLEGADA"        # T16
    REGISTRAR_ENTREGA = "REGISTRAR_ENTREGA"        # T19
    CANCELAR = "CANCELAR"                          # T5A (S-04)


E = TypeVar("E", bound=Hashable)
D = TypeVar("D", bound=Hashable)


class MaquinaDeEstados(Generic[E, D]):
    def __init__(self, transiciones: dict[tuple[E, D], E], inicial: E):
        self._transiciones = dict(transiciones)
        self.inicial = inicial

    def aplicar(self, estado: E, disparador: D, accion: str = "") -> E:
        """Devuelve el estado destino o lanza `TransicionDeEstadoInvalida` explicando qué se requería."""
        destino = self._transiciones.get((estado, disparador))
        if destino is None:
            origenes = " o ".join(sorted(e.value for e in self.estados_origen(disparador))) or "ninguno"
            que = accion or getattr(disparador, "value", str(disparador))
            raise TransicionDeEstadoInvalida(
                f"No se puede {que} en estado {getattr(estado, 'value', estado)} (se requiere {origenes})."
            )
        return destino

    def es_valida(self, estado: E, disparador: D) -> bool:
        return (estado, disparador) in self._transiciones

    def estados_origen(self, disparador: D) -> set[E]:
        return {e for (e, d) in self._transiciones if d == disparador}

    def disparadores_permitidos(self, estado: E) -> set[D]:
        return {d for (e, d) in self._transiciones if e == estado}

    def es_terminal(self, estado: E) -> bool:
        return not self.disparadores_permitidos(estado)

    def transiciones(self) -> list[tuple[E, D, E]]:
        return [(e, d, destino) for (e, d), destino in self._transiciones.items()]


_S, _D = EstadoServicio, Disparador

CICLO_DE_VIDA_DEL_SERVICIO: MaquinaDeEstados[EstadoServicio, Disparador] = MaquinaDeEstados(
    {
        (_S.SOLICITADO, _D.ELABORAR_COTIZACION): _S.COTIZADO,
        (_S.COTIZADO, _D.CONFIRMAR_SERVICIO): _S.CONFIRMADO,
        (_S.CONFIRMADO, _D.ASIGNAR_RECURSOS): _S.UNIDAD_ASIGNADA,
        (_S.UNIDAD_ASIGNADA, _D.ASIGNAR_RECURSOS): _S.UNIDAD_ASIGNADA,  # reasignación (US-08)
        (_S.UNIDAD_ASIGNADA, _D.REGISTRAR_RECEPCION): _S.RECOLECTADO,
        (_S.RECOLECTADO, _D.INICIAR_TRASLADO): _S.EN_TRANSITO,
        (_S.EN_TRANSITO, _D.REGISTRAR_LLEGADA): _S.LLEGADA_A_DESTINO,
        (_S.LLEGADA_A_DESTINO, _D.REGISTRAR_ENTREGA): _S.ENTREGADO,
        (_S.CONFIRMADO, _D.CANCELAR): _S.CANCELADO,
        (_S.UNIDAD_ASIGNADA, _D.CANCELAR): _S.CANCELADO,
        (_S.RECOLECTADO, _D.CANCELAR): _S.CANCELADO,
        (_S.EN_TRANSITO, _D.CANCELAR): _S.CANCELADO,
        (_S.LLEGADA_A_DESTINO, _D.CANCELAR): _S.CANCELADO,
    },
    inicial=_S.SOLICITADO,
)
