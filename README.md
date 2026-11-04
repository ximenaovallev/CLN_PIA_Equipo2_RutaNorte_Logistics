# RutaNorte Logistics — Sistema de lógica de negocio (PIA)

Producto Integrador de Aprendizaje · Componentes de Lógica de Negocio · Profesor: Miguel Ángel Gómez Marroquín

**Equipo:** Ximena Montserrat Ovalle Vallejo · Santiago Almanza Moreno · Javier Hernández Huerta

| | |
|---|---|
| Repositorio | `https://github.com/ximenaovallev/CLN_PIA_Equipo2_RutaNorte_Logistics` |
| Sistema desplegado | `https://rutanorte-api.onrender.com` |
| Swagger UI | `https://rutanorte-api.onrender.com/docs` · OpenAPI: `https://rutanorte-api.onrender.com/openapi.json` |

> La API implementa el proceso de cotización y ejecución de servicios de transporte de RutaNorte Logistics: cotizar, aceptar, generar la orden, asignar recursos, ejecutar, entregar con evidencia o cancelar. Las reglas del BRD (R-01…R-22) viven en el dominio (DDD + Specification + máquina de estados).

## 1. Arquitectura en una vista

```
src/
├── domain/          Entidades, Value Objects, agregados (Cotizacion, OrdenDeServicio), eventos,
│                    Specification, máquina de estados, servicios de dominio (solo biblioteca estándar)
├── application/     Comandos (19), consultas (7), handlers, DTOs, puertos (Repository / Unit of Work)
├── infrastructure/  Repositorios en memoria y SQL (SQLAlchemy Core), Unit of Work, publicador de eventos,
│                    configuración 12-Factor, composición
└── api/             FastAPI: rutas, esquemas, traducción de errores de dominio a HTTP
```

Regla de dependencias: `api → application → domain ← infrastructure` (verificada por `tests/unit/test_arquitectura.py`).

## 2. Documentación (trazabilidad análisis → arquitectura → código → pruebas)

| Artefacto | Ubicación |
|---|---|
| BRD | `docs/BRD.md` |
| ≥15 historias de usuario (17) con Gherkin | `docs/analisis/historias_de_usuario.md`, `docs/analisis/features/*.feature` |
| BPMN | `docs/analisis/bpmn/01_bpmn_rutanorte.bpmn` (+ `.png`) |
| Glosario | `docs/analisis/glosario.md` |
| ADRs (12) | `docs/architecture/adr/` |
| Decisiones técnicas, supuestos | `docs/architecture/decisiones_tecnicas.md`, `supuestos.md` |
| Diagramas DDD/UML (PlantUML + PNG) | `docs/architecture/diagramas/` |
| Matriz de trazabilidad | `docs/architecture/trazabilidad.md` (verificada por `tests/test_trazabilidad.py`) |
| OpenAPI | `docs/api/openapi.json` |
| Evidencias de ejecución | `docs/evidencias/` |

## 3. Instalación

Requisitos: Python 3.10+ (probado en 3.13; la imagen Docker usa 3.12). Opcional: Docker + Docker Compose, PostgreSQL 16.

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                   # Windows: copy .env.example .env
```

## 4. Ejecución

**Local sin base de datos externa** (sin `DATABASE_URL` usa SQLite en memoria; los datos se pierden al reiniciar):

```bash
PYTHONPATH=src uvicorn --factory api.main:app_de_produccion --reload
```

**Con PostgreSQL**: exporta `DATABASE_URL=postgresql://usuario:clave@host:5432/rutanorte` y ejecuta el mismo comando. El esquema se crea al arrancar.

**Docker Compose (DB + App + Tests):**

```bash
cp .env.example .env
docker compose up --build                       # PostgreSQL + API en http://localhost:8000/docs
docker compose --profile tests run --rm tests   # pruebas con cobertura contra PostgreSQL (falla si < 80 %)
```

Puntos de entrada: `GET /health`, Swagger UI en `/docs`, OpenAPI en `/openapi.json`.

### Variables de entorno (12-Factor)

Ver `.env.example` (sin secretos reales): `DATABASE_URL`, `POSTGRES_*`, `APP_ENV`, `LOG_LEVEL`, `PORT` y los supuestos pendientes de validar `LIMITE_PESO_KG`, `LIMITE_VOLUMEN_M3`, `DIAS_CONSERVACION_EVIDENCIAS`, `ROLES_QUE_CANCELAN`.

## 5. Pruebas

```bash
pytest --cov --cov-fail-under=80                                  # memoria + SQLite  (225 pruebas)
TEST_DATABASE_URL=postgresql://usuario:clave@localhost:5432/rutanorte_test \
  pytest --cov --cov-fail-under=80                                # + PostgreSQL     (287 pruebas)
python scripts/ejecutar_paquete.py      # paquete de datos del curso: 120 casos + 20 transiciones
python scripts/exportar_openapi.py --verificar   # el OpenAPI publicado coincide con el código
```

Resultado verificado: **287 pruebas aprobadas, cobertura 98 %** (umbral exigido: 80 %). Las mismas pruebas de comportamiento corren contra repositorios en memoria, SQLite y PostgreSQL.

## 6. Demostración

Con el servidor levantado (local o desplegado):

```bash
python scripts/demo.py [URL_BASE]       # recorre 21 pasos: cotizar → aceptar → orden → asignar → ejecutar → entregar, más rechazos
```

Guion sugerido para la defensa: (1) `/docs`; (2) crear cliente, recursos y solicitud; (3) cotizar y aceptar; (4) confirmar y asignar recursos (probar conflicto → 422); (5) intentar una transición inválida (→ 409); (6) entregar con y sin evidencia; (7) cancelar con rol sin autoridad (→ 422); (8) consultar eventos de dominio.

## 7. CI/CD

`.github/workflows/ci.yml`: **pruebas** (PostgreSQL de servicio, cobertura ≥ 80 %, paquete de datos, contrato OpenAPI) → **imagen-docker** (build) → **despliegue** (en `main`, vía *deploy hook* de Render si el secreto `RENDER_DEPLOY_HOOK_URL` está configurado). Despliegue con `render.yaml` (Blueprint: base PostgreSQL + servicio web Docker). Nota: el plan gratuito de Render duerme el servicio tras inactividad; abrir `/health` unos minutos antes de la demostración.

## 8. Supuestos pendientes

S-01…S-05 (topes de peso/volumen, caducidad de evidencias, roles que cancelan…) se tratan como parámetros configurables y están listados en `docs/architecture/supuestos.md` para validación con el cliente.
