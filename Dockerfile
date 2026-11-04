FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
ARG INSTALAR_DEV=false
RUN if [ "$INSTALAR_DEV" = "true" ]; then pip install --no-cache-dir -r requirements-dev.txt; \
    else pip install --no-cache-dir -r requirements.txt; fi

COPY src ./src
COPY tests ./tests
COPY scripts ./scripts
COPY docs/api ./docs/api
COPY pyproject.toml ./

RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
# La configuración llega por variables de entorno (12-Factor); Render inyecta PORT.
CMD ["sh", "-c", "uvicorn --factory api.main:app_de_produccion --host 0.0.0.0 --port ${PORT:-8000}"]
