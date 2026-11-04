"""State Machine: la tabla de transiciones es la única fuente de verdad del ciclo de vida (ADR-008)."""
import pytest

from domain.comunes import TransicionDeEstadoInvalida
from domain.maquina_de_estados import CICLO_DE_VIDA_DEL_SERVICIO as CICLO, Disparador as D, EstadoServicio as S


def test_camino_feliz_recorre_los_ocho_estados_del_brd_en_orden():
    estado = CICLO.inicial
    camino = [estado]
    for d in (D.ELABORAR_COTIZACION, D.CONFIRMAR_SERVICIO, D.ASIGNAR_RECURSOS, D.REGISTRAR_RECEPCION,
              D.INICIAR_TRASLADO, D.REGISTRAR_LLEGADA, D.REGISTRAR_ENTREGA):
        estado = CICLO.aplicar(estado, d)
        camino.append(estado)
    assert [e.value for e in camino] == ["SOLICITADO", "COTIZADO", "CONFIRMADO", "UNIDAD_ASIGNADA", "RECOLECTADO",
                                         "EN_TRANSITO", "LLEGADA_A_DESTINO", "ENTREGADO"]


def test_reasignar_deja_el_servicio_en_unidad_asignada():
    assert CICLO.aplicar(S.UNIDAD_ASIGNADA, D.ASIGNAR_RECURSOS) is S.UNIDAD_ASIGNADA


@pytest.mark.parametrize("estado", [S.CONFIRMADO, S.UNIDAD_ASIGNADA, S.RECOLECTADO, S.EN_TRANSITO, S.LLEGADA_A_DESTINO])
def test_se_puede_cancelar_un_servicio_aceptado_que_no_ha_terminado(estado):
    assert CICLO.aplicar(estado, D.CANCELAR) is S.CANCELADO


@pytest.mark.parametrize("estado", [S.SOLICITADO, S.COTIZADO, S.ENTREGADO, S.CANCELADO])
def test_no_se_cancela_antes_de_aceptar_ni_despues_de_terminar(estado):
    assert not CICLO.es_valida(estado, D.CANCELAR)


@pytest.mark.parametrize("estado", [S.ENTREGADO, S.CANCELADO])
def test_entregado_y_cancelado_son_terminales(estado):
    assert CICLO.es_terminal(estado) and CICLO.disparadores_permitidos(estado) == set()


def test_ningun_estado_no_terminal_es_callejon_sin_salida():
    for estado in S:
        if estado not in (S.ENTREGADO, S.CANCELADO):
            assert not CICLO.es_terminal(estado), estado


def test_todos_los_estados_son_alcanzables_desde_el_inicial():
    alcanzados, pendientes = {CICLO.inicial}, [CICLO.inicial]
    while pendientes:
        actual = pendientes.pop()
        for origen, _, destino in CICLO.transiciones():
            if origen is actual and destino not in alcanzados:
                alcanzados.add(destino)
                pendientes.append(destino)
    assert alcanzados == set(S)


def test_todo_disparador_se_usa_en_al_menos_una_transicion():
    assert {d for _, d, _ in CICLO.transiciones()} == set(D)


def test_transicion_invalida_explica_que_se_requeria():
    with pytest.raises(TransicionDeEstadoInvalida) as e:
        CICLO.aplicar(S.CONFIRMADO, D.REGISTRAR_ENTREGA, "registrar la entrega")
    assert "No se puede registrar la entrega en estado CONFIRMADO (se requiere LLEGADA_A_DESTINO)." in str(e.value)


def test_transicion_invalida_sin_accion_usa_el_nombre_del_disparador():
    with pytest.raises(TransicionDeEstadoInvalida) as e:
        CICLO.aplicar(S.ENTREGADO, D.INICIAR_TRASLADO)
    assert "INICIAR_TRASLADO" in str(e.value)


def test_estados_origen_de_un_disparador():
    assert CICLO.estados_origen(D.ASIGNAR_RECURSOS) == {S.CONFIRMADO, S.UNIDAD_ASIGNADA}
    assert CICLO.estados_origen(D.CANCELAR) == {S.CONFIRMADO, S.UNIDAD_ASIGNADA, S.RECOLECTADO, S.EN_TRANSITO,
                                                S.LLEGADA_A_DESTINO}
