# ADR-003: CQRS básico (Commands/Queries) sin bases de datos separadas

**Estado:** Aceptada

## Contexto
Atención al Cliente depende de Operaciones para conocer el estado de un servicio y necesita consultar estado, eventos, retrasos e incidencias (N6, US-14). Operaciones necesita indicadores históricos (N7, US-15). Estas lecturas no deben exponer el modelo de escritura.

## Alternativas
1. Un solo modelo para escribir y consultar: simple, pero las consultas arrastran reglas e invariantes que no necesitan.
2. CQRS completo con bases separadas y sincronización por eventos: excesivo para el alcance actual.
3. **CQRS básico**: Commands con Handler que usan el dominio; Queries con Handler que usan un puerto de lectura y devuelven DTO / View Model.

## Decisión
- Commands (`src/application/comandos.py`): 19, uno por intención (p. ej. `SolicitarCotizacionCommand`, `AsignarRecursosCommand`, `RegistrarEntregaCommand`, `CancelarServicioCommand`).
- Queries: `ConsultarEstadoDelServicioQuery`, `ConsultarIndicadoresQuery`, `ConsultarCotizacionQuery`, `ListarOrdenesQuery` y consultas de catálogo, resueltas por `IConsultaDeServicios` (`SqlConsultaDeServicios`, `EnMemoriaConsultaDeServicios`) y devueltas como DTO (`application/dto.py`).
- Misma base de datos. Los DTO de lectura no se reutilizan para escribir, y la API expone los comandos con POST/PUT y las consultas con GET.
- Límite reconocido: las consultas SQL reconstruyen el agregado con los mismos repositorios y proyectan a DTO (`infrastructure/vistas.py`); es suficiente para el volumen esperado y evita duplicar reglas. Si el volumen crece, la consulta puede pasar a SQL directo sin cambiar el puerto.

## Consecuencias
- Beneficio: Atención al Cliente consulta sin depender de Operaciones ni de WhatsApp.
- Costo: más clases (comandos, queries, DTO).
- Riesgo: lecturas costosas con muchos servicios (indicadores recorren las órdenes); aceptable hoy.

## Trazabilidad
N3, N6, N7; RF-14, RF-15; US-14, US-15; BPMN: T22, T23, DS1; pruebas `test_cu05_*` y `test_api.py` (ver `trazabilidad.md`).
