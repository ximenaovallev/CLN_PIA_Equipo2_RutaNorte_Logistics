"""Endpoints REST. Cada ruta traduce JSON → Command/Query, invoca el handler y traduce el Resultado → HTTP."""
from __future__ import annotations

from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from application import comandos as c
from application.dto import Resultado
from domain.valores import EventoAsociado
from infrastructure.composicion import Aplicacion

from . import esquemas as e
from .errores import codigo_http

_ERRORES = {
    400: {"model": e.ErrorOut, "description": "Datos inválidos o mal formados"},
    404: {"model": e.ErrorOut, "description": "El recurso no existe"},
    409: {"model": e.ErrorOut, "description": "Conflicto con el estado actual"},
    422: {"model": e.ErrorOut, "description": "Regla de negocio no cumplida"},
}


def _app(request: Request) -> Aplicacion:
    return request.app.state.aplicacion


def _responder(r: Resultado, exito: int = 200) -> JSONResponse:
    if r.exito:
        return JSONResponse(status_code=exito, content={"mensaje": r.mensaje_de_negocio, "datos": r.datos})
    return JSONResponse(status_code=codigo_http(r.codigo_de_error),
                        content={"codigo": r.codigo_de_error or "ReglaDeNegocio", "mensaje": r.mensaje_de_negocio})


def _consulta(operacion):
    """Las consultas lanzan errores de dominio (p. ej. no encontrado); se traducen igual que los comandos."""
    from domain.comunes import ErrorDeDominio
    try:
        return operacion()
    except ErrorDeDominio as error:
        raise HTTPException(status_code=codigo_http(type(error).__name__),
                            detail={"codigo": type(error).__name__, "mensaje": str(error)}) from None


def _dto(valor):
    return asdict(valor)


router = APIRouter(responses=_ERRORES)

# ------------------------------------ Catálogos ------------------------------------
@router.post("/clientes", status_code=201, tags=["Catálogos"], summary="Registrar cliente",
             response_model=e.OperacionOut)
def registrar_cliente(cuerpo: e.ClienteIn, request: Request):
    return _responder(_app(request).registrar_cliente.handle(c.RegistrarClienteCommand(**cuerpo.model_dump())), 201)


@router.get("/clientes/{cliente_id}", tags=["Catálogos"], summary="Consultar cliente")
def consultar_cliente(cliente_id: str, request: Request):
    return _consulta(lambda: _dto(_app(request).consultar_cliente.handle(c.ConsultarClienteQuery(cliente_id))))


@router.post("/unidades", status_code=201, tags=["Catálogos"], summary="Registrar unidad de transporte",
             response_model=e.OperacionOut)
def registrar_unidad(cuerpo: e.UnidadIn, request: Request):
    return _responder(_app(request).registrar_unidad.handle(c.RegistrarUnidadCommand(**cuerpo.model_dump())), 201)


@router.get("/unidades/{unidad_id}", tags=["Catálogos"], summary="Consultar unidad")
def consultar_unidad(unidad_id: str, request: Request):
    return _consulta(lambda: _dto(_app(request).consultar_unidad.handle(c.ConsultarUnidadQuery(unidad_id))))


@router.post("/operadores", status_code=201, tags=["Catálogos"], summary="Registrar operador",
             response_model=e.OperacionOut)
def registrar_operador(cuerpo: e.OperadorIn, request: Request):
    return _responder(_app(request).registrar_operador.handle(c.RegistrarOperadorCommand(**cuerpo.model_dump())), 201)


@router.get("/operadores/{operador_id}", tags=["Catálogos"], summary="Consultar operador")
def consultar_operador(operador_id: str, request: Request):
    return _consulta(lambda: _dto(_app(request).consultar_operador.handle(c.ConsultarOperadorQuery(operador_id))))


@router.put("/operadores/{operador_id}/disponibilidad", tags=["Catálogos"], summary="Cambiar disponibilidad",
            response_model=e.OperacionOut)
def cambiar_disponibilidad(operador_id: str, cuerpo: e.DisponibilidadIn, request: Request):
    return _responder(_app(request).cambiar_disponibilidad.handle(
        c.CambiarDisponibilidadDeOperadorCommand(operador_id, cuerpo.disponible)))


# ------------------------------------ Cotizaciones ------------------------------------
@router.post("/cotizaciones", status_code=201, tags=["Cotizaciones"], summary="Solicitar cotización (US-01)",
             response_model=e.OperacionOut)
def solicitar_cotizacion(cuerpo: e.CotizacionIn, request: Request):
    cmd = c.SolicitarCotizacionCommand(cuerpo.cliente_id, cuerpo.solicitud.a_dominio())
    return _responder(_app(request).solicitar_cotizacion.handle(cmd), 201)


@router.get("/cotizaciones/{cotizacion_id}", tags=["Cotizaciones"], summary="Consultar cotización")
def consultar_cotizacion(cotizacion_id: str, request: Request):
    return _consulta(lambda: _app(request).consultar_cotizacion.handle(c.ConsultarCotizacionQuery(cotizacion_id)))


@router.put("/cotizaciones/{cotizacion_id}/solicitud", tags=["Cotizaciones"],
            summary="Modificar la solicitud mientras está en proceso (US-03)", response_model=e.OperacionOut)
def modificar_cotizacion(cotizacion_id: str, cuerpo: e.SolicitudIn, request: Request):
    return _responder(_app(request).modificar_cotizacion.handle(
        c.ModificarCotizacionCommand(cotizacion_id, cuerpo.a_dominio())))


@router.put("/cotizaciones/{cotizacion_id}/importe", tags=["Cotizaciones"],
            summary="Elaborar la cotización con su importe (US-02)", response_model=e.OperacionOut)
def elaborar_cotizacion(cotizacion_id: str, cuerpo: e.ImporteIn, request: Request):
    return _responder(_app(request).elaborar_cotizacion.handle(
        c.ElaborarCotizacionCommand(cotizacion_id, cuerpo.importe_mxn)))


@router.post("/cotizaciones/{cotizacion_id}/respuesta", tags=["Cotizaciones"],
             summary="El cliente acepta o rechaza la cotización (US-17)", response_model=e.OperacionOut)
def responder_cotizacion(cotizacion_id: str, cuerpo: e.RespuestaIn, request: Request):
    return _responder(_app(request).responder_cotizacion.handle(
        c.ResponderCotizacionCommand(cotizacion_id, c.RespuestaDelCliente(cuerpo.respuesta))))


# ------------------------------------ Órdenes de servicio ------------------------------------
@router.post("/ordenes", status_code=201, tags=["Órdenes de servicio"],
             summary="Generar orden desde una cotización aceptada (US-05/06)", response_model=e.OperacionOut)
def generar_orden(cuerpo: e.OrdenIn, request: Request):
    return _responder(_app(request).generar_orden.handle(c.GenerarOrdenDeServicioCommand(**cuerpo.model_dump())), 201)


@router.get("/ordenes", tags=["Órdenes de servicio"], summary="Listar órdenes (filtro opcional por estado)")
def listar_ordenes(request: Request, estado: str | None = None, limite: int = Query(50, ge=1, le=500)):
    return [_dto(o) for o in _consulta(lambda: _app(request).listar_ordenes.handle(c.ListarOrdenesQuery(estado, limite)))]


@router.get("/ordenes/{orden_id}/estado", tags=["Órdenes de servicio"],
            summary="Consultar estado, historial e incidencias (US-14)")
def consultar_estado(orden_id: str, request: Request):
    return _consulta(lambda: _dto(_app(request).consultar_estado.handle(c.ConsultarEstadoDelServicioQuery(orden_id))))


@router.post("/ordenes/{orden_id}/asignacion", tags=["Órdenes de servicio"],
             summary="Asignar o reasignar unidad y operador (US-07/08)", response_model=e.OperacionOut)
def asignar_recursos(orden_id: str, cuerpo: e.AsignacionIn, request: Request):
    return _responder(_app(request).asignar_recursos.handle(c.AsignarRecursosCommand(orden_id, **cuerpo.model_dump())))


@router.post("/ordenes/{orden_id}/autorizacion-alto-valor", tags=["Órdenes de servicio"],
             summary="Autorizar carga de alto valor (S-02 / US-16)", response_model=e.OperacionOut)
def autorizar_alto_valor(orden_id: str, cuerpo: e.AutorizacionAltoValorIn, request: Request):
    return _responder(_app(request).autorizar_alto_valor.handle(
        c.AutorizarCargaDeAltoValorCommand(orden_id, cuerpo.autorizado_por)))


@router.post("/ordenes/{orden_id}/recepcion", tags=["Órdenes de servicio"],
             summary="Registrar recepción de la mercancía con evidencia (US-09)", response_model=e.OperacionOut)
def registrar_recepcion(orden_id: str, cuerpo: e.RecepcionIn, request: Request):
    return _responder(_app(request).registrar_recepcion.handle(
        c.RegistrarRecepcionCommand(orden_id, cuerpo.evidencia.a_dominio(EventoAsociado.RECEPCION))))


@router.post("/ordenes/{orden_id}/traslado", tags=["Órdenes de servicio"],
             summary="Iniciar traslado", response_model=e.OperacionOut)
def iniciar_traslado(orden_id: str, request: Request):
    return _responder(_app(request).iniciar_traslado.handle(c.IniciarTrasladoCommand(orden_id)))


@router.post("/ordenes/{orden_id}/llegada", tags=["Órdenes de servicio"],
             summary="Registrar llegada a destino", response_model=e.OperacionOut)
def registrar_llegada(orden_id: str, request: Request):
    return _responder(_app(request).registrar_llegada.handle(c.RegistrarLlegadaCommand(orden_id)))


@router.post("/ordenes/{orden_id}/entrega", tags=["Órdenes de servicio"],
             summary="Registrar entrega o incidencia en destino (US-11/12/13)", response_model=e.OperacionOut)
def registrar_entrega(orden_id: str, cuerpo: e.EntregaIn, request: Request):
    evento = EventoAsociado.ENTREGA if cuerpo.incidencia is None else EventoAsociado.INCIDENCIA
    return _responder(_app(request).registrar_entrega.handle(c.RegistrarEntregaCommand(
        orden_id, cuerpo.destinatario_de_dominio(), cuerpo.evidencia.a_dominio(evento),
        cuerpo.incidencia, cuerpo.descripcion_incidencia)))


@router.post("/ordenes/{orden_id}/incidencias", tags=["Órdenes de servicio"],
             summary="Registrar incidencia durante el servicio (no cambia el estado)", response_model=e.OperacionOut)
def registrar_incidencia(orden_id: str, cuerpo: e.IncidenciaIn, request: Request):
    evidencia = cuerpo.evidencia.a_dominio(EventoAsociado.INCIDENCIA) if cuerpo.evidencia else None
    return _responder(_app(request).registrar_incidencia.handle(
        c.RegistrarIncidenciaCommand(orden_id, cuerpo.tipo, cuerpo.descripcion, evidencia)))


@router.post("/ordenes/{orden_id}/cancelacion", tags=["Órdenes de servicio"],
             summary="Cancelar el servicio (S-04)", response_model=e.OperacionOut)
def cancelar_servicio(orden_id: str, cuerpo: e.CancelacionIn, request: Request):
    return _responder(_app(request).cancelar_servicio.handle(c.CancelarServicioCommand(orden_id, **cuerpo.model_dump())))


@router.post("/ordenes/{orden_id}/cambios-operativos", status_code=201, tags=["Órdenes de servicio"],
             summary="Solicitar un cambio operativo posterior a la orden (US-04)", response_model=e.OperacionOut)
def solicitar_cambio(orden_id: str, cuerpo: e.CambioOperativoIn, request: Request):
    return _responder(_app(request).solicitar_cambio.handle(
        c.SolicitarCambioOperativoCommand(orden_id, **cuerpo.model_dump())), 201)


@router.put("/ordenes/{orden_id}/cambios-operativos/revision", tags=["Órdenes de servicio"],
            summary="Revisar el cambio operativo pendiente", response_model=e.OperacionOut)
def revisar_cambio(orden_id: str, cuerpo: e.RevisionDeCambioIn, request: Request):
    return _responder(_app(request).revisar_cambio.handle(
        c.RevisarCambioOperativoCommand(orden_id, **cuerpo.model_dump())))


# ------------------------------------ Indicadores ------------------------------------
@router.get("/indicadores", tags=["Indicadores"], summary="Indicadores operativos del periodo (US-15)")
def indicadores(request: Request, desde: date, hasta: date):
    if desde > hasta:
        raise HTTPException(status_code=400, detail={"codigo": "DatosInvalidos",
                                                     "mensaje": "'desde' no puede ser posterior a 'hasta'."})
    return _consulta(lambda: _dto(_app(request).consultar_indicadores.handle(c.ConsultarIndicadoresQuery(desde, hasta))))
