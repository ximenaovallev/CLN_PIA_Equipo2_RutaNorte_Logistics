"""Construcción de View Models (lado de lectura) a partir de agregados del dominio.

La usa la consulta en memoria; la consulta SQL arma los mismos DTO directamente desde las tablas.
"""
from __future__ import annotations

from datetime import date

from application.dto import CotizacionDTO, EstadoDelServicioDTO, IndicadoresDTO, OrdenResumenDTO
from domain.cotizacion import Cotizacion
from domain.maquina_de_estados import CICLO_DE_VIDA_DEL_SERVICIO as CICLO
from domain.orden_de_servicio import EstadoServicio, OrdenDeServicio, TipoDeIncidencia


def dto_estado(orden: OrdenDeServicio) -> EstadoDelServicioDTO:
    return EstadoDelServicioDTO(
        orden_id=orden.id,
        estado_actual=orden.estado_actual().value,
        eventos=[f"{e.fecha:%Y-%m-%d %H:%M} · {e.descripcion}" for e in orden.historial],
        retrasos=[i.descripcion for i in orden.incidencias if i.tipo is TipoDeIncidencia.RETRASO],
        incidencias=[f"{i.tipo.value}: {i.descripcion}" for i in orden.incidencias],
        acciones_permitidas=sorted(d.value for d in CICLO.disparadores_permitidos(orden.estado_actual())),
        cambio_operativo_pendiente=orden.cambio_pendiente.descripcion if orden.cambio_pendiente else None,
        unidad_id=orden.asignacion.unidad_id if orden.asignacion else None,
        operador_id=orden.asignacion.operador_id if orden.asignacion else None,
    )


def dto_cotizacion(c: Cotizacion) -> CotizacionDTO:
    s = c.solicitud
    estado_servicio = c.estado_del_servicio
    return CotizacionDTO(
        cotizacion_id=c.id, cliente_id=c.cliente_id, estado=c.estado.value,
        estado_del_servicio=estado_servicio.value if estado_servicio else None,
        importe_mxn=c.importe_mxn, origen=s.origen.ciudad, destino=s.destino.ciudad,
        mercancia=s.mercancia.descripcion, peso_kg=s.mercancia.peso.kilogramos,
        alto_valor=s.mercancia.alto_valor, fecha_requerida=s.fecha_requerida,
    )


def dto_resumen(o: OrdenDeServicio) -> OrdenResumenDTO:
    return OrdenResumenDTO(o.id, o.cliente_id, o.estado_actual().value, o.ruta,
                           o.mercancia.alto_valor, o.fecha_requerida)


def dto_indicadores(ordenes: list[OrdenDeServicio], desde: date, hasta: date) -> IndicadoresDTO:
    en_periodo = [o for o in ordenes if desde <= o.historial[0].fecha.date() <= hasta]
    entregadas = [o for o in en_periodo if o.estado_actual() is EstadoServicio.ENTREGADO]
    tiempos = [(o.historial[-1].fecha - o.historial[0].fecha).total_seconds() / 3600 for o in entregadas]
    a_tiempo = sum(1 for o in entregadas
                   if o.fecha_requerida is not None and o.fecha_entrega.date() <= o.fecha_requerida)
    incidencias = [i for o in en_periodo for i in o.incidencias]
    return IndicadoresDTO(
        tiempos_reales_de_entrega_horas=tiempos,
        retrasos=sum(1 for i in incidencias if i.tipo is TipoDeIncidencia.RETRASO),
        incidencias=len(incidencias),
        entregas_realizadas=len(entregadas),
        ordenes_en_el_periodo=len(en_periodo),
        entregas_a_tiempo=a_tiempo,
        cumplimiento_de_entregas=(a_tiempo / len(entregadas)) if entregadas else None,
    )
