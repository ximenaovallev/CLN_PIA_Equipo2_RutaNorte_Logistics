# ADR-011: Configuración 12-Factor, Docker Compose y CI/CD

**Estado:** Aceptada

## Decisión
- **Configuración por entorno** (`infrastructure/configuracion.py`): `DATABASE_URL`, `APP_ENV`, `LOG_LEVEL`, `PORT` y los supuestos `LIMITE_PESO_KG`, `LIMITE_VOLUMEN_M3`, `DIAS_CONSERVACION_EVIDENCIAS`, `ROLES_QUE_CANCELAN`. `.env.example` solo trae valores de ejemplo; `.env` está en `.gitignore`.
- **Docker**: imagen `python:3.12-slim`, usuario no root, un único proceso (`uvicorn`), logs a stdout. **docker-compose.yml**: `db` (postgres:16 con healthcheck), `app` (espera la base sana) y `tests` (perfil `tests`, ejecuta `pytest --cov --cov-fail-under=80` contra PostgreSQL).
- **CI** (`.github/workflows/ci.yml`): pytest sobre memoria, SQLite y un servicio PostgreSQL con cobertura mínima 80 %, evidencia del paquete de datos, verificación del OpenAPI, construcción de la imagen, validación de Compose y prueba de arranque.
- **CD**: Render (`render.yaml`, blueprint con base y servicio web, `autoDeploy`); el job `despliegue` puede disparar el deploy hook si existe el secreto.

## Consecuencias
La misma imagen corre en local y en Render. Limitación conocida: el plan gratuito de Render duerme el servicio tras inactividad (la primera petición tarda), por lo que conviene abrir `/health` antes de la demostración.

## Trazabilidad
RNF-03, RNF-04; R-20, R-21.
