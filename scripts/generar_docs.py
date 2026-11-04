"""Genera historias_de_usuario.md, los .feature y trazabilidad.md desde scripts/datos_documentales.py."""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_documentales as d  # noqa: E402

ANALISIS = RAIZ / "docs" / "analisis"
ARQ = RAIZ / "docs" / "architecture"
NOMBRE = {"cliente": "Cliente"}


def feature(h: dict) -> str:
    lineas = [f"# language: en", f"@{h['id']} " + " ".join(f"@{rf}" for rf in h["rf"]),
              f"Feature: {h['id']} {h['titulo']}", f"  As a {h['como']}", f"  I want to {h['quiero']}",
              f"  So that {h['para']}", ""]
    for nombre, pasos in h["escenarios"]:
        lineas.append(f"  Scenario: {nombre}")
        lineas += [f"    {p}" for p in pasos]
        lineas.append("")
    return "\n".join(lineas)


def historias_md() -> str:
    o = ["# Historias de usuario y criterios de aceptación (Gherkin)", "",
         "Las 17 historias de la Unidad 2 se conservan con su identificador y se **refinan**: cada criterio genérico se "
         "convirtió en escenarios concretos (camino feliz y excepción) con datos de ejemplo, el endpoint que los ejecuta "
         "y las pruebas que los verifican. Los `.feature` están en `docs/analisis/features/`. "
         "`tests/test_trazabilidad.py` comprueba que todas las referencias de esta página existan.", "",
         "| ID | Historia | Requisito | Necesidad | BPMN | Endpoint | Pruebas |", "|---|---|---|---|---|---|---|"]
    for h in d.HISTORIAS:
        o.append(f"| {h['id']} | {h['titulo']} | {', '.join(h['rf'])} | {h['necesidades']} | {h['bpmn']} | "
                 f"{'<br>'.join('`'+e+'`' for e in h['api'])} | {len(h['pruebas'])} |")
    o.append("")
    for h in d.HISTORIAS:
        o += [f"## {h['id']}: {h['titulo']}", "",
              f"**Como** {h['como']}, **quiero** {h['quiero']}, **para** {h['para']}.", "",
              f"- Requisitos: {', '.join(h['rf'])} · Necesidades: {h['necesidades']} · BPMN: {h['bpmn']}",
              f"- API: {', '.join('`'+e+'`' for e in h['api'])}",
              f"- Componentes: {', '.join('`'+c+'`' for c in h['componentes'])}", "", "```gherkin"]
        for nombre, pasos in h["escenarios"]:
            o.append(f"Scenario: {nombre}")
            o += [f"  {p}" for p in pasos]
            o.append("")
        o[-1:] = ["```", ""]
        o.append("Pruebas: " + ", ".join(f"`{p.split('/')[-1]}`" for p in h["pruebas"]))
        o.append("")
    return "\n".join(o)


def trazabilidad_md() -> str:
    o = ["# Matriz de trazabilidad: BRD → regla → componente → prueba", "",
         "Generada desde `scripts/datos_documentales.py` y verificada por `tests/test_trazabilidad.py` "
         "(cada prueba, componente, endpoint y elemento BPMN citado existe). IDs: **N1–N8** necesidades del BRD · "
         "**RF/RNF** requisitos refinados (`docs/BRD.md`) · **US** historias · **R-xx** reglas · **S/T/G/E/B/DS** elementos del BPMN.", "",
         "## 1. Requisito → historias → BPMN → API", "",
         "| Requisito | Necesidad | Descripción | Historias | BPMN | API |", "|---|---|---|---|---|---|"]
    for rid, nec, desc in d.REQUISITOS:
        hs = [h for h in d.HISTORIAS if rid in h["rf"]]
        o.append(f"| {rid} | {nec} | {desc} | {', '.join(h['id'] for h in hs) or '—'} | "
                 f"{'; '.join(sorted({h['bpmn'] for h in hs})) or '—'} | "
                 f"{'<br>'.join(sorted({'`'+e+'`' for h in hs for e in h['api']})) or '—'} |")
    o += ["", "## 2. Regla del negocio → componente → prueba", "",
          "| Regla | Descripción | Requisito | Historias | Componente (código) | Pruebas |", "|---|---|---|---|---|---|"]
    for rid, desc, rf, hs, comp, pruebas in sorted(d.REGLAS):
        o.append(f"| {rid} | {desc} | {rf} | {', '.join(hs) or '—'} | `{comp}` | "
                 f"{'<br>'.join('`'+p.replace('tests/','')+'`' for p in pruebas)} |")
    o += ["", "## 3. Historia → componentes → pruebas", "",
          "| Historia | Componentes | Pruebas |", "|---|---|---|"]
    for h in d.HISTORIAS:
        o.append(f"| {h['id']} {h['titulo']} | {'<br>'.join('`'+c+'`' for c in h['componentes'])} | "
                 f"{'<br>'.join('`'+p.replace('tests/','')+'`' for p in h['pruebas'])} |")
    o += ["", "## 4. Hallazgos", "",
          "- Todos los endpoints de la API están asociados a una historia o son de apoyo (catálogos, `/health`); la prueba "
          "`test_todo_endpoint_de_la_api_esta_asociado_a_una_historia` lo exige en ambos sentidos.",
          "- Los supuestos S-01 a S-05 (`docs/architecture/supuestos.md`) aparecen como reglas R-06, R-08, R-14, R-15 y R-16.",
          "- El paquete de datos del profesor se relaciona con estas reglas en `docs/architecture/paquete_de_datos.md`."]
    return "\n".join(o) + "\n"


if __name__ == "__main__":
    (ANALISIS / "features").mkdir(parents=True, exist_ok=True)
    for h in d.HISTORIAS:
        (ANALISIS / "features" / f"{h['id'].lower()}.feature").write_text(feature(h), encoding="utf-8")
    (ANALISIS / "historias_de_usuario.md").write_text(historias_md(), encoding="utf-8")
    (ARQ / "trazabilidad.md").write_text(trazabilidad_md(), encoding="utf-8")
    print("Documentación generada.")
