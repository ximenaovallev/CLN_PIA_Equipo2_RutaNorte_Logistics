"""Utilidades de prueba independientes del backend: leen y modifican agregados solo a través de la Unit of Work."""
from __future__ import annotations

from datetime import datetime, timezone

from domain.valores import Evidencia, EventoAsociado, TipoDeEvidencia

HORARIO = datetime(2026, 11, 2, 8, tzinfo=timezone.utc)


def evidencia(evento=EventoAsociado.ENTREGA, fecha=None) -> Evidencia:
    return Evidencia(TipoDeEvidencia.FOTOGRAFIA, "foto-001.jpg", fecha or datetime.now(timezone.utc), evento)


def leer_orden(app, orden_id):
    with app.uow as u:
        return u.ordenes.obtener_por_id(orden_id)


def leer_cotizacion(app, cotizacion_id):
    with app.uow as u:
        return u.cotizaciones.obtener_por_id(cotizacion_id)


def leer_operador(app, operador_id):
    with app.uow as u:
        return u.operadores.obtener_por_id(operador_id)


def cambiar_orden(app, orden_id, operacion):
    """Carga la orden, aplica `operacion(orden)` y la persiste (para preparar escenarios intermedios)."""
    with app.uow as u:
        o = u.ordenes.obtener_por_id(orden_id)
        operacion(o)
        u.ordenes.guardar(o)
        u.confirmar()


def sembrar(app, **entidades_por_repositorio):
    """sembrar(app, clientes=[...], unidades=[...], operadores=[...], cotizaciones=[...])"""
    with app.uow as u:
        for repo, entidades in entidades_por_repositorio.items():
            for e in entidades:
                getattr(u, repo).guardar(e)
        u.confirmar()


def contar_eventos(app, tipo) -> int:
    """Eventos publicados de un tipo (memoria: lista; SQL: tabla eventos_de_dominio)."""
    if app.almacen is not None:
        return sum(isinstance(e, tipo) for e in app.publicador.publicados)
    from sqlalchemy import func, select
    from infrastructure.sql.tablas import eventos_de_dominio as t
    with app.motor.connect() as c:
        return c.execute(select(func.count()).select_from(t).where(t.c.tipo == tipo.__name__)).scalar_one()
