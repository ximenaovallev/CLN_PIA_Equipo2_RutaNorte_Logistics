"""Aggregate Root: Cotizacion.

Su ciclo coincide con los dos primeros estados del servicio: SOLICITADO (aún sin elaborar) y COTIZADO
(Ventas ya registró el importe). Al aceptarla, el servicio queda CONFIRMADO.
"""
from __future__ import annotations

from decimal import Decimal
from enum import Enum

from .comunes import CotizacionNoElaborada, CotizacionNoModificable, DatosInvalidos, EventoDeDominio
from .especificaciones import CotizacionConImporte, CotizacionEnProceso
from .eventos import CotizacionAceptada, CotizacionElaborada
from .maquina_de_estados import CICLO_DE_VIDA_DEL_SERVICIO as CICLO, Disparador, EstadoServicio
from .valores import SolicitudDeCotizacion


class EstadoCotizacion(Enum):
    EN_PROCESO = "EN_PROCESO"
    ACEPTADA = "ACEPTADA"
    RECHAZADA = "RECHAZADA"


class Cotizacion:
    def __init__(self, id: str, cliente_id: str, solicitud: SolicitudDeCotizacion,
                 importe_mxn: Decimal | None = None, estado: EstadoCotizacion = EstadoCotizacion.EN_PROCESO):
        self.id = id
        self.cliente_id = cliente_id
        self._solicitud = solicitud
        self._importe_mxn = importe_mxn
        self._estado = estado
        self._eventos: list[EventoDeDominio] = []

    @property
    def solicitud(self) -> SolicitudDeCotizacion:
        return self._solicitud

    @property
    def estado(self) -> EstadoCotizacion:
        return self._estado

    @property
    def importe_mxn(self) -> Decimal | None:
        return self._importe_mxn

    @property
    def estado_del_servicio(self) -> EstadoServicio | None:
        """Estado del ciclo de vida del servicio que representa esta cotización (None si se rechazó)."""
        if self._estado is EstadoCotizacion.RECHAZADA:
            return None
        if self._estado is EstadoCotizacion.ACEPTADA:
            return EstadoServicio.CONFIRMADO
        return EstadoServicio.COTIZADO if self._importe_mxn is not None else EstadoServicio.SOLICITADO

    def modificar(self, solicitud: SolicitudDeCotizacion) -> None:
        """Ventas modifica la solicitud mientras está en proceso (US-03); el importe debe volver a elaborarse."""
        self._exigir_en_proceso("modificar")
        self._solicitud = solicitud
        self._importe_mxn = None

    def elaborar(self, importe_mxn: Decimal) -> None:
        """Ventas registra el importe de la cotización (US-02). El BRD no define tarifas: el importe se captura."""
        self._exigir_en_proceso("elaborar")
        if importe_mxn is None or importe_mxn <= 0:
            raise DatosInvalidos("El importe de la cotización debe ser mayor que cero.")
        if self._importe_mxn is None:  # primera elaboración: SOLICITADO → COTIZADO
            CICLO.aplicar(EstadoServicio.SOLICITADO, Disparador.ELABORAR_COTIZACION, "elaborar la cotización")
        self._importe_mxn = Decimal(importe_mxn).quantize(Decimal("0.01"))
        self._eventos.append(CotizacionElaborada(cotizacion_id=self.id, importe_mxn=self._importe_mxn))

    def aceptar(self) -> None:
        self._exigir_en_proceso("aceptar")
        if not CotizacionConImporte().es_satisfecha_por(self):
            raise CotizacionNoElaborada(
                f"No se puede aceptar la cotización {self.id}: Ventas aún no la elabora."
            )
        CICLO.aplicar(EstadoServicio.COTIZADO, Disparador.CONFIRMAR_SERVICIO, "confirmar el servicio")
        self._estado = EstadoCotizacion.ACEPTADA
        self._eventos.append(CotizacionAceptada(cotizacion_id=self.id))

    def rechazar(self) -> None:
        self._exigir_en_proceso("rechazar")
        self._estado = EstadoCotizacion.RECHAZADA

    def esta_aceptada(self) -> bool:
        return self._estado is EstadoCotizacion.ACEPTADA

    def extraer_eventos(self) -> list[EventoDeDominio]:
        eventos, self._eventos = self._eventos, []
        return eventos

    def _exigir_en_proceso(self, accion: str) -> None:
        if not CotizacionEnProceso().es_satisfecha_por(self):
            raise CotizacionNoModificable(
                f"No se puede {accion} la cotización {self.id}: está {self._estado.value}."
            )
