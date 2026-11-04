# ADR-009: PostgreSQL con SQLAlchemy Core detrás de los repositorios

**Estado:** Aceptada (cierra el pendiente de tecnología de ADR-002)

## Contexto
El PIA exige una aplicación funcional con base de datos, Docker Compose (DB + App + Tests) y despliegue. El dominio no debe depender de ninguna tecnología de persistencia.

## Alternativas
| Opción | Problema |
|---|---|
| ORM declarativo mapeando el dominio | Obliga a que las entidades conozcan la persistencia o a un mapeo imperativo complejo |
| Solo memoria | No cumple el requisito de aplicación funcional ni de despliegue |
| **SQLAlchemy Core + repositorios que traducen fila ↔ agregado** | Más código de traducción, pero el dominio queda limpio |

## Decisión
PostgreSQL 16 en Compose, CI y Render; SQLite en memoria para pruebas rápidas. Esquema en `infrastructure/sql/tablas.py` (9 tablas; diagrama `03_modelo_relacional`, generado desde las tablas). Los repositorios traducen con `OrdenDeServicio.restaurar(...)`, que rehidrata el agregado sin ejecutar reglas de transición. Importes `Numeric(12,2)` ↔ `Decimal`; fechas siempre en UTC. `SqlUnitOfWork` guarda la sesión en un `threading.local`: FastAPI atiende peticiones en varios hilos y un único objeto compartido mezclaría transacciones. `DATABASE_URL` acepta `postgres://` y `postgresql://` (formas que inyectan las plataformas).

## Consecuencias
- Beneficio: se cambió de memoria a SQL sin tocar dominio ni aplicación; el mismo conjunto de pruebas valida ambos.
- Costo: reescribir hijos del agregado (historial, incidencias, evidencias) en cada guardado; aceptable por su tamaño.
- No hay migraciones versionadas: el esquema se crea con `metadata.create_all` al iniciar. Mejora futura: Alembic.

## Trazabilidad
RNF-05; RF-14, RF-15; R-17, R-18; pruebas `tests/integration/test_persistencia_sql.py` y el backend parametrizado `backend`.
