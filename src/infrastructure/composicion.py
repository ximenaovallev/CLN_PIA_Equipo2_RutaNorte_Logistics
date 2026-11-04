"""Raíz de composición: único lugar donde se eligen las implementaciones concretas (DIP).

`construir_aplicacion(config)` arma los casos de uso sobre PostgreSQL/SQLite (DATABASE_URL);
`construir_aplicacion_en_memoria()` arma los mismos casos de uso sobre el almacén en memoria.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from application import handlers as h
from application.puertos import IConsultaDeServicios, IPublicadorDeEventos, IUnitOfWork
from domain.especificaciones import asignacion_permitida
from domain.servicios import AsignadorDeRecursos, AutoridadDeCancelacion
from domain.valores import PoliticaDeConservacion

from .configuracion import Configuracion
from .en_memoria import (
    AlmacenEnMemoria, EnMemoriaConsultaDeServicios, EnMemoriaUnitOfWork, PublicadorDeEventosEnMemoria,
)


@dataclass
class Aplicacion:
    """Conjunto de casos de uso (handlers) ya cableados con sus puertos."""
    registrar_cliente: h.RegistrarClienteHandler
    registrar_unidad: h.RegistrarUnidadHandler
    registrar_operador: h.RegistrarOperadorHandler
    cambiar_disponibilidad: h.CambiarDisponibilidadDeOperadorHandler
    solicitar_cotizacion: h.SolicitarCotizacionHandler
    elaborar_cotizacion: h.ElaborarCotizacionHandler
    modificar_cotizacion: h.ModificarCotizacionHandler
    responder_cotizacion: h.ResponderCotizacionHandler
    generar_orden: h.GenerarOrdenDeServicioHandler
    autorizar_alto_valor: h.AutorizarCargaDeAltoValorHandler
    cancelar_servicio: h.CancelarServicioHandler
    solicitar_cambio: h.SolicitarCambioOperativoHandler
    revisar_cambio: h.RevisarCambioOperativoHandler
    asignar_recursos: h.AsignarRecursosHandler
    registrar_recepcion: h.RegistrarRecepcionHandler
    iniciar_traslado: h.IniciarTrasladoHandler
    registrar_llegada: h.RegistrarLlegadaHandler
    registrar_entrega: h.RegistrarEntregaHandler
    registrar_incidencia: h.RegistrarIncidenciaHandler
    consultar_estado: h.ConsultarEstadoDelServicioHandler
    consultar_indicadores: h.ConsultarIndicadoresHandler
    consultar_cotizacion: h.ConsultarCotizacionHandler
    listar_ordenes: h.ListarOrdenesHandler
    consultar_cliente: h.ConsultarClienteHandler
    consultar_unidad: h.ConsultarUnidadHandler
    consultar_operador: h.ConsultarOperadorHandler
    politica_de_conservacion: PoliticaDeConservacion
    # Solo para pruebas y diagnóstico:
    publicador: IPublicadorDeEventos
    uow: IUnitOfWork
    almacen: Any = None  # AlmacenEnMemoria cuando el backend es memoria
    motor: Any = None    # Engine cuando el backend es SQL


def _ensamblar(uow: IUnitOfWork, pub: IPublicadorDeEventos, consulta: IConsultaDeServicios,
               config: Configuracion, **extra: Any) -> Aplicacion:
    asignador = AsignadorDeRecursos(asignacion_permitida(config.peso_maximo_kg, config.volumen_maximo_m3))
    autoridad = AutoridadDeCancelacion(config.roles_que_cancelan)
    return Aplicacion(
        registrar_cliente=h.RegistrarClienteHandler(uow, pub),
        registrar_unidad=h.RegistrarUnidadHandler(uow, pub),
        registrar_operador=h.RegistrarOperadorHandler(uow, pub),
        cambiar_disponibilidad=h.CambiarDisponibilidadDeOperadorHandler(uow, pub),
        solicitar_cotizacion=h.SolicitarCotizacionHandler(uow, pub),
        elaborar_cotizacion=h.ElaborarCotizacionHandler(uow, pub),
        modificar_cotizacion=h.ModificarCotizacionHandler(uow, pub),
        responder_cotizacion=h.ResponderCotizacionHandler(uow, pub),
        generar_orden=h.GenerarOrdenDeServicioHandler(uow, pub),
        autorizar_alto_valor=h.AutorizarCargaDeAltoValorHandler(uow, pub),
        cancelar_servicio=h.CancelarServicioHandler(uow, pub, autoridad),
        solicitar_cambio=h.SolicitarCambioOperativoHandler(uow, pub),
        revisar_cambio=h.RevisarCambioOperativoHandler(uow, pub),
        asignar_recursos=h.AsignarRecursosHandler(uow, pub, asignador),
        registrar_recepcion=h.RegistrarRecepcionHandler(uow, pub),
        iniciar_traslado=h.IniciarTrasladoHandler(uow, pub),
        registrar_llegada=h.RegistrarLlegadaHandler(uow, pub),
        registrar_entrega=h.RegistrarEntregaHandler(uow, pub),
        registrar_incidencia=h.RegistrarIncidenciaHandler(uow, pub),
        consultar_estado=h.ConsultarEstadoDelServicioHandler(consulta),
        consultar_indicadores=h.ConsultarIndicadoresHandler(consulta),
        consultar_cotizacion=h.ConsultarCotizacionHandler(consulta),
        listar_ordenes=h.ListarOrdenesHandler(consulta),
        consultar_cliente=h.ConsultarClienteHandler(consulta),
        consultar_unidad=h.ConsultarUnidadHandler(consulta),
        consultar_operador=h.ConsultarOperadorHandler(consulta),
        politica_de_conservacion=PoliticaDeConservacion(config.dias_de_conservacion),
        publicador=pub,
        uow=uow,
        **extra,
    )


def construir_aplicacion_en_memoria(config: Configuracion | None = None) -> Aplicacion:
    config = config or Configuracion.desde_entorno()
    almacen = AlmacenEnMemoria()
    return _ensamblar(EnMemoriaUnitOfWork(almacen), PublicadorDeEventosEnMemoria(),
                      EnMemoriaConsultaDeServicios(almacen), config, almacen=almacen)


def construir_aplicacion_sql(config: Configuracion | None = None, crear_esquema: bool = True) -> Aplicacion:
    from .sql.consulta import SqlConsultaDeServicios
    from .sql.motor import crear_fabrica_de_sesiones, crear_motor, crear_tablas
    from .sql.publicador import SqlPublicadorDeEventos
    from .sql.unit_of_work import SqlUnitOfWork

    config = config or Configuracion.desde_entorno()
    motor = crear_motor(config.database_url)
    if crear_esquema:
        crear_tablas(motor)
    fabrica = crear_fabrica_de_sesiones(motor)
    return _ensamblar(SqlUnitOfWork(fabrica), SqlPublicadorDeEventos(fabrica),
                      SqlConsultaDeServicios(fabrica), config, motor=motor)


def construir_aplicacion(config: Configuracion | None = None) -> Aplicacion:
    """Punto de entrada de producción: backend SQL según DATABASE_URL."""
    return construir_aplicacion_sql(config)
