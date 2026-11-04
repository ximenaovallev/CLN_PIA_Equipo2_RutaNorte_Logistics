"""Paquete de datos del profesor (LEEME): 120 casos de reglas y 20 transiciones, contra oráculos propios."""
from collections import Counter
from decimal import Decimal

import pytest

from dataset.cargador import cargar_paquete
from dataset.escenarios import ejecutar_casos, ejecutar_transicion, preparar_recursos
from dataset.modelo_de_referencia import (
    CantidadesDentroDeLaCapacidad, ServiciosHabilitados, beneficio_referencia, puede_procesarse,
)

PAQUETE = cargar_paquete()


def test_el_paquete_se_importa_completo_con_integridad_referencial():
    assert (len(PAQUETE.actores), len(PAQUETE.recursos), len(PAQUETE.operaciones)) == (40, 20, 60)
    assert len(PAQUETE.casos_prueba) == 120 and len(PAQUETE.transiciones) == 20
    assert sum(len(o.lineas) for o in PAQUETE.operaciones.values()) == 117
    assert {c["operacion_id"] for c in PAQUETE.casos_prueba} <= set(PAQUETE.operaciones)
    assert all(o.estado_inicial == "REGISTRADO" for o in PAQUETE.operaciones.values())


def test_total_se_calcula_con_decimal_sin_error_de_punto_flotante():
    op = PAQUETE.operaciones["ENV-O001"]
    assert op.total == sum(l.recurso.precio_mxn * l.cantidad for l in op.lineas) == Decimal("2505.00") + Decimal("4760.00")
    assert isinstance(op.total, Decimal) and PAQUETE.operaciones["ENV-O013"].total == Decimal("0")


def test_las_120_pruebas_de_reglas_coinciden_con_el_oraculo_independiente():
    filas = ejecutar_casos(PAQUETE)
    assert Counter(f["resultado_alumno"] for f in filas) == {"PASA": 120}
    por_tipo = Counter((f["tipo_prueba"], f["resultado_obtenido_specification"]) for f in filas)
    assert por_tipo[("validar_operacion", "True")] == 44 and por_tipo[("validar_operacion", "False")] == 16
    assert por_tipo[("evaluar_beneficio", "True")] == 11 and por_tipo[("evaluar_beneficio", "False")] == 49


def test_la_composicion_and_not_explica_por_que_no_aplica_el_beneficio():
    op = next(o for o in PAQUETE.operaciones.values() if not o.actor.preferente)
    motivos = beneficio_referencia().motivos_de_incumplimiento(op)
    assert motivos and "preferente" in motivos[0]
    sin_detalle = PAQUETE.operaciones["ENV-O013"]
    assert any("al menos una línea" in m for m in puede_procesarse().motivos_de_incumplimiento(sin_detalle))


def test_validacion_de_disponibilidad_y_cantidades_del_catalogo():
    deshabilitadas = [o.id for o in PAQUETE.operaciones.values() if not ServiciosHabilitados().es_satisfecha_por(o)]
    assert deshabilitadas == ["ENV-O005", "ENV-O015", "ENV-O020", "ENV-O035", "ENV-O040", "ENV-O055"]
    assert all(CantidadesDentroDeLaCapacidad().es_satisfecha_por(o) for o in PAQUETE.operaciones.values())


def test_las_20_transiciones_se_ejecutan_con_el_codigo_real_y_cumplen_el_oraculo(app):
    preparar_recursos(app)
    filas = [ejecutar_transicion(app, PAQUETE, f) for f in PAQUETE.transiciones]
    malas = [f for f in filas if f["resultado_alumno"] != "PASA"]
    assert not malas, malas
    assert Counter(f["estado_final_dominio"] for f in filas)["ENTREGADO"] >= 1


def test_diferencia_documentada_repetir_aprobacion_es_una_reasignacion_valida(app):
    """El paquete la trataría como transición inválida; el BRD (US-08) permite reasignar conservando el historial."""
    from dataset.escenarios import accion, registrar_operacion
    from helpers import leer_orden
    preparar_recursos(app)
    op = PAQUETE.operaciones["ENV-O003"]
    oid = registrar_operacion(app, op)["orden_id"]
    assert accion(app, oid, "repetir_aprobacion").exito
    historial = [h.descripcion for h in leer_orden(app, oid).historial]
    assert sum("asignados" in d or "Asignación" in d for d in historial) == 2
