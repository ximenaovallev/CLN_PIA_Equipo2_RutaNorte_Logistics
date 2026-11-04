"""Contratos HTTP (pydantic). Son el borde de la API: se traducen a Commands/Queries y nunca llegan al dominio."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from domain.orden_de_servicio import TipoDeIncidencia
from domain.valores import (
    Destinatario, Dimensiones, Evidencia, EventoAsociado, Mercancia, Peso, SolicitudDeCotizacion, TipoDeEvidencia,
    Ubicacion,
)


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _ejemplo(**datos):
    """Ejemplo que Swagger muestra ya escrito en el formulario («Try it out»)."""
    return ConfigDict(json_schema_extra={"examples": [datos]})


_UBI_ORIGEN = {"ciudad": "Monterrey", "direccion": "Av. Industria 100, Parque Industrial"}
_UBI_DESTINO = {"ciudad": "Querétaro", "direccion": "Calle Parque 5, Zona Industrial"}
_MERCANCIA = {"descripcion": "Refacciones automotrices", "peso_kg": 800, "largo_m": 2, "ancho_m": 1.5,
              "alto_m": 1.5, "caracteristicas_especiales": "", "alto_valor": False}
_SOLICITUD = {"origen": _UBI_ORIGEN, "destino": _UBI_DESTINO, "mercancia": _MERCANCIA, "fecha_requerida": "2026-12-01"}
_EVIDENCIA = {"tipo": "FOTOGRAFIA", "referencia": "https://ejemplo.com/fotos/entrega-001.jpg"}


# ----------------------------- entrada -----------------------------
class ClienteIn(_Base):
    """Datos para dar de alta a un cliente."""
    model_config = _ejemplo(id="CLI-001", nombre="Refacciones del Norte S.A. de C.V.", ciudad="Monterrey")
    id: str = Field(description="Código que usted le inventa al cliente (no se puede repetir). Ejemplo: CLI-001", examples=["CLI-001"])
    nombre: str = Field(description="Nombre del cliente o de su empresa", examples=["Refacciones del Norte S.A. de C.V."])
    ciudad: str = Field(default="", description="Ciudad donde está el cliente (opcional)", examples=["Monterrey"])


class UnidadIn(_Base):
    """Datos para dar de alta un camión o vehículo de carga."""
    model_config = _ejemplo(id="UNI-001", tipo="Camión torton", peso_kg=8000, volumen_m3=40)
    id: str = Field(description="Código de la unidad (no se puede repetir). Ejemplo: UNI-001", examples=["UNI-001"])
    tipo: str = Field(description="Tipo de vehículo", examples=["Camión torton"])
    peso_kg: float = Field(description="Cuántos kilos puede cargar como máximo", examples=[8000])
    volumen_m3: float = Field(description="Cuántos metros cúbicos de carga le caben como máximo", examples=[40])


class OperadorIn(_Base):
    """Datos para dar de alta a un operador (conductor)."""
    model_config = _ejemplo(id="OPE-001", nombre="Luis Pérez", disponible=True)
    id: str = Field(description="Código del operador (no se puede repetir). Ejemplo: OPE-001", examples=["OPE-001"])
    nombre: str = Field(description="Nombre completo del operador", examples=["Luis Pérez"])
    disponible: bool = Field(default=True, description="¿Puede recibir trabajo ahora? true = sí, false = no", examples=[True])


class DisponibilidadIn(_Base):
    """Indica si el operador puede recibir trabajo."""
    model_config = _ejemplo(disponible=False)
    disponible: bool = Field(description="true = disponible, false = no disponible (vacaciones, descanso, enfermo…)", examples=[False])


class UbicacionIn(_Base):
    """Un lugar: ciudad y dirección."""
    ciudad: str = Field(description="Ciudad", examples=["Monterrey"])
    direccion: str = Field(default="", description="Calle, número y colonia o parque industrial", examples=["Av. Industria 100"])


class MercanciaIn(_Base):
    """Lo que se va a transportar."""
    descripcion: str = Field(description="Qué se va a transportar, con palabras sencillas", examples=["Refacciones automotrices"])
    peso_kg: float = Field(description="Peso total en kilos. Debe ser mayor que cero", examples=[800])
    largo_m: float = Field(description="Largo de la carga en metros", examples=[2])
    ancho_m: float = Field(description="Ancho de la carga en metros", examples=[1.5])
    alto_m: float = Field(description="Alto de la carga en metros", examples=[1.5])
    caracteristicas_especiales: str = Field(default="", description="Cuidados especiales: frágil, refrigerada, etc. (opcional)", examples=["Frágil"])
    alto_valor: bool = Field(default=False, description="¿Es una carga de mucho valor? true = sí (requerirá autorización de Operaciones), false = no", examples=[False])


class SolicitudIn(_Base):
    """Todo lo que el cliente pide: de dónde a dónde, qué lleva y para cuándo."""
    model_config = _ejemplo(**_SOLICITUD)
    origen: UbicacionIn = Field(description="Dónde se recoge la mercancía")
    destino: UbicacionIn = Field(description="Dónde se entrega la mercancía")
    mercancia: MercanciaIn = Field(description="Qué se transporta")
    fecha_requerida: date = Field(description="Fecha en que el cliente necesita la entrega. Formato AAAA-MM-DD", examples=["2026-12-01"])

    def a_dominio(self) -> SolicitudDeCotizacion:
        m = self.mercancia
        return SolicitudDeCotizacion(
            origen=Ubicacion(self.origen.ciudad, self.origen.direccion),
            destino=Ubicacion(self.destino.ciudad, self.destino.direccion),
            mercancia=Mercancia(m.descripcion, Peso(m.peso_kg), Dimensiones(m.largo_m, m.ancho_m, m.alto_m),
                                m.caracteristicas_especiales, m.alto_valor),
            fecha_requerida=self.fecha_requerida,
        )


class CotizacionIn(_Base):
    """Petición de cotización de un cliente ya registrado."""
    model_config = _ejemplo(cliente_id="CLI-001", solicitud=_SOLICITUD)
    cliente_id: str = Field(description="Código del cliente (el mismo con que se registró)", examples=["CLI-001"])
    solicitud: SolicitudIn = Field(description="Lo que el cliente quiere transportar")


class ImporteIn(_Base):
    """Precio de la cotización."""
    model_config = _ejemplo(importe_mxn="12500.00")
    importe_mxn: Decimal = Field(description="Precio en pesos mexicanos. Debe ser mayor que cero. Ejemplo: 12500.00", examples=["12500.00"])


class RespuestaIn(_Base):
    """Lo que contesta el cliente."""
    model_config = _ejemplo(respuesta="ACEPTA")
    respuesta: Literal["ACEPTA", "RECHAZA"] = Field(description="ACEPTA si está de acuerdo con el precio; RECHAZA si no", examples=["ACEPTA"])


class OrdenIn(_Base):
    """Datos para crear la orden de servicio de una cotización aceptada."""
    model_config = _ejemplo(cotizacion_id="PEGUE-AQUÍ-EL-NÚMERO-DE-COTIZACIÓN", ruta="MTY-QRO",
                            horario_recoleccion="2026-11-20T08:00:00Z")
    cotizacion_id: str = Field(description="Número de la cotización ya ACEPTADA (lo recibió al pedir la cotización)")
    ruta: str = Field(description="Nombre corto de la ruta. Ejemplo: MTY-QRO (Monterrey a Querétaro)", examples=["MTY-QRO"])
    horario_recoleccion: datetime = Field(description="Día y hora en que se recogerá la mercancía. Formato: 2026-11-20T08:00:00Z", examples=["2026-11-20T08:00:00Z"])


class AsignacionIn(_Base):
    """Qué camión y qué operador harán el servicio."""
    model_config = _ejemplo(unidad_id="UNI-001", operador_id="OPE-001")
    unidad_id: str = Field(description="Código de la unidad de transporte (ya registrada)", examples=["UNI-001"])
    operador_id: str = Field(description="Código del operador (ya registrado y disponible)", examples=["OPE-001"])


class EvidenciaIn(_Base):
    """Comprobante del hecho: una foto o un documento."""
    model_config = _ejemplo(**_EVIDENCIA)
    tipo: TipoDeEvidencia = Field(default=TipoDeEvidencia.FOTOGRAFIA, description="FOTOGRAFIA o DOCUMENTO", examples=["FOTOGRAFIA"])
    referencia: str = Field(description="Dirección web (enlace) o folio de la foto o del documento", examples=["https://ejemplo.com/fotos/entrega-001.jpg"])
    fecha: datetime | None = Field(default=None, description="Fecha y hora de la evidencia (opcional; si no la pone, se usa la de ahora)")

    def a_dominio(self, evento: EventoAsociado) -> Evidencia:
        return Evidencia(self.tipo, self.referencia, self.fecha or datetime.now(timezone.utc), evento)


class RecepcionIn(_Base):
    """Comprobante de que el operador recibió la mercancía."""
    model_config = _ejemplo(evidencia=_EVIDENCIA)
    evidencia: EvidenciaIn = Field(description="Foto o documento de la mercancía recibida")


class EntregaIn(_Base):
    """Datos de la entrega. Si algo impidió entregar, indique el problema en «incidencia»."""
    model_config = _ejemplo(destinatario="INE-123456", evidencia=_EVIDENCIA)
    destinatario: str | None = Field(default=None, description="Identificación de la persona que recibe (por ejemplo, número de INE)", examples=["INE-123456"])
    evidencia: EvidenciaIn = Field(description="Foto o documento de la entrega")
    incidencia: TipoDeIncidencia | None = Field(default=None, description="Déjelo vacío si la entrega salió bien. Si NO se pudo entregar, elija el motivo")
    descripcion_incidencia: str = Field(default="", description="Si hubo problema, explique con sus palabras qué pasó", examples=["No había nadie para recibir"])

    def destinatario_de_dominio(self) -> Destinatario | None:
        return Destinatario(self.destinatario) if self.destinatario is not None else None


class IncidenciaIn(_Base):
    """Un problema durante el servicio (retraso, avería, etc.)."""
    model_config = _ejemplo(tipo="RETRASO", descripcion="Tráfico pesado en la carretera, llegaremos 2 horas tarde")
    tipo: TipoDeIncidencia = Field(description="Qué clase de problema es", examples=["RETRASO"])
    descripcion: str = Field(description="Explique con sus palabras qué pasó", examples=["Tráfico pesado en la carretera"])
    evidencia: EvidenciaIn | None = Field(default=None, description="Foto o documento que lo compruebe (opcional)")


class AutorizacionAltoValorIn(_Base):
    """Quién autoriza que se transporte una carga de mucho valor."""
    model_config = _ejemplo(autorizado_por="Operaciones")
    autorizado_por: str = Field(description="Nombre de la persona o del área que autoriza", examples=["Operaciones"])


class CancelacionIn(_Base):
    """Datos para cancelar un servicio."""
    model_config = _ejemplo(solicitado_por="Cliente CLI-001", motivo="El cliente ya no necesita el envío",
                            rol_que_autoriza="Operaciones")
    solicitado_por: str = Field(description="Quién pide la cancelación", examples=["Cliente CLI-001"])
    motivo: str = Field(description="Por qué se cancela, con sus palabras", examples=["El cliente ya no necesita el envío"])
    rol_que_autoriza: str = Field(default="Operaciones", description="Área que autoriza la cancelación (normalmente Operaciones)", examples=["Operaciones"])


class CambioOperativoIn(_Base):
    """Un cambio que afecta cómo se hará el servicio."""
    model_config = _ejemplo(solicitado_por="Cliente CLI-001", descripcion="Cambiar la hora de recolección a las 10:00")
    solicitado_por: str = Field(description="Quién pide el cambio", examples=["Cliente CLI-001"])
    descripcion: str = Field(description="Qué se quiere cambiar", examples=["Cambiar la hora de recolección a las 10:00"])


class RevisionDeCambioIn(_Base):
    """Decisión de Operaciones sobre un cambio pedido."""
    model_config = _ejemplo(revisado_por="Operaciones", aprobado=True, comentario="Se puede mover el horario")
    revisado_por: str = Field(description="Quién revisa el cambio", examples=["Operaciones"])
    aprobado: bool = Field(description="true = se aprueba el cambio, false = se rechaza", examples=[True])
    comentario: str = Field(default="", description="Explicación opcional de la decisión", examples=["Se puede mover el horario"])


# ----------------------------- salida -----------------------------
class ErrorOut(BaseModel):
    """Lo que la API contesta cuando algo no se pudo hacer. Siempre explica el problema y qué hacer."""
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "codigo": "TransicionDeEstadoInvalida",
        "mensaje": "No se puede registrar la entrega: el servicio está con la mercancía recolectada. Para hacerlo, el servicio debe estar llegado al destino.",
        "que_hacer": "Consulte en qué paso va la orden («Consultar el estado de una orden») y siga los pasos en orden."}]})
    codigo: str = Field(description="Nombre corto del problema (sirve para soporte técnico; no necesita entenderlo)")
    mensaje: str = Field(description="Qué pasó, explicado con palabras sencillas")
    que_hacer: str = Field(description="Qué puede hacer usted para resolverlo")


class OperacionOut(BaseModel):
    """Lo que la API contesta cuando todo salió bien."""
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "mensaje": "Listo: el cliente quedó registrado con el código CLI-001.",
        "que_sigue": "Ahora puede pedir una cotización para este cliente (sección «2. Cotizaciones»).",
        "datos": {"cliente_id": "CLI-001"}}]})
    mensaje: str = Field(description="Qué se hizo, explicado con palabras sencillas")
    que_sigue: str = Field(default="", description="Cuál es el siguiente paso recomendado")
    datos: dict = Field(default_factory=dict, description="Números y códigos que conviene guardar (por ejemplo, el número de cotización)")


class EstadoDeEntidad(str, Enum):
    ok = "ok"
