"""Demostración del flujo completo contra una API en ejecución (local o desplegada).

Uso:  python scripts/demo.py http://localhost:8000
"""
from __future__ import annotations

import sys
import uuid

import httpx

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
SUFIJO = uuid.uuid4().hex[:6].upper()  # permite repetir la demo sin choques de identificadores


def paso(titulo: str, r: httpx.Response, esperado: int) -> dict:
    ok = "OK " if r.status_code == esperado else "ERR"
    print(f"[{ok}] {r.request.method:4} {r.request.url.path:48} -> {r.status_code}  {titulo}")
    if r.status_code != esperado:
        print("      ", r.text)
        raise SystemExit(1)
    return r.json()


def main() -> None:
    cli, uni, ope = f"CLI-{SUFIJO}", f"UNI-{SUFIJO}", f"OPE-{SUFIJO}"
    with httpx.Client(base_url=BASE, timeout=30) as c:
        paso("la API está viva", c.get("/health"), 200)
        paso("registrar cliente", c.post("/clientes", json={"id": cli, "nombre": "Refacciones del Norte", "ciudad": "Monterrey"}), 201)
        paso("registrar unidad", c.post("/unidades", json={"id": uni, "tipo": "Caja seca", "peso_kg": 5000, "volumen_m3": 30}), 201)
        paso("registrar operador", c.post("/operadores", json={"id": ope, "nombre": "Luis Pérez"}), 201)
        solicitud = {"origen": {"ciudad": "Monterrey", "direccion": "Av. Industria 100"},
                     "destino": {"ciudad": "Querétaro", "direccion": "Parque Industrial 5"},
                     "mercancia": {"descripcion": "Refacciones", "peso_kg": 800, "largo_m": 2, "ancho_m": 1.5, "alto_m": 1.5,
                                   "alto_valor": True}, "fecha_requerida": "2026-12-01"}
        cot = paso("solicitar cotización (SOLICITADO)", c.post("/cotizaciones", json={"cliente_id": cli, "solicitud": solicitud}), 201)["datos"]["cotizacion_id"]
        paso("ERROR: aceptar sin cotizar -> 422", c.post(f"/cotizaciones/{cot}/respuesta", json={"respuesta": "ACEPTA"}), 422)
        paso("elaborar cotización (COTIZADO)", c.put(f"/cotizaciones/{cot}/importe", json={"importe_mxn": "15000.50"}), 200)
        paso("el cliente acepta", c.post(f"/cotizaciones/{cot}/respuesta", json={"respuesta": "ACEPTA"}), 200)
        oid = paso("generar orden (CONFIRMADO)", c.post("/ordenes", json={"cotizacion_id": cot, "ruta": "MTY-QRO", "horario_recoleccion": "2026-11-20T08:00:00Z"}), 201)["datos"]["orden_id"]
        paso("ERROR: alto valor sin autorizar -> 422", c.post(f"/ordenes/{oid}/asignacion", json={"unidad_id": uni, "operador_id": ope}), 422)
        paso("autorizar alto valor", c.post(f"/ordenes/{oid}/autorizacion-alto-valor", json={"autorizado_por": "Operaciones"}), 200)
        paso("asignar unidad y operador (UNIDAD_ASIGNADA)", c.post(f"/ordenes/{oid}/asignacion", json={"unidad_id": uni, "operador_id": ope}), 200)
        paso("ERROR: entregar sin haber recolectado -> 409", c.post(f"/ordenes/{oid}/entrega", json={"destinatario": "INE-1", "evidencia": {"referencia": "x.jpg"}}), 409)
        paso("recepción con evidencia (RECOLECTADO)", c.post(f"/ordenes/{oid}/recepcion", json={"evidencia": {"referencia": "recepcion.jpg"}}), 200)
        paso("iniciar traslado (EN_TRANSITO)", c.post(f"/ordenes/{oid}/traslado"), 200)
        paso("incidencia: retraso (no cambia el estado)", c.post(f"/ordenes/{oid}/incidencias", json={"tipo": "RETRASO", "descripcion": "Tráfico en la carretera"}), 200)
        paso("llegada a destino (LLEGADA_A_DESTINO)", c.post(f"/ordenes/{oid}/llegada"), 200)
        paso("entrega con receptor y evidencia (ENTREGADO)", c.post(f"/ordenes/{oid}/entrega", json={"destinatario": "INE-123456", "evidencia": {"referencia": "entrega.jpg"}}), 200)
        estado = paso("consultar estado e historial", c.get(f"/ordenes/{oid}/estado"), 200)
        paso("ERROR: orden inexistente -> 404", c.get("/ordenes/NO-EXISTE/estado"), 404)
        ind = paso("indicadores", c.get("/indicadores", params={"desde": "2020-01-01", "hasta": "2100-01-01"}), 200)
    print(f"\nEstado final: {estado['estado_actual']} | eventos en el historial: {len(estado['eventos'])}")
    print(f"Entregas realizadas: {ind['entregas_realizadas']} | cumplimiento de entregas (S-05): {ind['cumplimiento_de_entregas']}")


if __name__ == "__main__":
    main()
