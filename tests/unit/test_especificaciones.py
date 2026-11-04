"""Specification pattern: reglas de negocio componibles con Y (&), O (|) y NO (~) (ADR-007)."""
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from domain.cotizacion import Cotizacion
from domain.especificaciones import (
    AltoValorAutorizado, CambioOperativoPendiente, CandidatoDeAsignacion, CargaDeAltoValor, AceptadaPorElCliente,
    CotizacionConImporte, CotizacionEnProceso, DatosDeEntrega, DentroDeLosLimitesDeLaEmpresa, EvidenciaDelEvento,
    OperadorDisponible, ReceptorIdentificado, UnidadConCapacidadSuficiente, asignacion_permitida,
    control_de_alto_valor_cumplido, entrega_documentada, recepcion_documentada, sin_cambio_pendiente, unidad_adecuada,
)
from domain.orden_de_servicio import OrdenDeServicio
from domain.recursos import Operador, Unidad
from domain.valores import (
    Capacidad, Destinatario, Dimensiones, Evidencia, EventoAsociado, Horario, Mercancia, Peso, SolicitudDeCotizacion,
    TipoDeEvidencia, Ubicacion, Volumen,
)


def _solicitud(peso=800, alto_valor=False, dims=(2, 1.5, 1.5)):
    return SolicitudDeCotizacion(Ubicacion("MTY"), Ubicacion("QRO"),
                                 Mercancia("Refacciones", Peso(peso), Dimensiones(*dims), alto_valor=alto_valor),
                                 date(2026, 11, 1))


def _orden(**kw):
    c = Cotizacion("C", "CLI", _solicitud(**kw))
    c.elaborar(Decimal("100"))
    c.aceptar()
    return OrdenDeServicio.generar_desde("O", c, "MTY-QRO", Horario(datetime(2026, 11, 2, 8, tzinfo=timezone.utc)))


def _unidad(peso=5000, volumen=30):
    return Unidad("U", "Caja seca", Capacidad(Peso(peso), Volumen(volumen)))


def _candidato(peso_carga=800, peso_unidad=5000, disponible=True):
    return CandidatoDeAsignacion(_orden(peso=peso_carga), _unidad(peso_unidad), Operador("OP", "Op", disponible))


def _ev(evento=EventoAsociado.ENTREGA):
    return Evidencia(TipoDeEvidencia.FOTOGRAFIA, "f.jpg", datetime.now(timezone.utc), evento)


# ---- operadores lógicos ----
class _Siempre:
    pass


def test_y_exige_ambas_y_reporta_los_motivos_de_las_que_fallan():
    spec = UnidadConCapacidadSuficiente() & OperadorDisponible()
    assert spec.es_satisfecha_por(_candidato())
    c = _candidato(peso_carga=9000, disponible=False)
    motivos = spec.motivos_de_incumplimiento(c)
    assert not spec.es_satisfecha_por(c) and len(motivos) == 2
    assert any("no es adecuada" in m for m in motivos) and any("no está disponible" in m for m in motivos)


def test_o_basta_con_una_y_si_ninguna_se_cumple_reporta_ambos_motivos():
    spec = UnidadConCapacidadSuficiente() | OperadorDisponible()
    assert spec.es_satisfecha_por(_candidato(peso_carga=9000, disponible=True))
    assert spec.es_satisfecha_por(_candidato(peso_carga=800, disponible=False))
    c = _candidato(peso_carga=9000, disponible=False)
    assert not spec.es_satisfecha_por(c)
    assert len(spec.motivos_de_incumplimiento(c)) == 2
    assert spec.motivos_de_incumplimiento(_candidato()) == []


def test_no_invierte_la_regla():
    spec = ~OperadorDisponible()
    assert spec.es_satisfecha_por(_candidato(disponible=False))
    assert not spec.es_satisfecha_por(_candidato(disponible=True))
    assert spec.descripcion.startswith("NO ")
    assert "No debe cumplirse" in spec.motivos_de_incumplimiento(_candidato())[0]


def test_la_descripcion_de_una_composicion_se_lee_como_la_regla_de_negocio():
    d = asignacion_permitida().descripcion
    assert " Y " in d and "operador" in d


def test_una_especificacion_satisfecha_no_tiene_motivos_de_incumplimiento():
    assert OperadorDisponible().motivos_de_incumplimiento(_candidato()) == []


# ---- asignación (G2) y S-01 ----
def test_unidad_adecuada_considera_capacidad_de_la_unidad_y_limites_de_la_empresa():
    assert unidad_adecuada().es_satisfecha_por(_candidato())
    assert not unidad_adecuada(peso_maximo_kg=500).es_satisfecha_por(_candidato())
    assert not unidad_adecuada(volumen_maximo_m3=1).es_satisfecha_por(_candidato())
    assert unidad_adecuada(peso_maximo_kg=800, volumen_maximo_m3=4.5).es_satisfecha_por(_candidato())


def test_la_unidad_sin_volumen_suficiente_no_es_adecuada():
    c = CandidatoDeAsignacion(_orden(), _unidad(volumen=1), Operador("OP", "Op", True))
    assert not UnidadConCapacidadSuficiente().es_satisfecha_por(c)


def test_limites_de_la_empresa_sin_topes_siempre_se_cumplen():
    assert DentroDeLosLimitesDeLaEmpresa().es_satisfecha_por(_candidato(peso_carga=40000, peso_unidad=50000))


# ---- alto valor (S-02) ----
def test_control_de_alto_valor_combina_no_y_o():
    control = control_de_alto_valor_cumplido()
    normal, valioso = _orden(), _orden(alto_valor=True)
    assert CargaDeAltoValor().es_satisfecha_por(valioso) and not CargaDeAltoValor().es_satisfecha_por(normal)
    assert control.es_satisfecha_por(normal)                      # NO alto valor
    assert not control.es_satisfecha_por(valioso)                 # alto valor sin autorizar
    assert "autorizarla" in control.motivos_de_incumplimiento(valioso)[0]
    assert not AltoValorAutorizado().es_satisfecha_por(valioso)
    valioso.autorizar_alto_valor("Operaciones")
    assert control.es_satisfecha_por(valioso) and control.motivos_de_incumplimiento(valioso) == []


# ---- cambios operativos (US-04) ----
def test_sin_cambio_pendiente():
    o = _orden()
    assert sin_cambio_pendiente().es_satisfecha_por(o)
    o.solicitar_cambio_operativo("Cliente", "Mover la hora de recolección")
    assert CambioOperativoPendiente().es_satisfecha_por(o) and not sin_cambio_pendiente().es_satisfecha_por(o)


# ---- evidencia y receptor (US-09, US-12, US-13) ----
def test_entrega_documentada_exige_receptor_y_evidencia_de_entrega():
    assert entrega_documentada().es_satisfecha_por(DatosDeEntrega(Destinatario("INE"), _ev()))
    sin_receptor = DatosDeEntrega(None, _ev())
    sin_evidencia = DatosDeEntrega(Destinatario("INE"), None)
    assert not ReceptorIdentificado().es_satisfecha_por(sin_receptor)
    assert not entrega_documentada().es_satisfecha_por(sin_receptor)
    assert not entrega_documentada().es_satisfecha_por(sin_evidencia)
    assert len(entrega_documentada().motivos_de_incumplimiento(DatosDeEntrega(None, None))) == 2


def test_evidencia_debe_corresponder_al_evento():
    datos = DatosDeEntrega(Destinatario("INE"), _ev(EventoAsociado.RECEPCION))
    assert not EvidenciaDelEvento(EventoAsociado.ENTREGA).es_satisfecha_por(datos)
    assert EvidenciaDelEvento(EventoAsociado.RECEPCION).es_satisfecha_por(datos)
    assert recepcion_documentada().es_satisfecha_por(datos)


# ---- cotización ----
def test_especificaciones_de_cotizacion_siguen_su_ciclo():
    c = Cotizacion("C", "CLI", _solicitud())
    assert CotizacionEnProceso().es_satisfecha_por(c) and not CotizacionConImporte().es_satisfecha_por(c)
    c.elaborar(Decimal("10"))
    assert CotizacionConImporte().es_satisfecha_por(c) and not AceptadaPorElCliente().es_satisfecha_por(c)
    c.aceptar()
    assert AceptadaPorElCliente().es_satisfecha_por(c) and not CotizacionEnProceso().es_satisfecha_por(c)
