"""Lenguaje sencillo para quien usa la API (clientes, vendedores, operadores): ningún mensaje debe exigir
saber de programación. El dominio y los casos de uso conservan sus mensajes técnicos; este módulo, que vive en
el borde de la API, los traduce a frases claras y agrega siempre «qué hacer ahora»."""
from __future__ import annotations

import re

# ----------------------------- nombres en palabras -----------------------------
ESTADOS = {
    "SOLICITADO": "solicitado (esperando que Ventas ponga el precio)",
    "COTIZADO": "cotizado (ya tiene precio)",
    "CONFIRMADO": "confirmado",
    "UNIDAD_ASIGNADA": "con unidad y operador asignados",
    "RECOLECTADO": "con la mercancía recolectada",
    "EN_TRANSITO": "en camino",
    "LLEGADA_A_DESTINO": "llegado al destino",
    "ENTREGADO": "entregado",
    "CANCELADO": "cancelado",
    "EN_PROCESO": "en proceso",
    "ACEPTADA": "aceptada",
    "RECHAZADA": "rechazada",
}
_TOKENS = re.compile(r"\b(" + "|".join(sorted(ESTADOS, key=len, reverse=True)) + r")\b")


def estado_en_palabras(estado: str | None) -> str:
    return ESTADOS.get(estado or "", (estado or "").lower().replace("_", " "))


def _en_palabras(texto: str) -> str:
    return _TOKENS.sub(lambda m: ESTADOS[m.group(1)], texto)


# ----------------------------- respuestas correctas -----------------------------
def _d(datos: dict, clave: str, defecto: str = "") -> str:
    return str(datos.get(clave, defecto))


def exito(operacion: str, datos: dict) -> tuple[str, str]:
    """Devuelve (mensaje, que_sigue) para una operación que salió bien."""
    estado = _d(datos, "estado")
    if operacion == "registrar_cliente":
        return (f"Listo: el cliente quedó registrado con el código {_d(datos, 'cliente_id')}.",
                "Ahora puede pedir una cotización para este cliente (sección «2. Cotizaciones»).")
    if operacion == "registrar_unidad":
        return (f"Listo: la unidad de transporte quedó registrada con el código {_d(datos, 'unidad_id')}.",
                "Ya puede asignarla a una orden de servicio cuando la necesite.")
    if operacion == "registrar_operador":
        return (f"Listo: el operador quedó registrado con el código {_d(datos, 'operador_id')}.",
                "Ya puede asignarlo a una orden de servicio cuando la necesite.")
    if operacion == "cambiar_disponibilidad":
        disp = datos.get("disponible")
        return ("El operador quedó marcado como " + ("DISPONIBLE." if disp else "NO disponible."),
                "Solo los operadores disponibles pueden asignarse a una orden de servicio.")
    if operacion == "solicitar_cotizacion":
        return (f"Recibimos la solicitud de cotización. Su número de cotización es {_d(datos, 'cotizacion_id')}. "
                "Guárdelo: lo necesitará en los siguientes pasos.",
                "Ventas debe ponerle precio (sección «2. Cotizaciones» → «Poner el precio a la cotización»).")
    if operacion == "elaborar_cotizacion":
        return ("La cotización ya tiene precio y está lista para que el cliente la acepte o la rechace.",
                "El cliente debe responder (sección «2. Cotizaciones» → «El cliente acepta o rechaza la cotización»).")
    if operacion == "modificar_cotizacion":
        return ("Los datos de la solicitud se actualizaron. Como cambiaron, hay que calcular el precio de nuevo.",
                "Ventas debe volver a poner el precio de la cotización.")
    if operacion == "responder_cotizacion":
        if estado == "ACEPTADA":
            return ("¡Cotización aceptada! El cliente está de acuerdo con el precio.",
                    "Ya se puede crear la orden de servicio (sección «3. Órdenes de servicio» → «Crear la orden»).")
        return ("La cotización fue rechazada. No se creará ninguna orden de servicio con ella.",
                "Si el cliente cambia de opinión, puede pedir una cotización nueva.")
    if operacion == "generar_orden":
        return (f"La orden de servicio fue creada y quedó confirmada. Su número de orden es {_d(datos, 'orden_id')}. "
                "Guárdelo: lo necesitará en los siguientes pasos.",
                "Operaciones debe asignar una unidad de transporte y un operador.")
    if operacion == "asignar_recursos":
        return ("Se asignaron la unidad de transporte y el operador a la orden.",
                "Cuando el operador recoja la mercancía, registre la recepción con una foto o documento.")
    if operacion == "autorizar_alto_valor":
        return ("La carga de alto valor quedó autorizada.",
                "Ahora ya se puede asignar la unidad de transporte y el operador.")
    if operacion == "registrar_recepcion":
        return ("Se registró que la mercancía fue recibida y revisada. La orden pasó a «mercancía recolectada».",
                "Cuando salga el camión, indique que el traslado comenzó.")
    if operacion == "iniciar_traslado":
        return ("El traslado comenzó: la mercancía va en camino.",
                "Si surge un problema en el camino, regístrelo como incidencia. Al llegar, registre la llegada.")
    if operacion == "registrar_llegada":
        return ("Se registró que la unidad llegó al destino.",
                "Registre la entrega: quién recibe y una foto o documento como evidencia.")
    if operacion == "registrar_entrega":
        if estado == "ENTREGADO":
            return ("¡Entrega completada! La mercancía fue entregada y quedó registrada con su evidencia.",
                    "No hace falta hacer nada más. Puede revisar el historial en «Consultar el estado de una orden».")
        return ("La entrega no se pudo completar. Se registró el problema para que Operaciones lo atienda.",
                "Operaciones debe resolver la incidencia con el cliente. La orden sigue abierta.")
    if operacion == "registrar_incidencia":
        return ("Se registró el problema. El estado del servicio no cambia; Operaciones podrá verlo.",
                "Puede seguir con el servicio con normalidad.")
    if operacion == "cancelar_servicio":
        return ("El servicio fue cancelado. Quedó anotado quién lo pidió y por qué.",
                "Esta orden ya no puede continuar. Si el cliente aún necesita el envío, debe pedir una cotización nueva.")
    if operacion == "solicitar_cambio":
        return ("Se registró la solicitud de cambio. Mientras Operaciones no la revise, el servicio no puede avanzar.",
                "Operaciones debe revisar el cambio (sección «3. Órdenes de servicio» → «Revisar un cambio solicitado»).")
    if operacion == "revisar_cambio":
        return ("El cambio fue revisado. El servicio ya puede continuar.",
                "Siga con el paso que correspondía en la orden.")
    return ("La operación se realizó correctamente.", "")


# ----------------------------- errores de negocio -----------------------------
_QUE_HACER = {
    "DatosInvalidos": "Corrija el dato que se indica y vuelva a intentarlo.",
    "EntidadNoEncontrada": "Revise que el código esté bien escrito. Si todavía no lo registra, hágalo primero.",
    "EntidadYaExiste": "Use un código distinto (por ejemplo, agregue un número al final) y vuelva a intentarlo.",
    "TransicionDeEstadoInvalida": "Consulte en qué paso va la orden («Consultar el estado de una orden») y siga los pasos en orden.",
    "CotizacionNoModificable": "Solo se puede cambiar una cotización que todavía está en proceso. Si hace falta otra, pida una cotización nueva.",
    "CotizacionNoElaborada": "Primero Ventas debe ponerle precio («Poner el precio a la cotización»).",
    "OrdenNoGenerable": "Primero el cliente debe aceptar la cotización («El cliente acepta o rechaza la cotización»).",
    "RecursosNoDisponibles": "Elija otra unidad u otro operador, o espere a que el operador esté disponible.",
    "ControlDeAltoValorPendiente": "Primero autorice la carga de alto valor («Autorizar una carga de alto valor»).",
    "SinAutoridadParaCancelar": "Pida a una persona del área autorizada que confirme la cancelación.",
    "CambioPendienteDeRevision": "Operaciones debe revisar el cambio pendiente antes de seguir («Revisar un cambio solicitado»).",
}
_POR_DEFECTO = "Revise el mensaje, corrija lo que haga falta y vuelva a intentarlo."

_TRANSICION = re.compile(r"No se puede (?P<que>.+?) en estado (?P<estado>[A-Z_]+) \(se requiere (?P<req>.+?)\)\.?$")
_COT_NO_MODIF = re.compile(r"No se puede (?P<que>.+?) la cotización (?P<id>\S+): está (?P<estado>[A-Z_]+)\.?$")
_ORDEN_NO_GEN = re.compile(r"La orden solo se genera desde una cotización aceptada \(cotización (?P<id>\S+): (?P<estado>[A-Z_]+)\)\.?$")
_NO_ELAB = re.compile(r"No se puede aceptar la cotización (?P<id>\S+): Ventas aún no la elabora\.?$")


def _lista_de_estados(texto: str) -> str:
    partes = [p for p in re.split(r"\s+o\s+|,\s*", texto) if p]
    return " o ".join(ESTADOS.get(p.strip(), p.strip()) for p in partes)


def error(codigo: str | None, mensaje: str) -> tuple[str, str]:
    """Devuelve (mensaje_claro, que_hacer) para un error de negocio."""
    m = _TRANSICION.match(mensaje)
    if m:
        texto = (f"No se puede {m['que']}: el servicio está {estado_en_palabras(m['estado'])}. "
                 f"Para hacerlo, el servicio debe estar {_lista_de_estados(m['req'])}.")
    elif (m := _COT_NO_MODIF.match(mensaje)):
        texto = (f"No se puede {m['que']} la cotización {m['id']} porque ya está {estado_en_palabras(m['estado'])}. "
                 "Solo se puede cambiar una cotización mientras está en proceso.")
    elif (m := _ORDEN_NO_GEN.match(mensaje)):
        texto = (f"No se puede crear la orden porque la cotización {m['id']} todavía no está aceptada por el cliente "
                 f"(está {estado_en_palabras(m['estado'])}).")
    elif (m := _NO_ELAB.match(mensaje)):
        texto = f"El cliente todavía no puede responder la cotización {m['id']}: Ventas aún no le pone precio."
    else:
        texto = _en_palabras(mensaje)
    return texto, _QUE_HACER.get(codigo or "", _POR_DEFECTO)


# ----------------------------- datos mal escritos (400) -----------------------------
CAMPOS = {
    "id": "código", "nombre": "nombre", "ciudad": "ciudad", "direccion": "dirección", "tipo": "tipo",
    "peso_kg": "peso en kilos", "volumen_m3": "volumen en metros cúbicos", "disponible": "disponibilidad",
    "cliente_id": "código del cliente", "solicitud": "solicitud", "origen": "origen", "destino": "destino",
    "mercancia": "mercancía", "descripcion": "descripción", "largo_m": "largo en metros", "ancho_m": "ancho en metros",
    "alto_m": "alto en metros", "caracteristicas_especiales": "características especiales",
    "alto_valor": "carga de alto valor", "fecha_requerida": "fecha requerida", "importe_mxn": "importe en pesos",
    "respuesta": "respuesta del cliente", "cotizacion_id": "número de cotización", "ruta": "ruta",
    "horario_recoleccion": "horario de recolección", "unidad_id": "código de la unidad",
    "operador_id": "código del operador", "evidencia": "evidencia", "referencia": "referencia de la evidencia",
    "fecha": "fecha", "destinatario": "identificación de quien recibe", "incidencia": "tipo de problema",
    "descripcion_incidencia": "descripción del problema", "autorizado_por": "persona que autoriza",
    "solicitado_por": "persona que lo solicita", "motivo": "motivo", "rol_que_autoriza": "área que autoriza",
    "revisado_por": "persona que revisa", "aprobado": "aprobación", "comentario": "comentario",
    "desde": "fecha inicial", "hasta": "fecha final", "estado": "estado", "limite": "límite",
}


def _campo(loc: tuple) -> str:
    nombres = [CAMPOS.get(str(p), str(p)) for p in loc[1:] if not isinstance(p, int)]
    if not nombres:
        return "datos enviados"
    return " → ".join(nombres[-2:]) if len(nombres) > 1 else nombres[0]


def _frase_de_validacion(e: dict) -> str:
    campo, tipo, ctx = _campo(tuple(e["loc"])), e.get("type", ""), e.get("ctx") or {}
    if tipo == "missing":
        return f"Falta completar el dato «{campo}»."
    if tipo == "extra_forbidden":
        return f"El dato «{campo}» no corresponde a este formulario; quítelo."
    if tipo in ("enum", "literal_error"):
        return f"El valor de «{campo}» no es válido. Opciones permitidas: {ctx.get('expected', 'vea la lista en el formulario')}."
    if tipo in ("string_type", "string_too_short"):
        return f"«{campo}» debe ser un texto" + (" y no puede quedar vacío." if "short" in tipo else ".")
    if tipo in ("int_parsing", "float_parsing", "int_type", "float_type", "decimal_parsing", "decimal_type"):
        return f"«{campo}» debe ser un número (por ejemplo 12500.50), sin letras ni símbolos."
    if tipo in ("greater_than", "greater_than_equal"):
        return f"«{campo}» debe ser un número mayor que {ctx.get('gt', ctx.get('ge', 0))}."
    if tipo in ("less_than", "less_than_equal"):
        return f"«{campo}» debe ser un número menor que {ctx.get('lt', ctx.get('le', ''))}."
    if tipo.startswith("bool"):
        return f"«{campo}» debe ser verdadero (true) o falso (false)."
    if tipo.startswith("datetime"):
        return f"«{campo}» no es una fecha y hora válidas. Escríbala así: 2026-11-20T08:00:00Z."
    if tipo.startswith("date"):
        return f"«{campo}» no es una fecha válida. Escríbala como AAAA-MM-DD, por ejemplo 2026-12-01."
    if tipo in ("json_invalid", "model_attributes_type", "dict_type"):
        return "El mensaje enviado no tiene el formato correcto. Revise que las llaves, comas y comillas estén completas."
    return f"El dato «{campo}» no es válido ({e.get('msg', 'revise su valor')})."


def validacion(errores: list[dict]) -> tuple[str, str]:
    frases = [_frase_de_validacion(e) for e in errores]
    if len(frases) == 1:
        texto = frases[0]
    else:
        texto = f"Hay {len(frases)} datos por corregir: " + " ".join(f"({i}) {f}" for i, f in enumerate(frases, 1))
    return texto, "Corrija lo que se indica y vuelva a pulsar «Execute»."


# ----------------------------- direcciones que no existen -----------------------------
def http(status: int, detalle: str) -> tuple[str, str]:
    if status == 404:
        return ("No existe esa dirección.", "Para ver todo lo que puede hacer, abra la página /docs.")
    if status == 405:
        return ("Esa acción no está permitida en esta dirección.", "Revise en /docs qué acciones tiene cada sección.")
    return (detalle, _POR_DEFECTO)
