"""Aggregate Root: OrdenDeServicio (estado, asignación, historial, incidencias, evidencias, cambios operativos).

Los cambios de estado pasan por la State Machine (`CICLO_DE_VIDA_DEL_SERVICIO`) y las reglas de datos
por Specifications; este agregado coordina ambas y protege las invariantes del servicio.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum

from .comunes import (
    CambioPendienteDeRevision,
    ControlDeAltoValorPendiente,
    DatosInvalidos,
    ErrorDeDominio,
    EventoDeDominio,
    OrdenNoGenerable,
    TransicionDeEstadoInvalida,
    ahora,
)
from .cotizacion import Cotizacion
from .especificaciones import (
    AceptadaPorElCliente,
    DatosDeEntrega,
    control_de_alto_valor_cumplido,
    entrega_documentada,
    recepcion_documentada,
    sin_cambio_pendiente,
)
from .eventos import (
    CambioOperativoRevisado,
    CambioOperativoSolicitado,
    CargaDeAltoValorAutorizada,
    EntregaRegistrada,
    EstadoDelServicioCambiado,
    IncidenciaRegistrada,
    OrdenDeServicioGenerada,
    RecursosAsignados,
    ServicioCancelado,
)
from .maquina_de_estados import CICLO_DE_VIDA_DEL_SERVICIO as CICLO, Disparador, EstadoServicio
from .valores import (
    Asignacion,
    Destinatario,
    Evidencia,
    Horario,
    Mercancia,
    PoliticaDeConservacion,
    Ubicacion,
)

__all__ = ["EstadoServicio", "TipoDeIncidencia", "EntradaDeHistorial", "Cancelacion", "Incidencia",
           "CambioOperativo", "OrdenDeServicio"]


class TipoDeIncidencia(Enum):
    UNIDAD_AVERIADA = "UNIDAD_AVERIADA"
    RETRASO = "RETRASO"
    MERCANCIA_DIFERENTE = "MERCANCIA_DIFERENTE"
    MERCANCIA_RECHAZADA = "MERCANCIA_RECHAZADA"
    DIRECCION_INCORRECTA = "DIRECCION_INCORRECTA"
    DESTINATARIO_AUSENTE = "DESTINATARIO_AUSENTE"
    ENTREGA_PARCIAL = "ENTREGA_PARCIAL"
    MERCANCIA_DANADA = "MERCANCIA_DANADA"


@dataclass(frozen=True)
class EntradaDeHistorial:
    fecha: datetime
    descripcion: str
    estado_resultante: EstadoServicio
    registrado_por: str


@dataclass(frozen=True)
class Cancelacion:
    """El glosario exige registrar quién solicita la cancelación y el motivo."""

    solicitado_por: str
    motivo: str
    fecha: datetime


@dataclass(frozen=True)
class CambioOperativo:
    """Solicitud de cambio posterior a la orden que afecta la operación (US-04, BPMN T5/T5B)."""

    solicitado_por: str
    descripcion: str
    fecha: datetime


@dataclass
class Incidencia:
    """Entity (identidad local dentro del agregado)."""

    id: int
    tipo: TipoDeIncidencia
    descripcion: str
    fecha_registro: datetime
    evidencias: list[Evidencia] = field(default_factory=list)


class OrdenDeServicio:
    def __init__(self, id: str, cotizacion_id: str, cliente_id: str, origen: Ubicacion,
                 destino: Ubicacion, mercancia: Mercancia, ruta: str, horario_recoleccion: Horario,
                 fecha_requerida: date | None = None):
        self.id = id
        self.cotizacion_id = cotizacion_id
        self.cliente_id = cliente_id
        self.origen = origen
        self.destino = destino
        self.mercancia = mercancia
        self.ruta = ruta
        self.horario_recoleccion = horario_recoleccion
        self.fecha_requerida = fecha_requerida
        self._alto_valor_autorizado = False
        self._cancelacion: Cancelacion | None = None
        self._cambio_pendiente: CambioOperativo | None = None
        self._fecha_entrega: datetime | None = None
        self._estado = EstadoServicio.CONFIRMADO
        self._asignacion: Asignacion | None = None
        self._historial: list[EntradaDeHistorial] = []
        self._incidencias: list[Incidencia] = []
        self._evidencias_recepcion: list[Evidencia] = []
        self._evidencias_entrega: list[Evidencia] = []
        self._destinatario: Destinatario | None = None
        self._eventos: list[EventoDeDominio] = []

    # ------------------------------ creación ------------------------------
    @classmethod
    def generar_desde(cls, id: str, cotizacion: Cotizacion, ruta: str,
                      horario_recoleccion: Horario, registrado_por: str = "Operaciones") -> "OrdenDeServicio":
        if not AceptadaPorElCliente().es_satisfecha_por(cotizacion):
            raise OrdenNoGenerable(
                f"La orden solo se genera desde una cotización aceptada (cotización {cotizacion.id}: "
                f"{cotizacion.estado.value})."
            )
        if not ruta or not ruta.strip():
            raise DatosInvalidos("La orden requiere una ruta.")
        s = cotizacion.solicitud
        orden = cls(id, cotizacion.id, cotizacion.cliente_id, s.origen, s.destino,
                    s.mercancia, ruta, horario_recoleccion, s.fecha_requerida)
        orden._registrar("Orden de servicio generada", registrado_por)
        orden._eventos.append(OrdenDeServicioGenerada(orden_id=id, cotizacion_id=cotizacion.id))
        return orden

    @classmethod
    def restaurar(cls, *, id: str, cotizacion_id: str, cliente_id: str, origen: Ubicacion, destino: Ubicacion,
                  mercancia: Mercancia, ruta: str, horario_recoleccion: Horario, fecha_requerida: date | None,
                  estado: EstadoServicio, alto_valor_autorizado: bool, asignacion: Asignacion | None,
                  destinatario: Destinatario | None, fecha_entrega: datetime | None,
                  cancelacion: Cancelacion | None, cambio_pendiente: CambioOperativo | None,
                  historial: list[EntradaDeHistorial], incidencias: list[Incidencia],
                  evidencias_recepcion: list[Evidencia], evidencias_entrega: list[Evidencia]) -> "OrdenDeServicio":
        """Reconstituye el agregado desde la persistencia sin disparar reglas ni eventos."""
        orden = cls(id, cotizacion_id, cliente_id, origen, destino, mercancia, ruta, horario_recoleccion,
                    fecha_requerida)
        orden._estado = estado
        orden._alto_valor_autorizado = alto_valor_autorizado
        orden._asignacion = asignacion
        orden._destinatario = destinatario
        orden._fecha_entrega = fecha_entrega
        orden._cancelacion = cancelacion
        orden._cambio_pendiente = cambio_pendiente
        orden._historial = list(historial)
        orden._incidencias = list(incidencias)
        orden._evidencias_recepcion = list(evidencias_recepcion)
        orden._evidencias_entrega = list(evidencias_entrega)
        return orden

    # ------------------------------ consultas del agregado ------------------------------
    def estado_actual(self) -> EstadoServicio:
        return self._estado

    @property
    def asignacion(self) -> Asignacion | None:
        return self._asignacion

    @property
    def historial(self) -> tuple[EntradaDeHistorial, ...]:
        return tuple(self._historial)

    @property
    def incidencias(self) -> tuple[Incidencia, ...]:
        return tuple(self._incidencias)

    @property
    def cancelacion(self) -> Cancelacion | None:
        return self._cancelacion

    @property
    def cambio_pendiente(self) -> CambioOperativo | None:
        return self._cambio_pendiente

    @property
    def fecha_entrega(self) -> datetime | None:
        return self._fecha_entrega

    @property
    def alto_valor_autorizado(self) -> bool:
        return self._alto_valor_autorizado

    def evidencias(self, politica: PoliticaDeConservacion | None = None,
                   hoy: datetime | None = None) -> tuple[Evidencia, ...]:
        """Todas las evidencias asociadas a la orden; con política (S-03) solo las vigentes."""
        todas = [*self._evidencias_recepcion, *self._evidencias_entrega,
                 *(e for i in self._incidencias for e in i.evidencias)]
        if politica is None:
            return tuple(todas)
        momento = hoy or ahora()
        return tuple(e for e in todas if politica.conserva(e, momento))

    @property
    def evidencias_recepcion(self) -> tuple[Evidencia, ...]:
        return tuple(self._evidencias_recepcion)

    @property
    def destinatario(self) -> Destinatario | None:
        return self._destinatario

    @property
    def evidencias_entrega(self) -> tuple[Evidencia, ...]:
        return tuple(self._evidencias_entrega)

    def extraer_eventos(self) -> list[EventoDeDominio]:
        eventos, self._eventos = self._eventos, []
        return eventos

    # ------------------------------ comportamiento ------------------------------
    def asignar_recursos(self, asignacion: Asignacion, registrado_por: str = "Operaciones") -> None:
        """Asigna (o reasigna antes de la recolección) unidad y operador; conserva el historial."""
        self._exigir_sin_cambio_pendiente()
        CICLO.aplicar(self._estado, Disparador.ASIGNAR_RECURSOS, "asignar recursos")
        control = control_de_alto_valor_cumplido()
        if not control.es_satisfecha_por(self):
            raise ControlDeAltoValorPendiente(" ".join(control.motivos_de_incumplimiento(self)))
        es_reasignacion = self._asignacion is not None
        if es_reasignacion:
            descripcion = (f"Asignación actualizada: unidad {self._asignacion.unidad_id}→{asignacion.unidad_id}, "
                           f"operador {self._asignacion.operador_id}→{asignacion.operador_id}")
        else:
            descripcion = f"Unidad {asignacion.unidad_id} y operador {asignacion.operador_id} asignados"
        self._asignacion = asignacion
        self._transicionar(Disparador.ASIGNAR_RECURSOS, descripcion, registrado_por, "asignar recursos")
        self._eventos.append(RecursosAsignados(orden_id=self.id, asignacion=asignacion,
                                               es_reasignacion=es_reasignacion))

    def autorizar_alto_valor(self, autorizado_por: str) -> None:
        """SUPUESTO S-02: la carga de alto valor se autoriza antes de asignar unidad y operador."""
        if not self.mercancia.alto_valor:
            raise ErrorDeDominio(f"La orden {self.id} no es una carga de alto valor.")
        if not autorizado_por or not autorizado_por.strip():
            raise DatosInvalidos("La autorización debe registrar quién la otorga.")
        if not (CICLO.es_valida(self._estado, Disparador.ASIGNAR_RECURSOS)):
            raise TransicionDeEstadoInvalida(
                f"No se puede autorizar la carga de alto valor en estado {self._estado.value} "
                "(se requiere CONFIRMADO o UNIDAD_ASIGNADA)."
            )
        self._alto_valor_autorizado = True
        self._registrar(f"Carga de alto valor autorizada por {autorizado_por}", autorizado_por)
        self._eventos.append(CargaDeAltoValorAutorizada(orden_id=self.id, autorizado_por=autorizado_por))

    def solicitar_cambio_operativo(self, solicitado_por: str, descripcion: str) -> None:
        """US-04: un cambio posterior a la orden que afecta la operación queda pendiente de revisión."""
        if not solicitado_por.strip() or not descripcion.strip():
            raise DatosInvalidos("El cambio debe registrar quién lo solicita y qué cambia.")
        if CICLO.es_terminal(self._estado):
            raise TransicionDeEstadoInvalida(
                f"No se puede solicitar un cambio operativo en estado {self._estado.value}."
            )
        if self._cambio_pendiente is not None:
            raise CambioPendienteDeRevision(
                f"La orden {self.id} ya tiene un cambio operativo pendiente de revisión."
            )
        self._cambio_pendiente = CambioOperativo(solicitado_por, descripcion, ahora())
        self._registrar(f"Cambio operativo solicitado por {solicitado_por}: {descripcion}", solicitado_por)
        self._eventos.append(CambioOperativoSolicitado(orden_id=self.id, solicitado_por=solicitado_por,
                                                       descripcion=descripcion))

    def revisar_cambio_operativo(self, revisado_por: str, aprobado: bool, comentario: str = "") -> None:
        """Operaciones revisa el cambio antes de continuar (US-04, BPMN T5B)."""
        if self._cambio_pendiente is None:
            raise ErrorDeDominio(f"La orden {self.id} no tiene cambios operativos pendientes de revisión.")
        if not revisado_por.strip():
            raise DatosInvalidos("La revisión debe registrar quién la realiza.")
        resultado = "aprobado" if aprobado else "rechazado"
        detalle = f": {comentario}" if comentario else ""
        self._cambio_pendiente = None
        self._registrar(f"Cambio operativo {resultado} por {revisado_por}{detalle}", revisado_por)
        self._eventos.append(CambioOperativoRevisado(orden_id=self.id, revisado_por=revisado_por,
                                                     aprobado=aprobado))

    def cancelar(self, solicitado_por: str, motivo: str) -> None:
        """SUPUESTO S-04: cancela un servicio aceptado; registra quién la solicita y el motivo."""
        if not solicitado_por.strip() or not motivo.strip():
            raise DatosInvalidos("La cancelación debe registrar quién la solicita y el motivo.")
        CICLO.aplicar(self._estado, Disparador.CANCELAR, "cancelar el servicio")
        self._cancelacion = Cancelacion(solicitado_por, motivo, ahora())
        self._cambio_pendiente = None
        self._transicionar(Disparador.CANCELAR,
                           f"Servicio cancelado a solicitud de {solicitado_por}: {motivo}", solicitado_por,
                           "cancelar el servicio")
        self._eventos.append(ServicioCancelado(orden_id=self.id, solicitado_por=solicitado_por, motivo=motivo))

    def registrar_recepcion(self, evidencia: Evidencia, registrado_por: str = "Operador") -> None:
        self._exigir_sin_cambio_pendiente()
        CICLO.aplicar(self._estado, Disparador.REGISTRAR_RECEPCION, "registrar la recepción")
        regla = recepcion_documentada()
        datos = DatosDeEntrega(None, evidencia)
        if not regla.es_satisfecha_por(datos):
            raise DatosInvalidos(" ".join(regla.motivos_de_incumplimiento(datos)))
        self._evidencias_recepcion.append(evidencia)
        self._transicionar(Disparador.REGISTRAR_RECEPCION, "Mercancía recibida y validada en origen",
                           registrado_por, "registrar la recepción")

    def iniciar_traslado(self, registrado_por: str = "Operador") -> None:
        self._exigir_sin_cambio_pendiente()
        self._transicionar(Disparador.INICIAR_TRASLADO, "Traslado iniciado", registrado_por,
                           "iniciar el traslado")

    def registrar_llegada_a_destino(self, registrado_por: str = "Operador") -> None:
        self._exigir_sin_cambio_pendiente()
        self._transicionar(Disparador.REGISTRAR_LLEGADA, "Llegada a destino", registrado_por,
                           "registrar la llegada")

    def registrar_entrega(self, destinatario: Destinatario | None, evidencia: Evidencia | None,
                          registrado_por: str = "Operador") -> None:
        self._exigir_sin_cambio_pendiente()
        CICLO.aplicar(self._estado, Disparador.REGISTRAR_ENTREGA, "registrar la entrega")
        regla = entrega_documentada()
        datos = DatosDeEntrega(destinatario, evidencia)
        if not regla.es_satisfecha_por(datos):
            raise DatosInvalidos(" ".join(regla.motivos_de_incumplimiento(datos)))
        self._destinatario = destinatario
        self._evidencias_entrega.append(evidencia)
        self._fecha_entrega = ahora()
        self._transicionar(Disparador.REGISTRAR_ENTREGA, f"Entrega registrada; recibió {destinatario.identificacion}",
                           registrado_por, "registrar la entrega")
        self._eventos.append(EntregaRegistrada(orden_id=self.id, destinatario=destinatario))

    def registrar_incidencia(self, tipo: TipoDeIncidencia, descripcion: str,
                             evidencia: Evidencia | None = None, registrado_por: str = "Operador") -> None:
        """Registra una incidencia sin cambiar el estado: Operaciones decide el siguiente paso."""
        if CICLO.es_terminal(self._estado):
            raise TransicionDeEstadoInvalida(
                f"No se puede registrar una incidencia en estado {self._estado.value}."
            )
        if not descripcion or not descripcion.strip():
            raise DatosInvalidos("La incidencia requiere una descripción.")
        incidencia = Incidencia(len(self._incidencias) + 1, tipo, descripcion, ahora())
        if evidencia is not None:
            incidencia.evidencias.append(evidencia)
        self._incidencias.append(incidencia)
        self._registrar(f"Incidencia {tipo.value}: {descripcion}", registrado_por)
        self._eventos.append(IncidenciaRegistrada(orden_id=self.id, tipo=tipo))

    # ------------------------------ internos ------------------------------
    def _transicionar(self, disparador: Disparador, descripcion: str, registrado_por: str, accion: str) -> None:
        anterior = self._estado
        self._estado = CICLO.aplicar(anterior, disparador, accion)
        self._registrar(descripcion, registrado_por)
        if self._estado is not anterior:
            self._eventos.append(EstadoDelServicioCambiado(orden_id=self.id, desde=anterior,
                                                           hasta=self._estado, disparador=disparador))

    def _registrar(self, descripcion: str, registrado_por: str) -> None:
        self._historial.append(EntradaDeHistorial(ahora(), descripcion, self._estado, registrado_por))

    def _exigir_sin_cambio_pendiente(self) -> None:
        regla = sin_cambio_pendiente()
        if not regla.es_satisfecha_por(self):
            raise CambioPendienteDeRevision(
                f"La orden {self.id} tiene un cambio operativo pendiente: Operaciones debe revisarlo antes de continuar."
            )
