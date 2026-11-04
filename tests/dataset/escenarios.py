"""Ejecución del paquete del profesor: 120 casos de reglas (Specification) y 20 transiciones (código real del equipo)."""
from __future__ import annotations

from datetime import date, datetime, timezone

from application.comandos import (
    AsignarRecursosCommand, CancelarServicioCommand, ElaborarCotizacionCommand, GenerarOrdenDeServicioCommand,
    IniciarTrasladoCommand, RegistrarClienteCommand, RegistrarEntregaCommand, RegistrarLlegadaCommand,
    RegistrarOperadorCommand, RegistrarRecepcionCommand, RegistrarUnidadCommand, ResponderCotizacionCommand,
    RespuestaDelCliente, SolicitarCotizacionCommand, ConsultarEstadoDelServicioQuery,
)
from domain.valores import (
    Destinatario, Dimensiones, Evidencia, EventoAsociado, Mercancia, Peso, SolicitudDeCotizacion, TipoDeEvidencia,
    Ubicacion,
)

from .cargador import Operacion, Paquete
from .modelo_de_referencia import (
    beneficio_referencia, oraculo_beneficio, oraculo_puede_procesarse, puede_procesarse,
)

# Correspondencia entre el flujo de referencia del LEEME y los estados del BRD del equipo (docs/arquitectura/paquete_de_datos.md)
ESTADO_DE_REFERENCIA = {"CONFIRMADO": "REGISTRADO", "UNIDAD_ASIGNADA": "ASIGNADO", "RECOLECTADO": "ASIGNADO",
                        "EN_TRANSITO": "EN_RUTA", "LLEGADA_A_DESTINO": "EN_RUTA", "ENTREGADO": "ENTREGADO",
                        "CANCELADO": "CANCELADO"}


# ----------------------------------------------- 120 casos de reglas -----------------------------------------------
def ejecutar_casos(paquete: Paquete) -> list[dict[str, str]]:
    filas = []
    for caso in paquete.casos_prueba:
        op = paquete.operaciones[caso["operacion_id"]]
        if caso["tipo_prueba"] == "validar_operacion":
            spec, esperado = puede_procesarse(), oraculo_puede_procesarse(op)
        else:
            spec, esperado = beneficio_referencia(), oraculo_beneficio(op)
        obtenido = spec.es_satisfecha_por(op)
        motivos = spec.motivos_de_incumplimiento(op)
        filas.append({
            "caso_id": caso["caso_id"], "operacion_id": op.id, "tipo_prueba": caso["tipo_prueba"],
            "regla_a_verificar": caso["regla_a_verificar"], "total_mxn": f"{op.total:.2f}",
            "resultado_esperado_oraculo": str(esperado), "resultado_obtenido_specification": str(obtenido),
            "resultado_alumno": "PASA" if obtenido == esperado else "FALLA",
            "evidencia": "se cumple" if obtenido else " ".join(motivos),
        })
    return filas


# ----------------------------------------------- 20 transiciones -----------------------------------------------
def preparar_recursos(app) -> None:
    app.registrar_unidad.handle(RegistrarUnidadCommand("UNI-PAQ", "Camión torton", 20000, 100))
    app.registrar_operador.handle(RegistrarOperadorCommand("OPE-PAQ", "Operador del paquete"))


def _evidencia(evento: EventoAsociado) -> Evidencia:
    return Evidencia(TipoDeEvidencia.FOTOGRAFIA, "paquete/evidencia.jpg", datetime.now(timezone.utc), evento)


def _solicitud(op: Operacion) -> SolicitudDeCotizacion:
    unidades = max(sum(l.cantidad for l in op.lineas), 1)
    return SolicitudDeCotizacion(Ubicacion(op.actor.ciudad), Ubicacion("Monterrey"),
                                 Mercancia(f"Servicios {op.id}", Peso(50 * unidades), Dimensiones(1, 1, 1)),
                                 date.fromisoformat(op.fecha_solicitud))


def eventos_de(app, *ids: str) -> list[str]:
    if app.almacen is not None:
        return [type(e).__name__ for e in app.publicador.publicados
                if getattr(e, "orden_id", None) in ids or getattr(e, "cotizacion_id", None) in ids]
    from sqlalchemy import select
    from infrastructure.sql.tablas import eventos_de_dominio as t
    with app.motor.connect() as c:
        return [r.tipo for r in c.execute(select(t.c.tipo).where(t.c.agregado_id.in_(ids)).order_by(t.c.id))]


def registrar_operacion(app, op: Operacion) -> dict:
    """Lleva la operación al punto de partida del paquete (REGISTRADO ≡ CONFIRMADO): cliente, cotización por el
    total Decimal de sus líneas, aceptación (la «autorización» del paquete) y orden de servicio."""
    app.registrar_cliente.handle(RegistrarClienteCommand(op.actor.id, op.actor.nombre, op.actor.ciudad))
    cot = app.solicitar_cotizacion.handle(SolicitarCotizacionCommand(op.actor.id, _solicitud(op))).datos["cotizacion_id"]
    elaborada = app.elaborar_cotizacion.handle(ElaborarCotizacionCommand(cot, op.total))
    if not elaborada.exito:
        return {"cotizacion_id": cot, "orden_id": None, "fallo": elaborada}
    if op.autorizado:
        app.responder_cotizacion.handle(ResponderCotizacionCommand(cot, RespuestaDelCliente.ACEPTA))
    generada = app.generar_orden.handle(GenerarOrdenDeServicioCommand(
        cot, f"{op.actor.ciudad}-Monterrey", datetime(2026, 11, 20, 8, tzinfo=timezone.utc)))
    if not generada.exito:
        return {"cotizacion_id": cot, "orden_id": None, "fallo": generada}
    return {"cotizacion_id": cot, "orden_id": generada.datos["orden_id"], "fallo": None}


def _asignar(app, oid):
    return app.asignar_recursos.handle(AsignarRecursosCommand(oid, "UNI-PAQ", "OPE-PAQ"))


def _completar(app, oid):
    pasos = (
        lambda: _asignar(app, oid),
        lambda: app.registrar_recepcion.handle(RegistrarRecepcionCommand(oid, _evidencia(EventoAsociado.RECEPCION))),
        lambda: app.iniciar_traslado.handle(IniciarTrasladoCommand(oid)),
        lambda: app.registrar_llegada.handle(RegistrarLlegadaCommand(oid)),
        lambda: app.registrar_entrega.handle(RegistrarEntregaCommand(oid, Destinatario("INE-PAQUETE"), _evidencia(EventoAsociado.ENTREGA))),
    )
    r = None
    for paso in pasos:
        r = paso()
        if not r.exito:
            break
    return r


def accion(app, oid: str, nombre: str):
    """Ejecuta la acción sugerida con el código real. Cada acción del paquete se traduce a casos de uso del BRD."""
    if nombre == "aprobar":                  # asignar unidad y operador
        return _asignar(app, oid)
    if nombre == "repetir_aprobacion":       # asignar dos veces (en el BRD la segunda es una reasignación, US-08)
        _asignar(app, oid)
        return _asignar(app, oid)
    if nombre == "completar":                # recorrido completo hasta la entrega
        return _completar(app, oid)
    if nombre == "cancelar":
        return app.cancelar_servicio.handle(CancelarServicioCommand(oid, "Cliente", "Cancelación solicitada en el paquete de pruebas"))
    if nombre == "saltar_estado":            # entregar sin pasar por los estados intermedios
        return app.registrar_entrega.handle(RegistrarEntregaCommand(oid, Destinatario("INE-PAQUETE"), _evidencia(EventoAsociado.ENTREGA)))
    raise ValueError(f"Acción desconocida: {nombre}")


def oraculo_de_transicion(op: Operacion, nombre: str) -> tuple[str, str]:
    """(estado final del dominio, evento o excepción esperado) derivado de las reglas del BRD, no del código."""
    if not op.lineas:
        return "SIN_ORDEN", "DatosInvalidos"         # no hay importe que cotizar (importe > 0, BRD: cotización)
    if not op.autorizado:
        return "SIN_ORDEN", "OrdenNoGenerable"       # el cliente no aceptó: no se genera la orden (US-06)
    return {
        "aprobar": ("UNIDAD_ASIGNADA", "RecursosAsignados"),
        "repetir_aprobacion": ("UNIDAD_ASIGNADA", "RecursosAsignados"),  # DIFERENCIA con el paquete: reasignar es válido (US-08)
        "completar": ("ENTREGADO", "EntregaRegistrada"),
        "cancelar": ("CANCELADO", "ServicioCancelado"),
        "saltar_estado": ("CONFIRMADO", "TransicionDeEstadoInvalida"),
    }[nombre]


def ejecutar_transicion(app, paquete: Paquete, fila: dict[str, str]) -> dict[str, str]:
    op = paquete.operaciones[fila["operacion_id"]]
    nombre = fila["accion_sugerida"]
    esperado_estado, esperado_evento = oraculo_de_transicion(op, nombre)
    preparada = registrar_operacion(app, op)
    if preparada["orden_id"] is None:
        r = preparada["fallo"]
        estado, evento = "SIN_ORDEN", r.codigo_de_error
    else:
        oid = preparada["orden_id"]
        r = accion(app, oid, nombre)
        estado = app.consultar_estado.handle(ConsultarEstadoDelServicioQuery(oid)).estado_actual
        evento = eventos_de(app, oid)[-1] if r.exito else r.codigo_de_error
    return {
        "caso_id": fila["caso_id"], "operacion_id": op.id, "accion_sugerida": nombre,
        "estado_inicial_paquete": fila["estado_inicial"], "estado_inicial_dominio": "CONFIRMADO" if preparada["orden_id"] else "SIN_ORDEN",
        "estado_final_dominio": estado, "equivalente_en_el_paquete": ESTADO_DE_REFERENCIA.get(estado, estado),
        "evento_o_excepcion": evento or "", "esperado_estado": esperado_estado, "esperado_evento": esperado_evento,
        "resultado_alumno": "PASA" if (estado, evento) == (esperado_estado, esperado_evento) else "FALLA",
    }
