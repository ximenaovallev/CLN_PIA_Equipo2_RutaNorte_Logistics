"""El lenguaje que ve el usuario: claro, sin términos técnicos y siempre con «qué hacer»."""
import pytest

from api import lenguaje as l

OPERACIONES = ["registrar_cliente", "registrar_unidad", "registrar_operador", "cambiar_disponibilidad",
               "solicitar_cotizacion", "elaborar_cotizacion", "modificar_cotizacion", "responder_cotizacion",
               "generar_orden", "asignar_recursos", "autorizar_alto_valor", "registrar_recepcion",
               "iniciar_traslado", "registrar_llegada", "registrar_entrega", "registrar_incidencia",
               "cancelar_servicio", "solicitar_cambio", "revisar_cambio"]


@pytest.mark.parametrize("operacion", OPERACIONES)
def test_toda_operacion_correcta_dice_que_paso_y_que_sigue(operacion):
    mensaje, que_sigue = l.exito(operacion, {"estado": "ENTREGADO", "cliente_id": "C", "disponible": True})
    assert mensaje and que_sigue
    assert not any(token in mensaje + que_sigue for token in l.ESTADOS)


def test_respuestas_que_dependen_del_resultado():
    assert "aceptada" in l.exito("responder_cotizacion", {"estado": "ACEPTADA"})[0]
    assert "rechazada" in l.exito("responder_cotizacion", {"estado": "RECHAZADA"})[0]
    assert "Entrega completada" in l.exito("registrar_entrega", {"estado": "ENTREGADO"})[0]
    assert "no se pudo completar" in l.exito("registrar_entrega", {"estado": "LLEGADA_A_DESTINO"})[0]
    assert "NO disponible" in l.exito("cambiar_disponibilidad", {"disponible": False})[0]
    assert l.exito("otra", {})[0]


def test_estados_en_palabras_y_mensajes_de_error_conocidos():
    assert l.estado_en_palabras("EN_TRANSITO") == "en camino"
    assert l.estado_en_palabras("DESCONOCIDO") == "desconocido"
    texto, que_hacer = l.error("ControlDeAltoValorPendiente", "La carga es de alto valor y está en CONFIRMADO.")
    assert "confirmado" in texto and que_hacer
    assert l.error("ErrorInventado", "Algo pasó")[1]


@pytest.mark.parametrize("error,esperado", [
    ({"loc": ("body", "id"), "type": "missing"}, "Falta completar el dato «código»."),
    ({"loc": ("body", "x"), "type": "extra_forbidden"}, "no corresponde a este formulario"),
    ({"loc": ("body", "tipo"), "type": "enum", "ctx": {"expected": "'A' or 'B'"}}, "Opciones permitidas: 'A' or 'B'"),
    ({"loc": ("body", "nombre"), "type": "string_type"}, "debe ser un texto"),
    ({"loc": ("body", "peso_kg"), "type": "float_parsing"}, "debe ser un número"),
    ({"loc": ("body", "peso_kg"), "type": "greater_than", "ctx": {"gt": 0}}, "mayor que 0"),
    ({"loc": ("body", "peso_kg"), "type": "less_than", "ctx": {"lt": 9}}, "menor que 9"),
    ({"loc": ("body", "disponible"), "type": "bool_parsing"}, "verdadero (true) o falso (false)"),
    ({"loc": ("body", "fecha_requerida"), "type": "date_from_datetime_parsing"}, "AAAA-MM-DD"),
    ({"loc": ("body", "horario_recoleccion"), "type": "datetime_parsing"}, "2026-11-20T08:00:00Z"),
    ({"loc": ("body",), "type": "json_invalid"}, "no tiene el formato correcto"),
    ({"loc": ("query", "limite"), "type": "raro", "msg": "algo"}, "«límite» no es válido"),
])
def test_cada_tipo_de_dato_mal_escrito_se_explica_en_palabras(error, esperado):
    assert esperado in l.validacion([error])[0]


def test_varios_datos_por_corregir_se_numeran():
    texto, que_hacer = l.validacion([{"loc": ("body", "id"), "type": "missing"}, {"loc": ("body", "nombre"), "type": "missing"}])
    assert texto.startswith("Hay 2 datos por corregir: (1)") and "(2)" in texto and "Execute" in que_hacer


def test_direcciones_que_no_existen():
    assert "No existe esa dirección" in l.http(404, "Not Found")[0]
    assert "no está permitida" in l.http(405, "x")[0]
    assert l.http(500, "falló")[0] == "falló"
