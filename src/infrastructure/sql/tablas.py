"""Esquema relacional. El dominio no conoce estas tablas: los repositorios traducen en ambos sentidos."""
from __future__ import annotations

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey, Index, Integer, MetaData, Numeric, String, Table, Text,
)

metadata = MetaData()
_TZ = DateTime(timezone=True)

clientes = Table(
    "clientes", metadata,
    Column("id", String(64), primary_key=True),
    Column("nombre", String(200), nullable=False),
    Column("ciudad", String(100), nullable=False, default=""),
)

unidades = Table(
    "unidades", metadata,
    Column("id", String(64), primary_key=True),
    Column("tipo", String(100), nullable=False),
    Column("peso_kg", Float, nullable=False),
    Column("volumen_m3", Float, nullable=False),
)

operadores = Table(
    "operadores", metadata,
    Column("id", String(64), primary_key=True),
    Column("nombre", String(200), nullable=False),
    Column("disponible", Boolean, nullable=False),
)


def _columnas_de_solicitud() -> list[Column]:
    return [
        Column("origen_ciudad", String(100), nullable=False),
        Column("origen_direccion", String(300), nullable=False, default=""),
        Column("destino_ciudad", String(100), nullable=False),
        Column("destino_direccion", String(300), nullable=False, default=""),
        Column("mercancia_descripcion", String(300), nullable=False),
        Column("mercancia_peso_kg", Float, nullable=False),
        Column("mercancia_largo_m", Float, nullable=False),
        Column("mercancia_ancho_m", Float, nullable=False),
        Column("mercancia_alto_m", Float, nullable=False),
        Column("mercancia_caracteristicas", String(300), nullable=False, default=""),
        Column("mercancia_alto_valor", Boolean, nullable=False, default=False),
        Column("fecha_requerida", Date, nullable=True),
    ]


cotizaciones = Table(
    "cotizaciones", metadata,
    Column("id", String(64), primary_key=True),
    Column("cliente_id", String(64), ForeignKey("clientes.id"), nullable=False),
    Column("estado", String(20), nullable=False),
    Column("importe_mxn", Numeric(12, 2), nullable=True),
    *_columnas_de_solicitud(),
)

ordenes = Table(
    "ordenes", metadata,
    Column("id", String(64), primary_key=True),
    Column("cotizacion_id", String(64), ForeignKey("cotizaciones.id"), nullable=False),
    Column("cliente_id", String(64), ForeignKey("clientes.id"), nullable=False),
    Column("estado", String(30), nullable=False),
    Column("ruta", String(200), nullable=False),
    Column("horario_recoleccion", _TZ, nullable=False),
    Column("alto_valor_autorizado", Boolean, nullable=False, default=False),
    Column("asignacion_unidad_id", String(64), ForeignKey("unidades.id"), nullable=True),
    Column("asignacion_operador_id", String(64), ForeignKey("operadores.id"), nullable=True),
    Column("destinatario", String(200), nullable=True),
    Column("fecha_entrega", _TZ, nullable=True),
    Column("cancelacion_solicitado_por", String(200), nullable=True),
    Column("cancelacion_motivo", Text, nullable=True),
    Column("cancelacion_fecha", _TZ, nullable=True),
    Column("cambio_solicitado_por", String(200), nullable=True),
    Column("cambio_descripcion", Text, nullable=True),
    Column("cambio_fecha", _TZ, nullable=True),
    *_columnas_de_solicitud(),
)
Index("ix_ordenes_estado", ordenes.c.estado)
Index("ix_ordenes_cliente", ordenes.c.cliente_id)

historial = Table(
    "orden_historial", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("orden_id", String(64), ForeignKey("ordenes.id", ondelete="CASCADE"), nullable=False),
    Column("posicion", Integer, nullable=False),
    Column("fecha", _TZ, nullable=False),
    Column("descripcion", Text, nullable=False),
    Column("estado_resultante", String(30), nullable=False),
    Column("registrado_por", String(200), nullable=False),
)
Index("ix_historial_orden", historial.c.orden_id, historial.c.posicion)

incidencias = Table(
    "orden_incidencias", metadata,
    Column("orden_id", String(64), ForeignKey("ordenes.id", ondelete="CASCADE"), primary_key=True),
    Column("numero", Integer, primary_key=True),
    Column("tipo", String(40), nullable=False),
    Column("descripcion", Text, nullable=False),
    Column("fecha_registro", _TZ, nullable=False),
)

evidencias = Table(
    "orden_evidencias", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("orden_id", String(64), ForeignKey("ordenes.id", ondelete="CASCADE"), nullable=False),
    Column("categoria", String(12), nullable=False),  # RECEPCION | ENTREGA | INCIDENCIA
    Column("incidencia_numero", Integer, nullable=True),
    Column("tipo", String(20), nullable=False),
    Column("referencia", String(500), nullable=False),
    Column("fecha", _TZ, nullable=False),
    Column("evento_asociado", String(20), nullable=False),
)
Index("ix_evidencias_orden", evidencias.c.orden_id)

eventos_de_dominio = Table(
    "eventos_de_dominio", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("tipo", String(100), nullable=False),
    Column("agregado_id", String(64), nullable=True),
    Column("datos", Text, nullable=False),
    Column("ocurrio_en", _TZ, nullable=False),
)
Index("ix_eventos_agregado", eventos_de_dominio.c.agregado_id)
