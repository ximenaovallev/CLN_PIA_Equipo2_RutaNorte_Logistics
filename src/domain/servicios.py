"""Domain Services: comportamiento del dominio que no pertenece a una sola entidad."""
from __future__ import annotations

from .comunes import RecursosNoDisponibles, SinAutoridadParaCancelar
from .especificaciones import CandidatoDeAsignacion, Especificacion, asignacion_permitida
from .orden_de_servicio import OrdenDeServicio
from .recursos import Operador, Unidad
from .valores import Asignacion


class AsignadorDeRecursos:
    """La regla G2 (¿unidad adecuada y operador disponible?) involucra orden, unidad y operador.

    Recibe la Specification que la define (ADR-007), de modo que cambiar la política no exige editar este servicio.
    """

    def __init__(self, regla: Especificacion[CandidatoDeAsignacion] | None = None):
        self._regla = regla or asignacion_permitida()

    def validar_y_crear(self, orden: OrdenDeServicio, unidad: Unidad, operador: Operador) -> Asignacion:
        candidato = CandidatoDeAsignacion(orden, unidad, operador)
        if not self._regla.es_satisfecha_por(candidato):
            raise RecursosNoDisponibles(" ".join(self._regla.motivos_de_incumplimiento(candidato)))
        return Asignacion(unidad_id=unidad.id, operador_id=operador.id)


class AutoridadDeCancelacion:
    """SUPUESTO S-04 (pendiente de validar): qué roles pueden cancelar un servicio aceptado.

    El BRD solo exige registrar quién solicita la cancelación y el motivo; por defecto se asume que
    Operaciones, que administra la orden, es quien la autoriza. Es un parámetro, no una regla fija.
    """

    def __init__(self, roles_autorizados: frozenset[str] = frozenset({"Operaciones"})):
        self._roles = roles_autorizados

    def verificar(self, rol: str) -> None:
        if rol not in self._roles:
            raise SinAutoridadParaCancelar(
                f"El rol {rol} no tiene autoridad para cancelar un servicio (autorizados: {', '.join(sorted(self._roles))})."
            )
