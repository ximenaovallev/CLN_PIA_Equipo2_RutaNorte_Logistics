"""Endpoints REST. Cada ruta traduce JSON → Command/Query, invoca el handler y traduce el Resultado → HTTP.

Los textos que ve la persona usuaria (Swagger y respuestas) están en lenguaje sencillo (`lenguaje.py`)."""
from __future__ import annotations

from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse

from application import comandos as c
from application.dto import Resultado
from domain.valores import EventoAsociado
from infrastructure.composicion import Aplicacion

from . import esquemas as e
from . import lenguaje
from .errores import codigo_http

T_REGISTROS = "1. Registros básicos"
T_COTIZACIONES = "2. Cotizaciones"
T_ORDENES = "3. Órdenes de servicio"
T_INDICADORES = "4. Indicadores"
T_SISTEMA = "5. Estado del sistema"

ETIQUETAS = [
    {"name": T_REGISTROS, "description": "**Empiece aquí.** Dé de alta a los clientes, los camiones (unidades) y los operadores (conductores). "
     "Cada uno lleva un código que usted inventa, por ejemplo `CLI-001`."},
    {"name": T_COTIZACIONES, "description": "El cliente pide un precio, Ventas lo calcula y el cliente decide si lo acepta. "
     "Al pedir la cotización recibirá un **número de cotización**: guárdelo."},
    {"name": T_ORDENES, "description": "Cuando el cliente acepta, se crea la orden de servicio y se sigue el viaje paso a paso: "
     "asignar camión y operador, recoger, viajar, llegar y entregar. Aquí también se registran problemas, cambios y cancelaciones."},
    {"name": T_INDICADORES, "description": "Cifras para saber cómo vamos: entregas, retrasos y problemas en un periodo."},
    {"name": T_SISTEMA, "description": "Sirve para comprobar que el sistema está funcionando."},
]

_ERRORES = {
    400: {"model": e.ErrorOut, "description": "**Faltan datos o están mal escritos.** El mensaje dice exactamente cuál dato corregir."},
    404: {"model": e.ErrorOut, "description": "**No se encontró.** El código que escribió no existe todavía o tiene un error de escritura."},
    409: {"model": e.ErrorOut, "description": "**Ese paso no se puede hacer ahora.** Pasa cuando el código ya existe o cuando se intenta un paso fuera de orden."},
    422: {"model": e.ErrorOut, "description": "**El negocio no lo permite todavía.** Por ejemplo, un camión sin capacidad suficiente o una carga de alto valor sin autorizar."},
}

ID_COTIZACION = Path(description="Número de cotización que recibió al pedirla", examples=["PEGUE-AQUÍ-EL-NÚMERO-DE-COTIZACIÓN"])
ID_ORDEN = Path(description="Número de orden que recibió al crearla", examples=["PEGUE-AQUÍ-EL-NÚMERO-DE-ORDEN"])


def _app(request: Request) -> Aplicacion:
    return request.app.state.aplicacion


def _responder(r: Resultado, exito: int = 200, operacion: str = "") -> JSONResponse:
    if r.exito:
        mensaje, que_sigue = lenguaje.exito(operacion, r.datos)
        return JSONResponse(status_code=exito, content={"mensaje": mensaje, "que_sigue": que_sigue, "datos": r.datos})
    mensaje, que_hacer = lenguaje.error(r.codigo_de_error, r.mensaje_de_negocio)
    return JSONResponse(status_code=codigo_http(r.codigo_de_error),
                        content={"codigo": r.codigo_de_error or "ReglaDeNegocio", "mensaje": mensaje, "que_hacer": que_hacer})


def _consulta(operacion):
    """Las consultas lanzan errores de dominio (p. ej. no encontrado); se traducen igual que los comandos."""
    from domain.comunes import ErrorDeDominio
    try:
        return operacion()
    except ErrorDeDominio as error:
        nombre = type(error).__name__
        mensaje, que_hacer = lenguaje.error(nombre, str(error))
        raise HTTPException(status_code=codigo_http(nombre),
                            detail={"codigo": nombre, "mensaje": mensaje, "que_hacer": que_hacer}) from None


def _dto(valor):
    return asdict(valor)


router = APIRouter(responses=_ERRORES)

OK = "Todo salió bien."
CREADO = "Todo salió bien y quedó registrado."


# ------------------------------------ 1. Registros básicos ------------------------------------
@router.post("/clientes", status_code=201, tags=[T_REGISTROS], summary="Registrar un cliente",
             description="Da de alta a un cliente.\n\n**Cuándo usarla:** es lo primero que se hace, antes de pedir una cotización.\n\n"
                         "**Qué necesita:** un código que usted inventa (no se puede repetir) y el nombre del cliente.",
             response_description=CREADO, response_model=e.OperacionOut)
def registrar_cliente(cuerpo: e.ClienteIn, request: Request):
    return _responder(_app(request).registrar_cliente.handle(c.RegistrarClienteCommand(**cuerpo.model_dump())), 201,
                      "registrar_cliente")


@router.get("/clientes/{cliente_id}", tags=[T_REGISTROS], summary="Consultar un cliente",
            description="Muestra los datos de un cliente ya registrado.", response_description=OK)
def consultar_cliente(request: Request, cliente_id: str = Path(description="Código del cliente", examples=["CLI-001"])):
    return _consulta(lambda: _dto(_app(request).consultar_cliente.handle(c.ConsultarClienteQuery(cliente_id))))


@router.post("/unidades", status_code=201, tags=[T_REGISTROS], summary="Registrar una unidad de transporte (camión)",
             description="Da de alta un camión o vehículo de carga con lo que puede cargar.\n\n"
                         "**Para qué sirve:** al asignar un camión a una orden, el sistema comprueba que la carga le quepa.",
             response_description=CREADO, response_model=e.OperacionOut)
def registrar_unidad(cuerpo: e.UnidadIn, request: Request):
    return _responder(_app(request).registrar_unidad.handle(c.RegistrarUnidadCommand(**cuerpo.model_dump())), 201,
                      "registrar_unidad")


@router.get("/unidades/{unidad_id}", tags=[T_REGISTROS], summary="Consultar una unidad de transporte",
            description="Muestra los datos de un camión ya registrado.", response_description=OK)
def consultar_unidad(request: Request, unidad_id: str = Path(description="Código de la unidad", examples=["UNI-001"])):
    return _consulta(lambda: _dto(_app(request).consultar_unidad.handle(c.ConsultarUnidadQuery(unidad_id))))


@router.post("/operadores", status_code=201, tags=[T_REGISTROS], summary="Registrar un operador (conductor)",
             description="Da de alta a la persona que conduce.", response_description=CREADO, response_model=e.OperacionOut)
def registrar_operador(cuerpo: e.OperadorIn, request: Request):
    return _responder(_app(request).registrar_operador.handle(c.RegistrarOperadorCommand(**cuerpo.model_dump())), 201,
                      "registrar_operador")


@router.get("/operadores/{operador_id}", tags=[T_REGISTROS], summary="Consultar un operador",
            description="Muestra los datos de un operador ya registrado y si está disponible.", response_description=OK)
def consultar_operador(request: Request, operador_id: str = Path(description="Código del operador", examples=["OPE-001"])):
    return _consulta(lambda: _dto(_app(request).consultar_operador.handle(c.ConsultarOperadorQuery(operador_id))))


@router.put("/operadores/{operador_id}/disponibilidad", tags=[T_REGISTROS], summary="Marcar si un operador está disponible",
            description="Cambia si el operador puede recibir trabajo. Un operador **no disponible** no puede asignarse a ninguna orden.",
            response_description=OK, response_model=e.OperacionOut)
def cambiar_disponibilidad(cuerpo: e.DisponibilidadIn, request: Request,
                           operador_id: str = Path(description="Código del operador", examples=["OPE-001"])):
    return _responder(_app(request).cambiar_disponibilidad.handle(
        c.CambiarDisponibilidadDeOperadorCommand(operador_id, cuerpo.disponible)), operacion="cambiar_disponibilidad")


# ------------------------------------ 2. Cotizaciones ------------------------------------
@router.post("/cotizaciones", status_code=201, tags=[T_COTIZACIONES], summary="Pedir una cotización",
             description="El cliente pide que le digan cuánto costaría transportar su mercancía.\n\n"
                         "**Qué necesita:** el código del cliente (ya registrado), de dónde a dónde va la carga, qué es y para cuándo.\n\n"
                         "**Qué recibe:** un **número de cotización**. Guárdelo: lo usará en los siguientes pasos.\n\n"
                         "*Referencia técnica: historia US-01.*",
             response_description=CREADO, response_model=e.OperacionOut)
def solicitar_cotizacion(cuerpo: e.CotizacionIn, request: Request):
    cmd = c.SolicitarCotizacionCommand(cuerpo.cliente_id, cuerpo.solicitud.a_dominio())
    return _responder(_app(request).solicitar_cotizacion.handle(cmd), 201, "solicitar_cotizacion")


@router.get("/cotizaciones/{cotizacion_id}", tags=[T_COTIZACIONES], summary="Consultar una cotización",
            description="Muestra los datos de la cotización, su precio (si ya lo tiene) y en qué situación está.", response_description=OK)
def consultar_cotizacion(request: Request, cotizacion_id: str = ID_COTIZACION):
    return _consulta(lambda: _app(request).consultar_cotizacion.handle(c.ConsultarCotizacionQuery(cotizacion_id)))


@router.put("/cotizaciones/{cotizacion_id}/solicitud", tags=[T_COTIZACIONES],
            summary="Corregir los datos de la solicitud",
            description="Cambia los datos que el cliente pidió (por ejemplo, la fecha o el peso).\n\n"
                        "**Importante:** solo se puede mientras la cotización está *en proceso* (el cliente aún no la acepta). "
                        "Después de corregirla, Ventas debe volver a poner el precio.\n\n*Referencia técnica: historia US-03.*",
            response_description=OK, response_model=e.OperacionOut)
def modificar_cotizacion(cuerpo: e.SolicitudIn, request: Request, cotizacion_id: str = ID_COTIZACION):
    return _responder(_app(request).modificar_cotizacion.handle(
        c.ModificarCotizacionCommand(cotizacion_id, cuerpo.a_dominio())), operacion="modificar_cotizacion")


@router.put("/cotizaciones/{cotizacion_id}/importe", tags=[T_COTIZACIONES], summary="Poner el precio a la cotización",
            description="Ventas escribe cuánto costará el servicio, en pesos mexicanos.\n\n"
                        "**Después de esto** el cliente ya puede aceptar o rechazar.\n\n*Referencia técnica: historia US-02.*",
            response_description=OK, response_model=e.OperacionOut)
def elaborar_cotizacion(cuerpo: e.ImporteIn, request: Request, cotizacion_id: str = ID_COTIZACION):
    return _responder(_app(request).elaborar_cotizacion.handle(
        c.ElaborarCotizacionCommand(cotizacion_id, cuerpo.importe_mxn)), operacion="elaborar_cotizacion")


@router.post("/cotizaciones/{cotizacion_id}/respuesta", tags=[T_COTIZACIONES],
             summary="El cliente acepta o rechaza la cotización",
             description="Registra la decisión del cliente: **ACEPTA** o **RECHAZA**.\n\n"
                         "**Antes de usarla:** Ventas debe haber puesto el precio. Si no, el sistema avisará que todavía no se puede responder.\n\n"
                         "*Referencia técnica: historia US-17.*",
             response_description=OK, response_model=e.OperacionOut)
def responder_cotizacion(cuerpo: e.RespuestaIn, request: Request, cotizacion_id: str = ID_COTIZACION):
    return _responder(_app(request).responder_cotizacion.handle(
        c.ResponderCotizacionCommand(cotizacion_id, c.RespuestaDelCliente(cuerpo.respuesta))), operacion="responder_cotizacion")


# ------------------------------------ 3. Órdenes de servicio ------------------------------------
@router.post("/ordenes", status_code=201, tags=[T_ORDENES], summary="Crear la orden de servicio",
             description="Convierte una cotización **aceptada** en una orden de servicio: el trabajo que se va a realizar.\n\n"
                         "**Qué recibe:** un **número de orden**. Guárdelo: lo usará en todos los pasos del viaje.\n\n"
                         "*Referencia técnica: historias US-05 y US-06.*",
             response_description=CREADO, response_model=e.OperacionOut)
def generar_orden(cuerpo: e.OrdenIn, request: Request):
    return _responder(_app(request).generar_orden.handle(c.GenerarOrdenDeServicioCommand(**cuerpo.model_dump())), 201,
                      "generar_orden")


@router.get("/ordenes", tags=[T_ORDENES], summary="Ver la lista de órdenes",
            description="Lista las órdenes de servicio. Puede filtrarlas por situación (por ejemplo `EN_TRANSITO`).",
            response_description=OK)
def listar_ordenes(request: Request,
                   estado: str | None = Query(None, description="Opcional. Muestra solo las órdenes en esta situación. Ejemplo: EN_TRANSITO", examples=["EN_TRANSITO"]),
                   limite: int = Query(50, ge=1, le=500, description="Cuántas órdenes mostrar como máximo (de 1 a 500)", examples=[50])):
    return [_dto(o) for o in _consulta(lambda: _app(request).listar_ordenes.handle(c.ListarOrdenesQuery(estado, limite)))]


@router.get("/ordenes/{orden_id}/estado", tags=[T_ORDENES], summary="Consultar el estado de una orden",
            description="Dice en qué paso va el servicio, qué ha pasado hasta ahora (historial), si hubo retrasos o problemas "
                        "y qué se puede hacer a continuación. Pensada para **Atención al Cliente**.\n\n*Referencia técnica: historia US-14.*",
            response_description=OK)
def consultar_estado(request: Request, orden_id: str = ID_ORDEN):
    datos = _consulta(lambda: _dto(_app(request).consultar_estado.handle(c.ConsultarEstadoDelServicioQuery(orden_id))))
    datos["resumen"] = f"El servicio está {lenguaje.estado_en_palabras(datos['estado_actual'])}."
    return datos


@router.post("/ordenes/{orden_id}/asignacion", tags=[T_ORDENES], summary="Asignar camión y operador",
             description="Operaciones elige qué camión y qué operador harán el servicio.\n\n"
                         "**El sistema revisa que:** al camión le quepa la carga y que el operador esté disponible. "
                         "Si la carga es de alto valor, antes debe estar autorizada.\n\nTambién sirve para **cambiar** de operador si el primero no puede.\n\n"
                         "*Referencia técnica: historias US-07 y US-08.*",
             response_description=OK, response_model=e.OperacionOut)
def asignar_recursos(cuerpo: e.AsignacionIn, request: Request, orden_id: str = ID_ORDEN):
    return _responder(_app(request).asignar_recursos.handle(c.AsignarRecursosCommand(orden_id, **cuerpo.model_dump())),
                      operacion="asignar_recursos")


@router.post("/ordenes/{orden_id}/autorizacion-alto-valor", tags=[T_ORDENES], summary="Autorizar una carga de alto valor",
             description="Las cargas de mucho valor necesitan permiso de Operaciones antes de asignarles camión y operador. "
                         "Aquí se registra quién lo autoriza.\n\n*Referencia técnica: historia US-16.*",
             response_description=OK, response_model=e.OperacionOut)
def autorizar_alto_valor(cuerpo: e.AutorizacionAltoValorIn, request: Request, orden_id: str = ID_ORDEN):
    return _responder(_app(request).autorizar_alto_valor.handle(
        c.AutorizarCargaDeAltoValorCommand(orden_id, cuerpo.autorizado_por)), operacion="autorizar_alto_valor")


@router.post("/ordenes/{orden_id}/recepcion", tags=[T_ORDENES], summary="Registrar que se recogió la mercancía",
             description="El operador confirma que recibió la mercancía y adjunta una foto o documento como comprobante.\n\n"
                         "*Referencia técnica: historia US-09.*",
             response_description=OK, response_model=e.OperacionOut)
def registrar_recepcion(cuerpo: e.RecepcionIn, request: Request, orden_id: str = ID_ORDEN):
    return _responder(_app(request).registrar_recepcion.handle(
        c.RegistrarRecepcionCommand(orden_id, cuerpo.evidencia.a_dominio(EventoAsociado.RECEPCION))),
        operacion="registrar_recepcion")


@router.post("/ordenes/{orden_id}/traslado", tags=[T_ORDENES], summary="Registrar que salió el camión",
             description="Indica que el viaje comenzó. No necesita datos: solo escriba el número de orden.",
             response_description=OK, response_model=e.OperacionOut)
def iniciar_traslado(request: Request, orden_id: str = ID_ORDEN):
    return _responder(_app(request).iniciar_traslado.handle(c.IniciarTrasladoCommand(orden_id)), operacion="iniciar_traslado")


@router.post("/ordenes/{orden_id}/llegada", tags=[T_ORDENES], summary="Registrar que el camión llegó al destino",
             description="Indica que la unidad ya llegó al lugar de entrega. No necesita datos: solo escriba el número de orden.",
             response_description=OK, response_model=e.OperacionOut)
def registrar_llegada(request: Request, orden_id: str = ID_ORDEN):
    return _responder(_app(request).registrar_llegada.handle(c.RegistrarLlegadaCommand(orden_id)), operacion="registrar_llegada")


@router.post("/ordenes/{orden_id}/entrega", tags=[T_ORDENES], summary="Registrar la entrega (o el problema para entregar)",
             description="Cierra el servicio: quién recibió la mercancía y una foto o documento como comprobante.\n\n"
                         "**Si no se pudo entregar** (nadie recibió, dirección incorrecta…), indique el motivo en *incidencia*: "
                         "el servicio **no** se marca como entregado y Operaciones lo atiende.\n\n"
                         "*Referencia técnica: historias US-11, US-12 y US-13.*",
             response_description=OK, response_model=e.OperacionOut)
def registrar_entrega(cuerpo: e.EntregaIn, request: Request, orden_id: str = ID_ORDEN):
    evento = EventoAsociado.ENTREGA if cuerpo.incidencia is None else EventoAsociado.INCIDENCIA
    return _responder(_app(request).registrar_entrega.handle(c.RegistrarEntregaCommand(
        orden_id, cuerpo.destinatario_de_dominio(), cuerpo.evidencia.a_dominio(evento),
        cuerpo.incidencia, cuerpo.descripcion_incidencia)), operacion="registrar_entrega")


@router.post("/ordenes/{orden_id}/incidencias", tags=[T_ORDENES], summary="Avisar de un problema durante el servicio",
             description="Registra un retraso, una avería u otro problema. **No cambia el paso** en que va el servicio; "
                         "solo deja constancia para que Operaciones lo vea.\n\n*Referencia técnica: historia US-11.*",
             response_description=OK, response_model=e.OperacionOut)
def registrar_incidencia(cuerpo: e.IncidenciaIn, request: Request, orden_id: str = ID_ORDEN):
    evidencia = cuerpo.evidencia.a_dominio(EventoAsociado.INCIDENCIA) if cuerpo.evidencia else None
    return _responder(_app(request).registrar_incidencia.handle(
        c.RegistrarIncidenciaCommand(orden_id, cuerpo.tipo, cuerpo.descripcion, evidencia)), operacion="registrar_incidencia")


@router.post("/ordenes/{orden_id}/cancelacion", tags=[T_ORDENES], summary="Cancelar el servicio",
             description="Cancela una orden que aún no se entregó. Queda anotado **quién** lo pidió y **por qué**.\n\n"
                         "Solo el área autorizada (normalmente Operaciones) puede confirmar una cancelación.\n\n"
                         "*Referencia técnica: supuesto S-04 y historia US-05.*",
             response_description=OK, response_model=e.OperacionOut)
def cancelar_servicio(cuerpo: e.CancelacionIn, request: Request, orden_id: str = ID_ORDEN):
    return _responder(_app(request).cancelar_servicio.handle(c.CancelarServicioCommand(orden_id, **cuerpo.model_dump())),
                      operacion="cancelar_servicio")


@router.post("/ordenes/{orden_id}/cambios-operativos", status_code=201, tags=[T_ORDENES],
             summary="Pedir un cambio en el servicio",
             description="Pide un cambio que afecta cómo se hará el servicio (por ejemplo, el horario). "
                         "**Mientras Operaciones no lo revise, el servicio no puede avanzar.**\n\n*Referencia técnica: historia US-04.*",
             response_description=CREADO, response_model=e.OperacionOut)
def solicitar_cambio(cuerpo: e.CambioOperativoIn, request: Request, orden_id: str = ID_ORDEN):
    return _responder(_app(request).solicitar_cambio.handle(
        c.SolicitarCambioOperativoCommand(orden_id, **cuerpo.model_dump())), 201, "solicitar_cambio")


@router.put("/ordenes/{orden_id}/cambios-operativos/revision", tags=[T_ORDENES], summary="Revisar un cambio solicitado",
            description="Operaciones decide si **aprueba** o **rechaza** el cambio pedido. Después, el servicio puede continuar.",
            response_description=OK, response_model=e.OperacionOut)
def revisar_cambio(cuerpo: e.RevisionDeCambioIn, request: Request, orden_id: str = ID_ORDEN):
    return _responder(_app(request).revisar_cambio.handle(
        c.RevisarCambioOperativoCommand(orden_id, **cuerpo.model_dump())), operacion="revisar_cambio")


# ------------------------------------ 4. Indicadores ------------------------------------
@router.get("/indicadores", tags=[T_INDICADORES], summary="Ver cifras del periodo (entregas, retrasos, problemas)",
            description="Muestra cuántas entregas se hicieron, cuántas fueron a tiempo, cuántos retrasos y problemas hubo "
                        "entre dos fechas.\n\n*Referencia técnica: historia US-15.*", response_description=OK)
def indicadores(request: Request,
                desde: date = Query(description="Primer día del periodo. Formato AAAA-MM-DD", examples=["2026-01-01"]),
                hasta: date = Query(description="Último día del periodo. Formato AAAA-MM-DD", examples=["2026-12-31"])):
    if desde > hasta:
        raise HTTPException(status_code=400, detail={
            "codigo": "DatosInvalidos",
            "mensaje": "La fecha inicial no puede ser posterior a la fecha final.",
            "que_hacer": "Intercambie las fechas o corrija alguna de ellas."})
    return _consulta(lambda: _dto(_app(request).consultar_indicadores.handle(c.ConsultarIndicadoresQuery(desde, hasta))))
