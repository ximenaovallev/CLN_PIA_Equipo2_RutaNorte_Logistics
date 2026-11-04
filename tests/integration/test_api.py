"""API REST de extremo a extremo (TestClient): contrato de códigos 200/201/400/404/409/422 y flujo completo."""
import pytest
from fastapi.testclient import TestClient

from api.main import crear_app
from conftest import BACKENDS, crear_app as crear_aplicacion


@pytest.fixture(params=BACKENDS)
def cliente(request):
    return TestClient(crear_app(crear_aplicacion(request.param)))


SOLICITUD = {
    "origen": {"ciudad": "Monterrey", "direccion": "Av. Industria 100"},
    "destino": {"ciudad": "Querétaro", "direccion": "Parque Industrial 5"},
    "mercancia": {"descripcion": "Refacciones", "peso_kg": 800, "largo_m": 2, "ancho_m": 1.5, "alto_m": 1.5},
    "fecha_requerida": "2026-12-01",
}
EVIDENCIA = {"referencia": "foto-001.jpg"}


def _catalogos(c):
    assert c.post("/clientes", json={"id": "CLI-1", "nombre": "Refacciones del Norte", "ciudad": "Monterrey"}).status_code == 201
    assert c.post("/unidades", json={"id": "U-1", "tipo": "Caja seca", "peso_kg": 5000, "volumen_m3": 30}).status_code == 201
    assert c.post("/operadores", json={"id": "OP-1", "nombre": "Luis"}).status_code == 201


def _orden(c, alto_valor=False):
    _catalogos(c) if c.get("/clientes/CLI-1").status_code == 404 else None
    cuerpo = {"cliente_id": "CLI-1", "solicitud": {**SOLICITUD, "mercancia": {**SOLICITUD["mercancia"], "alto_valor": alto_valor}}}
    cot = c.post("/cotizaciones", json=cuerpo).json()["datos"]["cotizacion_id"]
    assert c.put(f"/cotizaciones/{cot}/importe", json={"importe_mxn": "15000.50"}).status_code == 200
    assert c.post(f"/cotizaciones/{cot}/respuesta", json={"respuesta": "ACEPTA"}).status_code == 200
    r = c.post("/ordenes", json={"cotizacion_id": cot, "ruta": "MTY-QRO", "horario_recoleccion": "2026-11-20T08:00:00Z"})
    assert r.status_code == 201
    return r.json()["datos"]["orden_id"]


def test_flujo_completo_desde_la_cotizacion_hasta_la_entrega_y_los_indicadores(cliente):
    oid = _orden(cliente)
    assert cliente.post(f"/ordenes/{oid}/asignacion", json={"unidad_id": "U-1", "operador_id": "OP-1"}).status_code == 200
    assert cliente.post(f"/ordenes/{oid}/recepcion", json={"evidencia": EVIDENCIA}).status_code == 200
    assert cliente.post(f"/ordenes/{oid}/traslado").status_code == 200
    assert cliente.post(f"/ordenes/{oid}/llegada").status_code == 200
    r = cliente.post(f"/ordenes/{oid}/entrega", json={"destinatario": "INE-123", "evidencia": EVIDENCIA})
    assert r.status_code == 200 and r.json()["datos"]["estado"] == "ENTREGADO"
    estado = cliente.get(f"/ordenes/{oid}/estado").json()
    assert estado["estado_actual"] == "ENTREGADO" and estado["acciones_permitidas"] == []
    assert len(estado["eventos"]) >= 6
    assert [o["orden_id"] for o in cliente.get("/ordenes?estado=ENTREGADO").json()] == [oid]
    ind = cliente.get("/indicadores?desde=2020-01-01&hasta=2100-01-01").json()
    assert ind["entregas_realizadas"] == 1 and ind["cumplimiento_de_entregas"] in (0.0, 1.0)


def test_cotizacion_conserva_el_importe_decimal_exacto(cliente):
    _catalogos(cliente)
    cot = cliente.post("/cotizaciones", json={"cliente_id": "CLI-1", "solicitud": SOLICITUD}).json()["datos"]["cotizacion_id"]
    cliente.put(f"/cotizaciones/{cot}/importe", json={"importe_mxn": "0.10"})
    dto = cliente.get(f"/cotizaciones/{cot}").json()
    assert dto["estado_del_servicio"] == "COTIZADO" and float(dto["importe_mxn"]) == pytest.approx(0.10)


def test_400_cuerpo_incompleto_o_valores_invalidos(cliente):
    assert cliente.post("/clientes", json={"nombre": "sin id"}).status_code == 400
    _catalogos(cliente)
    malo = {**SOLICITUD, "mercancia": {**SOLICITUD["mercancia"], "peso_kg": -5}}
    r = cliente.post("/cotizaciones", json={"cliente_id": "CLI-1", "solicitud": malo})
    assert r.status_code == 400 and r.json()["codigo"] == "DatosInvalidos"
    assert cliente.get("/indicadores?desde=2026-02-01&hasta=2026-01-01").status_code == 400
    assert cliente.get("/ordenes?limite=0").status_code == 400


def test_404_recursos_inexistentes(cliente):
    for ruta in ("/clientes/X", "/unidades/X", "/operadores/X", "/cotizaciones/X", "/ordenes/X/estado"):
        r = cliente.get(ruta)
        assert r.status_code == 404 and r.json()["codigo"] == "EntidadNoEncontrada", ruta
    assert cliente.post("/ordenes/X/traslado").status_code == 404


def test_409_duplicado_y_transicion_invalida(cliente):
    _catalogos(cliente)
    assert cliente.post("/clientes", json={"id": "CLI-1", "nombre": "otra vez"}).status_code == 409
    oid = _orden(cliente)
    r = cliente.post(f"/ordenes/{oid}/llegada")
    assert r.status_code == 409 and r.json()["codigo"] == "TransicionDeEstadoInvalida"
    assert "el servicio está confirmado" in r.json()["mensaje"] and "debe estar en camino" in r.json()["mensaje"]
    assert r.json()["que_hacer"]




def test_422_reglas_de_negocio(cliente):
    oid = _orden(cliente, alto_valor=True)
    r = cliente.post(f"/ordenes/{oid}/asignacion", json={"unidad_id": "U-1", "operador_id": "OP-1"})
    assert r.status_code == 422 and r.json()["codigo"] == "ControlDeAltoValorPendiente"
    assert cliente.post(f"/ordenes/{oid}/autorizacion-alto-valor", json={"autorizado_por": "Operaciones"}).status_code == 200
    cliente.put("/operadores/OP-1/disponibilidad", json={"disponible": False})
    r = cliente.post(f"/ordenes/{oid}/asignacion", json={"unidad_id": "U-1", "operador_id": "OP-1"})
    assert r.status_code == 422 and r.json()["codigo"] == "RecursosNoDisponibles"
    r = cliente.post(f"/ordenes/{oid}/cancelacion", json={"solicitado_por": "Ventas", "motivo": "x", "rol_que_autoriza": "Ventas"})
    assert r.status_code == 422 and r.json()["codigo"] == "SinAutoridadParaCancelar"


def test_422_no_se_genera_orden_de_una_cotizacion_sin_aceptar(cliente):
    _catalogos(cliente)
    cot = cliente.post("/cotizaciones", json={"cliente_id": "CLI-1", "solicitud": SOLICITUD}).json()["datos"]["cotizacion_id"]
    r = cliente.post("/ordenes", json={"cotizacion_id": cot, "ruta": "R", "horario_recoleccion": "2026-11-20T08:00:00Z"})
    assert r.status_code == 422
    r = cliente.post(f"/cotizaciones/{cot}/respuesta", json={"respuesta": "ACEPTA"})
    assert r.status_code == 422 and r.json()["codigo"] == "CotizacionNoElaborada"


def test_incidencia_en_destino_no_entrega_el_servicio(cliente):
    oid = _orden(cliente)
    cliente.post(f"/ordenes/{oid}/asignacion", json={"unidad_id": "U-1", "operador_id": "OP-1"})
    cliente.post(f"/ordenes/{oid}/recepcion", json={"evidencia": EVIDENCIA})
    cliente.post(f"/ordenes/{oid}/traslado")
    cliente.post(f"/ordenes/{oid}/llegada")
    r = cliente.post(f"/ordenes/{oid}/entrega", json={"evidencia": EVIDENCIA, "incidencia": "DESTINATARIO_AUSENTE",
                                                      "descripcion_incidencia": "Nadie recibió"})
    assert r.status_code == 200 and r.json()["datos"]["estado"] == "LLEGADA_A_DESTINO"
    assert cliente.post(f"/ordenes/{oid}/entrega", json={"evidencia": EVIDENCIA}).status_code == 400  # sin receptor: datos incompletos
    assert cliente.post(f"/ordenes/{oid}/incidencias", json={
        "tipo": "RETRASO", "descripcion": "Tráfico", "evidencia": EVIDENCIA}).status_code == 200
    assert len(cliente.get(f"/ordenes/{oid}/estado").json()["incidencias"]) == 2


def test_cambio_operativo_bloquea_y_se_revisa(cliente):
    oid = _orden(cliente)
    assert cliente.post(f"/ordenes/{oid}/cambios-operativos",
                        json={"solicitado_por": "Cliente", "descripcion": "Otro horario"}).status_code == 201
    r = cliente.post(f"/ordenes/{oid}/asignacion", json={"unidad_id": "U-1", "operador_id": "OP-1"})
    assert r.status_code == 409 and r.json()["codigo"] == "CambioPendienteDeRevision"
    assert cliente.get(f"/ordenes/{oid}/estado").json()["cambio_operativo_pendiente"] == "Otro horario"
    assert cliente.put(f"/ordenes/{oid}/cambios-operativos/revision",
                       json={"revisado_por": "Operaciones", "aprobado": True}).status_code == 200
    assert cliente.post(f"/ordenes/{oid}/asignacion", json={"unidad_id": "U-1", "operador_id": "OP-1"}).status_code == 200


def test_modificar_solicitud_solo_mientras_esta_en_proceso(cliente):
    _catalogos(cliente)
    cot = cliente.post("/cotizaciones", json={"cliente_id": "CLI-1", "solicitud": SOLICITUD}).json()["datos"]["cotizacion_id"]
    nueva = {**SOLICITUD, "destino": {"ciudad": "Guadalajara"}}
    assert cliente.put(f"/cotizaciones/{cot}/solicitud", json=nueva).status_code == 200
    assert cliente.get(f"/cotizaciones/{cot}").json()["destino"] == "Guadalajara"
    cliente.put(f"/cotizaciones/{cot}/importe", json={"importe_mxn": "100"})
    cliente.post(f"/cotizaciones/{cot}/respuesta", json={"respuesta": "RECHAZA"})
    assert cliente.put(f"/cotizaciones/{cot}/solicitud", json=SOLICITUD).status_code == 409


def test_consultas_de_catalogo_y_cancelacion(cliente):
    oid = _orden(cliente)
    assert cliente.get("/clientes/CLI-1").json()["nombre"] == "Refacciones del Norte"
    assert cliente.get("/unidades/U-1").json()["peso_kg"] == 5000
    assert cliente.get("/operadores/OP-1").json()["disponible"] is True
    assert cliente.post(f"/ordenes/{oid}/cancelacion", json={"solicitado_por": "Cliente", "motivo": "Ya no lo necesita"}).status_code == 200
    assert cliente.get(f"/ordenes/{oid}/estado").json()["estado_actual"] == "CANCELADO"


def test_health_y_openapi_documentado(cliente):
    assert cliente.get("/health").json()["estado"] == "ok"
    spec = cliente.get("/openapi.json").json()
    assert spec["info"]["title"] == "RutaNorte Logistics API"
    assert cliente.get("/docs").status_code == 200  # Swagger UI
    codigos = {c for p in spec["paths"].values() for op in p.values() for c in op["responses"]}
    assert {"200", "201", "400", "404", "409", "422"} <= codigos


# ----------------------------- lenguaje sencillo para quien usa la API -----------------------------
def test_las_respuestas_correctas_explican_que_paso_y_que_sigue(cliente):
    r = cliente.post("/clientes", json={"id": "CLI-9", "nombre": "Cliente de prueba"})
    cuerpo = r.json()
    assert r.status_code == 201 and "quedó registrado con el código CLI-9" in cuerpo["mensaje"]
    assert cuerpo["que_sigue"] and cuerpo["datos"] == {"cliente_id": "CLI-9"}


def test_todo_error_trae_mensaje_claro_y_que_hacer_sin_terminos_tecnicos(cliente):
    _catalogos(cliente)
    oid = _orden(cliente)
    respuestas = [
        cliente.post("/clientes", json={"id": "CLI-1", "nombre": "otra vez"}),      # 409 duplicado
        cliente.post(f"/ordenes/{oid}/llegada"),                                     # 409 fuera de orden
        cliente.get("/clientes/NO-EXISTE"),                                          # 404
        cliente.post("/clientes", json={"nombre": "sin código"}),                    # 400 falta un dato
    ]
    for r in respuestas:
        cuerpo = r.json()
        assert set(cuerpo) == {"codigo", "mensaje", "que_hacer"}, cuerpo
        assert cuerpo["que_hacer"].strip()
        for tecnico in ("UNIDAD_ASIGNADA", "EN_TRANSITO", "CONFIRMADO", "Traceback", "pydantic", "Field required"):
            assert tecnico not in cuerpo["mensaje"], cuerpo["mensaje"]


def test_400_indica_en_palabras_cual_dato_falta_o_esta_mal(cliente):
    r = cliente.post("/clientes", json={"nombre": "sin código"})
    assert r.status_code == 400 and r.json()["mensaje"] == "Falta completar el dato «código»."
    r = cliente.post("/cotizaciones", json={"cliente_id": "C", "solicitud": {
        "origen": {"ciudad": "A"}, "destino": {"ciudad": "B"}, "fecha_requerida": "mañana",
        "mercancia": {"descripcion": "x", "peso_kg": "mucho", "largo_m": 1, "ancho_m": 1, "alto_m": 1}}})
    mensaje = r.json()["mensaje"]
    assert r.status_code == 400 and "fecha requerida" in mensaje and "AAAA-MM-DD" in mensaje
    assert "peso en kilos" in mensaje and "debe ser un número" in mensaje
    r = cliente.post("/cotizaciones/X/respuesta", json={"respuesta": "TAL VEZ"})
    assert "ACEPTA" in r.json()["mensaje"] and "RECHAZA" in r.json()["mensaje"]


def test_direccion_inexistente_y_pagina_principal_llevan_a_la_ayuda(cliente):
    r = cliente.get("/no-existe")
    assert r.status_code == 404 and "No existe esa dirección" in r.json()["mensaje"] and "/docs" in r.json()["que_hacer"]
    inicio = cliente.get("/", follow_redirects=False)
    assert inicio.status_code in (302, 307) and inicio.headers["location"] == "/docs"


def test_swagger_esta_en_lenguaje_sencillo_con_ejemplos_y_sin_claves_tecnicas(cliente):
    spec = cliente.get("/openapi.json").json()
    assert "Try it out" in spec["info"]["description"] and "Execute" in spec["info"]["description"]
    assert [t["name"] for t in spec["tags"]][0] == "1. Registros básicos"
    for ruta, metodos in spec["paths"].items():
        for metodo, op in metodos.items():
            assert op["summary"] and not any(x in op["summary"] for x in ("US-", "S-0", "CU-")), (ruta, op["summary"])
            assert op.get("description") or ruta == "/", (ruta, metodo)
    cuerpos = {op["requestBody"]["content"]["application/json"]["schema"]["$ref"].split("/")[-1]
               for metodos in spec["paths"].values() for op in metodos.values() if "requestBody" in op}
    assert len(cuerpos) >= 14
    for nombre in cuerpos:
        esquema = spec["components"]["schemas"][nombre]
        assert esquema.get("examples"), f"{nombre} no trae un ejemplo escrito para «Try it out»"
    for nombre, esquema in spec["components"]["schemas"].items():
        if nombre.endswith("In"):
            for campo, definicion in esquema["properties"].items():
                assert definicion.get("description") or definicion.get("$ref") or definicion.get("allOf"), f"{nombre}.{campo} no tiene descripción"
