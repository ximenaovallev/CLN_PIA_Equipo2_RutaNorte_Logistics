"""Service Layer: cada handler coordina un caso de uso.

Recibe la solicitud, obtiene los objetos, invoca el comportamiento del dominio, pide la
persistencia y devuelve un resultado. Las reglas del negocio viven en el dominio.
"""
from __future__ import annotations

from typing import Callable
from uuid import uuid4

from domain.cliente import Cliente
from domain.comunes import EntidadYaExiste, ErrorDeDominio, EventoDeDominio
from domain.cotizacion import Cotizacion
from domain.orden_de_servicio import OrdenDeServicio
from domain.recursos import Operador, Unidad
from domain.servicios import AsignadorDeRecursos, AutoridadDeCancelacion
from domain.valores import Capacidad, Horario, Peso, Volumen

from .comandos import (
    AsignarRecursosCommand,
    AutorizarCargaDeAltoValorCommand,
    CambiarDisponibilidadDeOperadorCommand,
    CancelarServicioCommand,
    ConsultarClienteQuery,
    ConsultarCotizacionQuery,
    ConsultarEstadoDelServicioQuery,
    ConsultarIndicadoresQuery,
    ConsultarOperadorQuery,
    ConsultarUnidadQuery,
    ElaborarCotizacionCommand,
    GenerarOrdenDeServicioCommand,
    IniciarTrasladoCommand,
    ListarOrdenesQuery,
    ModificarCotizacionCommand,
    RegistrarClienteCommand,
    RegistrarEntregaCommand,
    RegistrarIncidenciaCommand,
    RegistrarLlegadaCommand,
    RegistrarOperadorCommand,
    RegistrarRecepcionCommand,
    RegistrarUnidadCommand,
    RespuestaDelCliente,
    ResponderCotizacionCommand,
    RevisarCambioOperativoCommand,
    SolicitarCambioOperativoCommand,
    SolicitarCotizacionCommand,
)
from .dto import (
    ClienteDTO,
    CotizacionDTO,
    EstadoDelServicioDTO,
    IndicadoresDTO,
    OperadorDTO,
    OrdenResumenDTO,
    Resultado,
    UnidadDTO,
)
from .puertos import IConsultaDeServicios, IPublicadorDeEventos, IUnitOfWork

Trabajo = Callable[[IUnitOfWork], tuple[list[EventoDeDominio], dict]]


class _Handler:
    """Plantilla común: una transacción por caso de uso; los eventos se publican solo tras confirmar."""

    def __init__(self, uow: IUnitOfWork, publicador: IPublicadorDeEventos):
        self._uow, self._publicador = uow, publicador

    def _ejecutar(self, mensaje: str, trabajo: Trabajo) -> Resultado:
        try:
            with self._uow as uow:  # si hay un error de dominio, el `with` revierte la transacción
                eventos, datos = trabajo(uow)
                uow.confirmar()
        except ErrorDeDominio as error:
            return Resultado.fallo(str(error), codigo=type(error).__name__)
        self._publicador.publicar(eventos)
        return Resultado.ok(mensaje, **datos)


# ============================ Catálogos de apoyo ============================
class RegistrarClienteHandler(_Handler):
    def handle(self, cmd: RegistrarClienteCommand) -> Resultado:
        def trabajo(uow: IUnitOfWork):
            if uow.clientes.existe(cmd.id):
                raise EntidadYaExiste(f"Ya existe el cliente {cmd.id}.")
            uow.clientes.guardar(Cliente(cmd.id, cmd.nombre, cmd.ciudad))
            return [], {"cliente_id": cmd.id}
        return self._ejecutar("Cliente registrado.", trabajo)


class RegistrarUnidadHandler(_Handler):
    def handle(self, cmd: RegistrarUnidadCommand) -> Resultado:
        def trabajo(uow: IUnitOfWork):
            if uow.unidades.existe(cmd.id):
                raise EntidadYaExiste(f"Ya existe la unidad {cmd.id}.")
            uow.unidades.guardar(Unidad(cmd.id, cmd.tipo, Capacidad(Peso(cmd.peso_kg), Volumen(cmd.volumen_m3))))
            return [], {"unidad_id": cmd.id}
        return self._ejecutar("Unidad registrada.", trabajo)


class RegistrarOperadorHandler(_Handler):
    def handle(self, cmd: RegistrarOperadorCommand) -> Resultado:
        def trabajo(uow: IUnitOfWork):
            if uow.operadores.existe(cmd.id):
                raise EntidadYaExiste(f"Ya existe el operador {cmd.id}.")
            uow.operadores.guardar(Operador(cmd.id, cmd.nombre, cmd.disponible))
            return [], {"operador_id": cmd.id}
        return self._ejecutar("Operador registrado.", trabajo)


class CambiarDisponibilidadDeOperadorHandler(_Handler):
    def handle(self, cmd: CambiarDisponibilidadDeOperadorCommand) -> Resultado:
        def trabajo(uow: IUnitOfWork):
            operador = uow.operadores.obtener_por_id(cmd.operador_id)
            operador.marcar_disponibilidad(cmd.disponible)
            uow.operadores.guardar(operador)
            return [], {"disponible": cmd.disponible}
        return self._ejecutar("Disponibilidad del operador actualizada.", trabajo)


# ============================ Cotización ============================
class SolicitarCotizacionHandler(_Handler):
    """US-01 Solicitud de cotización (estado SOLICITADO)."""

    def handle(self, cmd: SolicitarCotizacionCommand) -> Resultado:
        def trabajo(uow: IUnitOfWork):
            uow.clientes.obtener_por_id(cmd.cliente_id)  # el solicitante debe estar registrado
            cotizacion = Cotizacion(str(uuid4()), cmd.cliente_id, cmd.solicitud)
            uow.cotizaciones.guardar(cotizacion)
            return cotizacion.extraer_eventos(), {"cotizacion_id": cotizacion.id, "estado": "SOLICITADO"}
        return self._ejecutar("Solicitud de cotización registrada.", trabajo)


class ElaborarCotizacionHandler(_Handler):
    """US-02 Elaboración de cotización por Ventas (estado COTIZADO)."""

    def handle(self, cmd: ElaborarCotizacionCommand) -> Resultado:
        def trabajo(uow: IUnitOfWork):
            cotizacion = uow.cotizaciones.obtener_por_id(cmd.cotizacion_id)
            cotizacion.elaborar(cmd.importe_mxn)
            uow.cotizaciones.guardar(cotizacion)
            return cotizacion.extraer_eventos(), {"estado": cotizacion.estado_del_servicio.value}
        return self._ejecutar("Cotización elaborada.", trabajo)


class ModificarCotizacionHandler(_Handler):
    """US-03 Modificación de cotización mientras está en proceso."""

    def handle(self, cmd: ModificarCotizacionCommand) -> Resultado:
        def trabajo(uow: IUnitOfWork):
            cotizacion = uow.cotizaciones.obtener_por_id(cmd.cotizacion_id)
            cotizacion.modificar(cmd.solicitud)
            uow.cotizaciones.guardar(cotizacion)
            return cotizacion.extraer_eventos(), {"estado": cotizacion.estado_del_servicio.value}
        return self._ejecutar("Cotización modificada.", trabajo)


class ResponderCotizacionHandler(_Handler):
    """CU-01 Responder cotización (US-17)."""

    def handle(self, cmd: ResponderCotizacionCommand) -> Resultado:
        def trabajo(uow: IUnitOfWork):
            cotizacion = uow.cotizaciones.obtener_por_id(cmd.cotizacion_id)
            if cmd.respuesta is RespuestaDelCliente.ACEPTA:
                cotizacion.aceptar()
            else:
                cotizacion.rechazar()
            uow.cotizaciones.guardar(cotizacion)
            return cotizacion.extraer_eventos(), {"estado": cotizacion.estado.value}
        resultado = self._ejecutar("Cotización respondida.", trabajo)
        return Resultado.ok(f"Cotización {resultado.datos['estado']}.", **resultado.datos) if resultado.exito \
            else resultado


# ============================ Orden de servicio ============================
class GenerarOrdenDeServicioHandler(_Handler):
    """CU-02 Generar orden de servicio."""

    def handle(self, cmd: GenerarOrdenDeServicioCommand) -> Resultado:
        def trabajo(uow: IUnitOfWork):
            cotizacion = uow.cotizaciones.obtener_por_id(cmd.cotizacion_id)
            orden = OrdenDeServicio.generar_desde(
                id=str(uuid4()), cotizacion=cotizacion, ruta=cmd.ruta,
                horario_recoleccion=Horario(cmd.horario_recoleccion),
            )
            uow.ordenes.guardar(orden)
            return orden.extraer_eventos(), {"orden_id": orden.id, "estado": orden.estado_actual().value}
        return self._ejecutar("Orden de servicio generada.", trabajo)


class _HandlerDeOrden(_Handler):
    """Carga la orden, aplica `operacion` sobre ella y la guarda."""

    def _sobre_orden(self, orden_id: str, mensaje: str, operacion) -> Resultado:
        def trabajo(uow: IUnitOfWork):
            orden = uow.ordenes.obtener_por_id(orden_id)
            operacion(orden, uow)
            uow.ordenes.guardar(orden)
            return orden.extraer_eventos(), {"estado": orden.estado_actual().value}
        return self._ejecutar(mensaje, trabajo)


class AutorizarCargaDeAltoValorHandler(_HandlerDeOrden):
    """CU-07 Autorizar carga de alto valor (SUPUESTO S-02, US-16)."""

    def handle(self, cmd: AutorizarCargaDeAltoValorCommand) -> Resultado:
        return self._sobre_orden(cmd.orden_id, "Carga de alto valor autorizada.",
                                 lambda orden, uow: orden.autorizar_alto_valor(cmd.autorizado_por))


class CancelarServicioHandler(_HandlerDeOrden):
    """CU-06 Cancelar servicio (SUPUESTO S-04, US-05): registra quién la solicita y el motivo."""

    def __init__(self, uow: IUnitOfWork, publicador: IPublicadorDeEventos, autoridad: AutoridadDeCancelacion):
        super().__init__(uow, publicador)
        self._autoridad = autoridad

    def handle(self, cmd: CancelarServicioCommand) -> Resultado:
        try:
            self._autoridad.verificar(cmd.rol_que_autoriza)
        except ErrorDeDominio as error:
            return Resultado.fallo(str(error), codigo=type(error).__name__)
        return self._sobre_orden(cmd.orden_id, "Servicio cancelado.",
                                 lambda orden, uow: orden.cancelar(cmd.solicitado_por, cmd.motivo))


class SolicitarCambioOperativoHandler(_HandlerDeOrden):
    """US-04 Solicitud de un cambio que afecta la operación (queda pendiente de revisión)."""

    def handle(self, cmd: SolicitarCambioOperativoCommand) -> Resultado:
        return self._sobre_orden(cmd.orden_id, "Cambio operativo registrado; pendiente de revisión.",
                                 lambda orden, uow: orden.solicitar_cambio_operativo(cmd.solicitado_por,
                                                                                      cmd.descripcion))


class RevisarCambioOperativoHandler(_HandlerDeOrden):
    """US-04 Revisión del cambio por Operaciones antes de continuar."""

    def handle(self, cmd: RevisarCambioOperativoCommand) -> Resultado:
        return self._sobre_orden(cmd.orden_id, "Cambio operativo revisado.",
                                 lambda orden, uow: orden.revisar_cambio_operativo(cmd.revisado_por, cmd.aprobado,
                                                                                    cmd.comentario))


class AsignarRecursosHandler(_HandlerDeOrden):
    """CU-03 Asignar unidad y operador (también reasigna si el operador cambia; US-07, US-08)."""

    def __init__(self, uow: IUnitOfWork, publicador: IPublicadorDeEventos, asignador: AsignadorDeRecursos):
        super().__init__(uow, publicador)
        self._asignador = asignador

    def handle(self, cmd: AsignarRecursosCommand) -> Resultado:
        def operacion(orden: OrdenDeServicio, uow: IUnitOfWork) -> None:
            unidad = uow.unidades.obtener_por_id(cmd.unidad_id)
            operador = uow.operadores.obtener_por_id(cmd.operador_id)
            asignacion = self._asignador.validar_y_crear(orden, unidad, operador)  # regla G2
            orden.asignar_recursos(asignacion, registrado_por="Operaciones")
        return self._sobre_orden(cmd.orden_id, "Unidad y operador asignados.", operacion)


class RegistrarRecepcionHandler(_HandlerDeOrden):
    """US-09 Recepción y validación de la mercancía en origen."""

    def handle(self, cmd: RegistrarRecepcionCommand) -> Resultado:
        return self._sobre_orden(cmd.orden_id, "Recepción registrada.",
                                 lambda orden, uow: orden.registrar_recepcion(cmd.evidencia))


class IniciarTrasladoHandler(_HandlerDeOrden):
    """US-10 Actualización de estado: traslado iniciado."""

    def handle(self, cmd: IniciarTrasladoCommand) -> Resultado:
        return self._sobre_orden(cmd.orden_id, "Traslado iniciado.",
                                 lambda orden, uow: orden.iniciar_traslado())


class RegistrarLlegadaHandler(_HandlerDeOrden):
    """US-12 Registro de llegada a destino."""

    def handle(self, cmd: RegistrarLlegadaCommand) -> Resultado:
        return self._sobre_orden(cmd.orden_id, "Llegada registrada.",
                                 lambda orden, uow: orden.registrar_llegada_a_destino())


class RegistrarEntregaHandler(_HandlerDeOrden):
    """CU-04 Registrar entrega o incidencia en destino (US-11, US-12, US-13)."""

    def handle(self, cmd: RegistrarEntregaCommand) -> Resultado:
        def operacion(orden: OrdenDeServicio, uow: IUnitOfWork) -> None:
            if cmd.incidencia is None:
                orden.registrar_entrega(cmd.destinatario, cmd.evidencia)
            else:
                orden.registrar_incidencia(cmd.incidencia, cmd.descripcion_incidencia, cmd.evidencia)
        return self._sobre_orden(cmd.orden_id, "Registro completado.", operacion)


class RegistrarIncidenciaHandler(_HandlerDeOrden):
    """US-11 Registro de incidencias durante el servicio (no cambia el estado)."""

    def handle(self, cmd: RegistrarIncidenciaCommand) -> Resultado:
        return self._sobre_orden(cmd.orden_id, "Incidencia registrada.",
                                 lambda orden, uow: orden.registrar_incidencia(cmd.tipo, cmd.descripcion,
                                                                               cmd.evidencia))


# ============================ Queries (lado de lectura) ============================
class _Consulta:
    def __init__(self, consulta: IConsultaDeServicios):
        self._consulta = consulta


class ConsultarEstadoDelServicioHandler(_Consulta):
    """CU-05 Consultar estado del servicio (Query, sin cargar el agregado; US-14)."""

    def handle(self, query: ConsultarEstadoDelServicioQuery) -> EstadoDelServicioDTO:
        return self._consulta.estado_del_servicio(query.orden_id)


class ConsultarIndicadoresHandler(_Consulta):
    """Query de indicadores históricos para Operaciones (US-15)."""

    def handle(self, query: ConsultarIndicadoresQuery) -> IndicadoresDTO:
        return self._consulta.indicadores(query.desde, query.hasta)


class ConsultarCotizacionHandler(_Consulta):
    def handle(self, query: ConsultarCotizacionQuery) -> CotizacionDTO:
        return self._consulta.cotizacion(query.cotizacion_id)


class ListarOrdenesHandler(_Consulta):
    def handle(self, query: ListarOrdenesQuery) -> list[OrdenResumenDTO]:
        return self._consulta.ordenes(query.estado, query.limite)


class ConsultarClienteHandler(_Consulta):
    def handle(self, query: ConsultarClienteQuery) -> ClienteDTO:
        return self._consulta.cliente(query.cliente_id)


class ConsultarUnidadHandler(_Consulta):
    def handle(self, query: ConsultarUnidadQuery) -> UnidadDTO:
        return self._consulta.unidad(query.unidad_id)


class ConsultarOperadorHandler(_Consulta):
    def handle(self, query: ConsultarOperadorQuery) -> OperadorDTO:
        return self._consulta.operador(query.operador_id)
