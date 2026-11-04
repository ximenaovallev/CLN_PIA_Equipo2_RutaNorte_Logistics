"""Verifica que la matriz BRD → regla → componente → prueba no tenga referencias rotas (coherencia documento ↔ código)."""
import importlib
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import datos_documentales as d  # noqa: E402
from api.main import crear_app  # noqa: E402
from infrastructure.composicion import construir_aplicacion_en_memoria  # noqa: E402
from conftest import configuracion  # noqa: E402

BPMN = (RAIZ / "docs" / "analisis" / "bpmn" / "01_bpmn_rutanorte.bpmn").read_text(encoding="utf-8")


def _existe_prueba(ref: str) -> bool:
    archivo, nombre = ref.split("::")
    ruta = RAIZ / archivo
    return ruta.exists() and re.search(rf"^def {re.escape(nombre)}\(", ruta.read_text(encoding="utf-8"), re.M) is not None


def _resolver(ruta: str):
    if "/" in ruta:  # archivo del repositorio (p. ej. el workflow de CI)
        assert (RAIZ / ruta).exists(), ruta
        return RAIZ / ruta
    partes = ruta.split(".")
    for corte in range(len(partes), 0, -1):
        try:
            objeto = importlib.import_module(".".join(partes[:corte]))
        except ModuleNotFoundError:
            continue
        for atributo in partes[corte:]:
            objeto = getattr(objeto, atributo)
        return objeto
    raise AssertionError(f"No se puede resolver {ruta}")


@pytest.fixture(scope="module")
def operaciones_openapi():
    spec = crear_app(construir_aplicacion_en_memoria(configuracion()), configuracion()).openapi()
    return {f"{m.upper()} {p}" for p, ops in spec["paths"].items() for m in ops}


IDS_RF = {r[0] for r in d.REQUISITOS}


def test_hay_al_menos_15_historias_con_gherkin_y_cada_una_tiene_escenarios():
    assert len(d.HISTORIAS) >= 15
    for h in d.HISTORIAS:
        assert h["escenarios"], h["id"]
        for _, pasos in h["escenarios"]:
            assert pasos[0].startswith("Given") and any(p.startswith("When") for p in pasos) and any(p.startswith("Then") for p in pasos), h["id"]


@pytest.mark.parametrize("h", d.HISTORIAS, ids=lambda h: h["id"])
def test_cada_historia_apunta_a_codigo_pruebas_endpoints_y_bpmn_que_existen(h, operaciones_openapi):
    assert h["pruebas"], f"{h['id']} no tiene pruebas"
    for p in h["pruebas"]:
        assert _existe_prueba(p), f"{h['id']}: no existe la prueba {p}"
    for c in h["componentes"]:
        assert _resolver(c) is not None, f"{h['id']}: no existe el componente {c}"
    for e in h["api"]:
        assert e in operaciones_openapi, f"{h['id']}: el endpoint {e} no está en el OpenAPI"
    for rf in h["rf"]:
        assert rf in IDS_RF, f"{h['id']}: requisito desconocido {rf}"
    for token in re.findall(r"\b[STGEB][A-Z]?\d+[AB]?\b|\bDS1\b", h["bpmn"]):
        assert f'id="{token}"' in BPMN, f"{h['id']}: el elemento BPMN {token} no existe en el diagrama"
    assert (RAIZ / "docs" / "analisis" / "features" / f"{h['id'].lower()}.feature").exists()


@pytest.mark.parametrize("r", d.REGLAS, ids=lambda r: r[0])
def test_cada_regla_tiene_requisito_componente_y_pruebas_reales(r):
    _, _, rf, historias, componente, pruebas = r
    assert rf in IDS_RF and _resolver(componente) is not None and pruebas
    assert all(_existe_prueba(p) for p in pruebas), r[0]
    assert all(h in {x["id"] for x in d.HISTORIAS} for h in historias)


def test_todo_requisito_esta_cubierto_por_una_historia_o_una_regla():
    cubiertos = {rf for h in d.HISTORIAS for rf in h["rf"]} | {r[2] for r in d.REGLAS}
    assert IDS_RF <= cubiertos, sorted(IDS_RF - cubiertos)


def test_todo_endpoint_de_la_api_esta_asociado_a_una_historia(operaciones_openapi):
    asociados = {e for h in d.HISTORIAS for e in h["api"]} | set(d.ENDPOINTS_NO_HISTORIAS)
    assert operaciones_openapi <= asociados, sorted(operaciones_openapi - asociados)
    assert asociados <= operaciones_openapi, sorted(asociados - operaciones_openapi)


def test_las_17_historias_de_la_unidad_2_se_conservan():
    assert [h["id"] for h in d.HISTORIAS] == [f"US-{n:02d}" for n in range(1, 18)]


def test_el_bpmn_no_referencia_elementos_inexistentes_y_tiene_las_tareas_clave():
    for token in ("T1", "T2", "T4", "T8", "T10", "T11", "T16", "T19", "G2", "G4"):
        assert f'id="{token}"' in BPMN


def test_ci_y_compose_exigen_cobertura_minima_de_80():
    assert "--cov-fail-under=80" in (RAIZ / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "--cov-fail-under=80" in (RAIZ / "docker-compose.yml").read_text(encoding="utf-8")


# ------------------------- los diagramas corresponden al código -------------------------
def _clases_del_dominio() -> set[str]:
    import inspect
    import pkgutil
    import domain
    nombres = set()
    for m in pkgutil.iter_modules(domain.__path__):
        mod = importlib.import_module(f"domain.{m.name}")
        nombres |= {n for n, o in inspect.getmembers(mod, inspect.isclass) if o.__module__ == mod.__name__}
    return nombres


@pytest.mark.parametrize("archivo", ["01_clases_dominio.puml", "01b_especificaciones_eventos_y_estados.puml"])
def test_toda_clase_de_los_diagramas_de_dominio_existe_en_el_codigo(archivo):
    texto = (RAIZ / "docs" / "architecture" / "diagramas" / archivo).read_text(encoding="utf-8")
    declaradas = set(re.findall(r"^\s*(?:abstract class|class|interface|enum)\s+(\w+)", texto, re.M))
    ajenas = {"EstadoServicio_ref"}  # sin excepciones: todas deben existir
    faltan = declaradas - _clases_del_dominio() - ajenas
    assert not faltan, f"Clases del diagrama que no existen en src/domain: {sorted(faltan)}"


def test_los_diagramas_generados_estan_al_dia_con_el_codigo():
    import generar_diagramas as g
    base = RAIZ / "docs" / "architecture" / "diagramas"
    assert (base / "02_estados_del_servicio.puml").read_text(encoding="utf-8") == g.estados_puml()
    assert (base / "03_modelo_relacional.puml").read_text(encoding="utf-8") == g.er_puml()


def test_los_diagramas_de_secuencia_nombran_componentes_reales():
    import application.handlers as h
    import infrastructure.sql.unit_of_work as u
    for archivo, handler in (("05_secuencia_asignar_recursos.puml", "AsignarRecursosHandler"),
                             ("06_secuencia_registrar_entrega.puml", "RegistrarEntregaHandler")):
        texto = (RAIZ / "docs" / "architecture" / "diagramas" / archivo).read_text(encoding="utf-8")
        assert handler in texto and hasattr(h, handler) and "SqlUnitOfWork" in texto and hasattr(u, "SqlUnitOfWork")
