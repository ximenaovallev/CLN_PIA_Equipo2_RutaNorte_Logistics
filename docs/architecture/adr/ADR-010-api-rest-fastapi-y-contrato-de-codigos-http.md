# ADR-010: API REST con FastAPI y contrato de códigos HTTP

**Estado:** Aceptada

## Contexto
El PIA exige una API REST documentada (OpenAPI/Swagger UI) y el paquete del profesor pide contrastar respuestas con 200/201, 400/409/422 y 404 «según el contrato del equipo». La API no debe contener reglas de negocio.

## Decisión
- FastAPI en `src/api/`: `rutas.py` traduce JSON → Command/Query → `Resultado` → HTTP; `esquemas.py` (pydantic) valida el borde; `errores.py` contiene la tabla error de dominio → código.
- **Contrato**: 200 operación correcta · 201 recurso creado · **400** datos mal formados o inválidos (`DatosInvalidos`, validación pydantic) · **404** no existe (`EntidadNoEncontrada`) · **409** conflicto con el estado actual (`TransicionDeEstadoInvalida`, `EntidadYaExiste`, `CotizacionNoModificable`, `CambioPendienteDeRevision`) · **422** regla de negocio no cumplida (`RecursosNoDisponibles`, `ControlDeAltoValorPendiente`, `SinAutoridadParaCancelar`, `OrdenNoGenerable`, `CotizacionNoElaborada`). Todo error devuelve `{codigo, mensaje}`.
- Se reemplazó el 422 por defecto de FastAPI por 400 para la validación de formato, de modo que 422 signifique siempre «regla de negocio».
- Swagger UI en `/docs`, contrato exportado a `docs/api/openapi.json` (`scripts/exportar_openapi.py`; CI verifica que esté al día). Recursos: sustantivos en plural; las acciones que no son CRUD son subrecursos (`/ordenes/{id}/asignacion`).

## Consecuencias
- Beneficio: el cliente distingue «corrige tu petición» (400) de «el recurso está en otro estado» (409) y de «la regla del negocio no lo permite» (422).
- Riesgo: la asignación entre error de dominio y código es una decisión del equipo; está en un solo archivo y probada.

## Trazabilidad
RNF-02; R-19; pruebas `tests/integration/test_api.py`; evidencia `docs/evidencias/demo_ejecucion.txt`.
