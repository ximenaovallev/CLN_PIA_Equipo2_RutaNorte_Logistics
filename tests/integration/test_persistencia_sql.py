"""Persistencia SQL: ida y vuelta de agregados, transacciones, eventos y configuración 12-Factor."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from application.comandos import AsignarRecursosCommand, CancelarServicioCommand, RegistrarEntregaCommand
from domain.cliente import Cliente
from domain.comunes import EntidadNoEncontrada
from domain.eventos import OrdenDeServicioGenerada
from domain.orden_de_servicio import EstadoServicio, TipoDeIncidencia
from domain.valores import Destinatario, EventoAsociado
from infrastructure.composicion import construir_aplicacion_sql
from infrastructure.configuracion import Configuracion
from infrastructure.sql import tablas as t
from infrastructure.sql.motor import normalizar_url
from conftest import configuracion
from helpers import cambiar_orden, contar_eventos, evidencia, leer_cotizacion, leer_orden, sembrar


@pytest.fixture
def app_sql():
    return construir_aplicacion_sql(configuracion())


def test_la_orden_completa_sobrevive_a_guardar_y_cargar(orden_en_destino):
    app, oid = orden_en_destino
    app.registrar_entrega.handle(RegistrarEntregaCommand(
        oid, None, evidencia(EventoAsociado.INCIDENCIA), TipoDeIncidencia.DESTINATARIO_AUSENTE, "Nadie recibió"))
    app.registrar_entrega.handle(RegistrarEntregaCommand(oid, Destinatario("INE-9"), evidencia()))
    o = leer_orden(app, oid)
    assert o.estado_actual() is EstadoServicio.ENTREGADO
    assert o.destinatario == Destinatario("INE-9") and o.fecha_entrega is not None
    assert o.fecha_entrega.tzinfo is not None
    assert o.asignacion.unidad_id == "U-GRANDE" and o.asignacion.operador_id == "OP-1"
    assert len(o.evidencias_recepcion) == 1 and len(o.evidencias_entrega) == 1
    assert o.incidencias[0].tipo is TipoDeIncidencia.DESTINATARIO_AUSENTE and len(o.incidencias[0].evidencias) == 1
    assert [h.estado_resultante.value for h in o.historial][-1] == "ENTREGADO"
    assert o.historial[0].fecha <= o.historial[-1].fecha


def test_la_cancelacion_y_el_cambio_pendiente_se_persisten(orden_confirmada):
    app, oid = orden_confirmada
    cambiar_orden(app, oid, lambda o: o.solicitar_cambio_operativo("Cliente", "Otro horario"))
    assert leer_orden(app, oid).cambio_pendiente.descripcion == "Otro horario"
    cambiar_orden(app, oid, lambda o: o.revisar_cambio_operativo("Operaciones", True))
    assert leer_orden(app, oid).cambio_pendiente is None
    assert app.cancelar_servicio.handle(CancelarServicioCommand(oid, "Cliente", "Motivo")).exito
    c = leer_orden(app, oid).cancelacion
    assert c.solicitado_por == "Cliente" and c.motivo == "Motivo"


def test_el_importe_se_guarda_como_decimal_exacto(mundo):
    assert leer_cotizacion(mundo, "COT-1").importe_mxn == Decimal("15000.00")


def test_error_de_dominio_revierte_la_transaccion(orden_confirmada):
    app, oid = orden_confirmada
    r = app.asignar_recursos.handle(AsignarRecursosCommand(oid, "U-GRANDE", "OP-2"))  # OP-2 no disponible
    assert not r.exito
    o = leer_orden(app, oid)
    assert o.estado_actual() is EstadoServicio.CONFIRMADO and o.asignacion is None and len(o.historial) == 1


def test_salir_sin_confirmar_no_deja_nada(app, solicitud):
    with app.uow as u:
        u.clientes.guardar(Cliente("CLI-X", "Temporal"))
    with app.uow as u:
        assert not u.clientes.existe("CLI-X")
    with app.uow as u:
        u.clientes.guardar(Cliente("CLI-X", "Temporal"))
        u.revertir()
    with app.uow as u:
        assert not u.clientes.existe("CLI-X")
    with app.uow as u:
        u.clientes.guardar(Cliente("CLI-X", "Definitivo"))
        u.confirmar()
    with app.uow as u:
        assert u.clientes.obtener_por_id("CLI-X").nombre == "Definitivo"


def test_guardar_dos_veces_actualiza_y_no_duplica(app):
    sembrar(app, clientes=[Cliente("C", "Uno")])
    sembrar(app, clientes=[Cliente("C", "Dos", "MTY")])
    with app.uow as u:
        c = u.clientes.obtener_por_id("C")
    assert (c.nombre, c.ciudad) == ("Dos", "MTY")


@pytest.mark.parametrize("repo", ["clientes", "unidades", "operadores", "cotizaciones", "ordenes"])
def test_obtener_inexistente_lanza_entidad_no_encontrada(app, repo):
    with app.uow as u, pytest.raises(EntidadNoEncontrada):
        getattr(u, repo).obtener_por_id("NO-EXISTE")


def test_los_domain_events_se_registran_tras_confirmar(orden_confirmada):
    app, _ = orden_confirmada
    assert contar_eventos(app, OrdenDeServicioGenerada) == 1


def test_los_eventos_sql_quedan_en_la_tabla_con_su_agregado(app_sql):
    sembrar(app_sql, clientes=[Cliente("C", "Uno")])
    from domain.eventos import CotizacionElaborada
    from datetime import date
    from application.comandos import SolicitarCotizacionCommand, ElaborarCotizacionCommand
    from domain.valores import Dimensiones, Mercancia, Peso, SolicitudDeCotizacion, Ubicacion
    sol = SolicitudDeCotizacion(Ubicacion("A"), Ubicacion("B"), Mercancia("x", Peso(1), Dimensiones(1, 1, 1)), date(2026, 12, 1))
    cid = app_sql.solicitar_cotizacion.handle(SolicitarCotizacionCommand("C", sol)).datos["cotizacion_id"]
    app_sql.elaborar_cotizacion.handle(ElaborarCotizacionCommand(cid, Decimal("5")))
    with app_sql.motor.connect() as c:
        filas = c.execute(select(t.eventos_de_dominio).where(t.eventos_de_dominio.c.tipo == "CotizacionElaborada")).all()
    assert len(filas) == 1 and filas[0].agregado_id == cid and "5" in filas[0].datos


def test_publicar_sin_eventos_no_escribe(app_sql):
    app_sql.publicador.publicar([])
    with app_sql.motor.connect() as c:
        assert c.execute(select(func.count()).select_from(t.eventos_de_dominio)).scalar_one() == 0


# ------------------------------------ configuración ------------------------------------
def test_normalizar_url_acepta_las_formas_de_las_plataformas():
    assert normalizar_url("postgres://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalizar_url("postgresql://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalizar_url("postgresql+psycopg://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalizar_url("sqlite:///x.db") == "sqlite:///x.db"


def test_configuracion_se_lee_solo_del_entorno(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db/rutanorte")
    monkeypatch.setenv("APP_ENV", "produccion")
    monkeypatch.setenv("LIMITE_PESO_KG", "12000")
    monkeypatch.setenv("LIMITE_VOLUMEN_M3", "60.5")
    monkeypatch.setenv("DIAS_CONSERVACION_EVIDENCIAS", "365")
    monkeypatch.setenv("ROLES_QUE_CANCELAN", "Operaciones, Ventas")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    cfg = Configuracion.desde_entorno()
    assert cfg.database_url.endswith("/rutanorte") and cfg.entorno == "produccion" and cfg.nivel_de_log == "DEBUG"
    assert cfg.peso_maximo_kg == 12000 and cfg.volumen_maximo_m3 == 60.5 and cfg.dias_de_conservacion == 365
    assert cfg.roles_que_cancelan == {"Operaciones", "Ventas"}


def test_configuracion_por_omision_no_define_supuestos(monkeypatch):
    for v in ("DATABASE_URL", "LIMITE_PESO_KG", "LIMITE_VOLUMEN_M3", "DIAS_CONSERVACION_EVIDENCIAS", "ROLES_QUE_CANCELAN"):
        monkeypatch.delenv(v, raising=False)
    cfg = Configuracion.desde_entorno()
    assert cfg.peso_maximo_kg is None and cfg.dias_de_conservacion is None
    assert cfg.roles_que_cancelan == {"Operaciones"} and cfg.database_url.startswith("sqlite")
