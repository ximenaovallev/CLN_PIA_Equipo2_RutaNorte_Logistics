"""Repositories SQL: traducen entre las filas y los agregados del dominio."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import Session

from domain.cliente import Cliente
from domain.comunes import EntidadNoEncontrada
from domain.cotizacion import Cotizacion, EstadoCotizacion
from domain.maquina_de_estados import EstadoServicio
from domain.orden_de_servicio import (
    CambioOperativo,
    Cancelacion,
    EntradaDeHistorial,
    Incidencia,
    OrdenDeServicio,
    TipoDeIncidencia,
)
from domain.recursos import Operador, Unidad
from domain.repositorios import (
    IClienteRepository,
    ICotizacionRepository,
    IOperadorRepository,
    IOrdenServicioRepository,
    IUnidadRepository,
)
from domain.valores import (
    Asignacion,
    Capacidad,
    Destinatario,
    Dimensiones,
    Evidencia,
    EventoAsociado,
    Horario,
    Mercancia,
    Peso,
    SolicitudDeCotizacion,
    TipoDeEvidencia,
    Ubicacion,
    Volumen,
)

from . import tablas as t


def a_utc(valor: datetime | None) -> datetime | None:
    """Normaliza a UTC antes de guardar (SQLite no conserva la zona horaria)."""
    if valor is None:
        return None
    return valor.astimezone(timezone.utc) if valor.tzinfo else valor.replace(tzinfo=timezone.utc)


def de_utc(valor: datetime | None) -> datetime | None:
    return a_utc(valor)


def _no_encontrado(que: str, id: str) -> EntidadNoEncontrada:
    return EntidadNoEncontrada(f"No existe {que} con identificador {id}.")


def _existe(sesion: Session, tabla, id: str) -> bool:
    return sesion.execute(select(tabla.c.id).where(tabla.c.id == id)).first() is not None


def _upsert(sesion: Session, tabla, id: str, valores: dict) -> None:
    if _existe(sesion, tabla, id):
        sesion.execute(update(tabla).where(tabla.c.id == id).values(**valores))
    else:
        sesion.execute(insert(tabla).values(id=id, **valores))


# ------------------------- solicitud / mercancía (compartido por cotización y orden) -------------------------
def _valores_de_solicitud(origen: Ubicacion, destino: Ubicacion, m: Mercancia, fecha_requerida) -> dict:
    return dict(
        origen_ciudad=origen.ciudad, origen_direccion=origen.direccion,
        destino_ciudad=destino.ciudad, destino_direccion=destino.direccion,
        mercancia_descripcion=m.descripcion, mercancia_peso_kg=m.peso.kilogramos,
        mercancia_largo_m=m.dimensiones.largo_m, mercancia_ancho_m=m.dimensiones.ancho_m,
        mercancia_alto_m=m.dimensiones.alto_m, mercancia_caracteristicas=m.caracteristicas_especiales,
        mercancia_alto_valor=m.alto_valor, fecha_requerida=fecha_requerida,
    )


def _mercancia(fila) -> Mercancia:
    return Mercancia(
        descripcion=fila.mercancia_descripcion, peso=Peso(fila.mercancia_peso_kg),
        dimensiones=Dimensiones(fila.mercancia_largo_m, fila.mercancia_ancho_m, fila.mercancia_alto_m),
        caracteristicas_especiales=fila.mercancia_caracteristicas, alto_valor=bool(fila.mercancia_alto_valor),
    )


class SqlClienteRepository(IClienteRepository):
    def __init__(self, sesion: Session):
        self._s = sesion

    def obtener_por_id(self, id: str) -> Cliente:
        f = self._s.execute(select(t.clientes).where(t.clientes.c.id == id)).first()
        if f is None:
            raise _no_encontrado("el cliente", id)
        return Cliente(f.id, f.nombre, f.ciudad)

    def existe(self, id: str) -> bool:
        return _existe(self._s, t.clientes, id)

    def guardar(self, cliente: Cliente) -> None:
        _upsert(self._s, t.clientes, cliente.id, dict(nombre=cliente.nombre, ciudad=cliente.ciudad))


class SqlUnidadRepository(IUnidadRepository):
    def __init__(self, sesion: Session):
        self._s = sesion

    def obtener_por_id(self, id: str) -> Unidad:
        f = self._s.execute(select(t.unidades).where(t.unidades.c.id == id)).first()
        if f is None:
            raise _no_encontrado("la unidad", id)
        return Unidad(f.id, f.tipo, Capacidad(Peso(f.peso_kg), Volumen(f.volumen_m3)))

    def existe(self, id: str) -> bool:
        return _existe(self._s, t.unidades, id)

    def guardar(self, unidad: Unidad) -> None:
        _upsert(self._s, t.unidades, unidad.id, dict(
            tipo=unidad.tipo, peso_kg=unidad.capacidad.peso.kilogramos,
            volumen_m3=unidad.capacidad.volumen.metros_cubicos))


class SqlOperadorRepository(IOperadorRepository):
    def __init__(self, sesion: Session):
        self._s = sesion

    def obtener_por_id(self, id: str) -> Operador:
        f = self._s.execute(select(t.operadores).where(t.operadores.c.id == id)).first()
        if f is None:
            raise _no_encontrado("el operador", id)
        return Operador(f.id, f.nombre, bool(f.disponible))

    def existe(self, id: str) -> bool:
        return _existe(self._s, t.operadores, id)

    def guardar(self, operador: Operador) -> None:
        _upsert(self._s, t.operadores, operador.id,
                dict(nombre=operador.nombre, disponible=operador.esta_disponible()))


class SqlCotizacionRepository(ICotizacionRepository):
    def __init__(self, sesion: Session):
        self._s = sesion

    def obtener_por_id(self, id: str) -> Cotizacion:
        f = self._s.execute(select(t.cotizaciones).where(t.cotizaciones.c.id == id)).first()
        if f is None:
            raise _no_encontrado("la cotización", id)
        solicitud = SolicitudDeCotizacion(
            origen=Ubicacion(f.origen_ciudad, f.origen_direccion),
            destino=Ubicacion(f.destino_ciudad, f.destino_direccion),
            mercancia=_mercancia(f), fecha_requerida=f.fecha_requerida,
        )
        importe = Decimal(f.importe_mxn) if f.importe_mxn is not None else None
        return Cotizacion(f.id, f.cliente_id, solicitud, importe, EstadoCotizacion(f.estado))

    def guardar(self, c: Cotizacion) -> None:
        s = c.solicitud
        valores = dict(cliente_id=c.cliente_id, estado=c.estado.value, importe_mxn=c.importe_mxn,
                       **_valores_de_solicitud(s.origen, s.destino, s.mercancia, s.fecha_requerida))
        _upsert(self._s, t.cotizaciones, c.id, valores)


class SqlOrdenServicioRepository(IOrdenServicioRepository):
    def __init__(self, sesion: Session):
        self._s = sesion

    # ------------------------------ lectura ------------------------------
    def obtener_por_id(self, id: str) -> OrdenDeServicio:
        s = self._s
        f = s.execute(select(t.ordenes).where(t.ordenes.c.id == id)).first()
        if f is None:
            raise _no_encontrado("la orden de servicio", id)
        historial = [
            EntradaDeHistorial(de_utc(h.fecha), h.descripcion, EstadoServicio(h.estado_resultante), h.registrado_por)
            for h in s.execute(select(t.historial).where(t.historial.c.orden_id == id)
                               .order_by(t.historial.c.posicion))
        ]
        evidencias = list(s.execute(select(t.evidencias).where(t.evidencias.c.orden_id == id)
                                    .order_by(t.evidencias.c.id)))
        def evidencia(e) -> Evidencia:
            return Evidencia(TipoDeEvidencia(e.tipo), e.referencia, de_utc(e.fecha), EventoAsociado(e.evento_asociado))
        incidencias = []
        for i in s.execute(select(t.incidencias).where(t.incidencias.c.orden_id == id)
                           .order_by(t.incidencias.c.numero)):
            incidencias.append(Incidencia(
                i.numero, TipoDeIncidencia(i.tipo), i.descripcion, de_utc(i.fecha_registro),
                [evidencia(e) for e in evidencias
                 if e.categoria == "INCIDENCIA" and e.incidencia_numero == i.numero]))
        cancelacion = (Cancelacion(f.cancelacion_solicitado_por, f.cancelacion_motivo, de_utc(f.cancelacion_fecha))
                       if f.cancelacion_fecha is not None else None)
        cambio = (CambioOperativo(f.cambio_solicitado_por, f.cambio_descripcion, de_utc(f.cambio_fecha))
                  if f.cambio_fecha is not None else None)
        asignacion = (Asignacion(f.asignacion_unidad_id, f.asignacion_operador_id)
                      if f.asignacion_unidad_id is not None else None)
        return OrdenDeServicio.restaurar(
            id=f.id, cotizacion_id=f.cotizacion_id, cliente_id=f.cliente_id,
            origen=Ubicacion(f.origen_ciudad, f.origen_direccion),
            destino=Ubicacion(f.destino_ciudad, f.destino_direccion),
            mercancia=_mercancia(f), ruta=f.ruta, horario_recoleccion=Horario(de_utc(f.horario_recoleccion)),
            fecha_requerida=f.fecha_requerida, estado=EstadoServicio(f.estado),
            alto_valor_autorizado=bool(f.alto_valor_autorizado), asignacion=asignacion,
            destinatario=Destinatario(f.destinatario) if f.destinatario else None,
            fecha_entrega=de_utc(f.fecha_entrega), cancelacion=cancelacion, cambio_pendiente=cambio,
            historial=historial, incidencias=incidencias,
            evidencias_recepcion=[evidencia(e) for e in evidencias if e.categoria == "RECEPCION"],
            evidencias_entrega=[evidencia(e) for e in evidencias if e.categoria == "ENTREGA"],
        )

    # ------------------------------ escritura ------------------------------
    def guardar(self, o: OrdenDeServicio) -> None:
        s = self._s
        c, cb = o.cancelacion, o.cambio_pendiente
        valores = dict(
            cotizacion_id=o.cotizacion_id, cliente_id=o.cliente_id, estado=o.estado_actual().value, ruta=o.ruta,
            horario_recoleccion=a_utc(o.horario_recoleccion.inicio),
            alto_valor_autorizado=o.alto_valor_autorizado,
            asignacion_unidad_id=o.asignacion.unidad_id if o.asignacion else None,
            asignacion_operador_id=o.asignacion.operador_id if o.asignacion else None,
            destinatario=o.destinatario.identificacion if o.destinatario else None,
            fecha_entrega=a_utc(o.fecha_entrega),
            cancelacion_solicitado_por=c.solicitado_por if c else None,
            cancelacion_motivo=c.motivo if c else None, cancelacion_fecha=a_utc(c.fecha) if c else None,
            cambio_solicitado_por=cb.solicitado_por if cb else None,
            cambio_descripcion=cb.descripcion if cb else None, cambio_fecha=a_utc(cb.fecha) if cb else None,
            **_valores_de_solicitud(o.origen, o.destino, o.mercancia, o.fecha_requerida),
        )
        _upsert(s, t.ordenes, o.id, valores)
        # Los hijos pertenecen al agregado: se reescriben completos (son pocos y se guardan en la misma transacción).
        for tabla in (t.historial, t.incidencias, t.evidencias):
            s.execute(delete(tabla).where(tabla.c.orden_id == o.id))
        if o.historial:
            s.execute(insert(t.historial), [
                dict(orden_id=o.id, posicion=n, fecha=a_utc(h.fecha), descripcion=h.descripcion,
                     estado_resultante=h.estado_resultante.value, registrado_por=h.registrado_por)
                for n, h in enumerate(o.historial)])
        filas_evidencia = [self._fila_evidencia(o.id, "RECEPCION", None, e) for e in o.evidencias_recepcion]
        filas_evidencia += [self._fila_evidencia(o.id, "ENTREGA", None, e) for e in o.evidencias_entrega]
        for i in o.incidencias:
            s.execute(insert(t.incidencias).values(orden_id=o.id, numero=i.id, tipo=i.tipo.value,
                                                   descripcion=i.descripcion, fecha_registro=a_utc(i.fecha_registro)))
            filas_evidencia += [self._fila_evidencia(o.id, "INCIDENCIA", i.id, e) for e in i.evidencias]
        if filas_evidencia:
            s.execute(insert(t.evidencias), filas_evidencia)

    @staticmethod
    def _fila_evidencia(orden_id: str, categoria: str, numero: int | None, e: Evidencia) -> dict:
        return dict(orden_id=orden_id, categoria=categoria, incidencia_numero=numero, tipo=e.tipo.value,
                    referencia=e.referencia, fecha=a_utc(e.fecha), evento_asociado=e.evento_asociado.value)
