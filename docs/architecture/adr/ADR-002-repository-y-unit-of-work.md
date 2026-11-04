# ADR-002: Repository en términos del dominio y Unit of Work por caso de uso

**Estado:** Aceptada (la tecnología concreta de persistencia se decidió en el PIA: ADR-009)

## Contexto
El BRD exige centralizar la información del servicio (N1) y conservar un historial de cambios (N2, N4). Un caso de uso como "asignar unidad y operador" modifica la orden y debe confirmarse o revertirse completo (RNF-05).

## Alternativas
1. Que los handlers ejecuten SQL directamente: acopla aplicación y dominio a la base de datos y rompe DIP.
2. Un repositorio genérico CRUD por tabla: expone la estructura de datos, no necesidades del dominio.
3. **Repository por agregado/entidad con Unit of Work**: interfaces con lenguaje del dominio; la implementación se aísla en infraestructura.

## Decisión
`IClienteRepository`, `ICotizacionRepository`, `IOrdenServicioRepository`, `IUnidadRepository` e `IOperadorRepository` (`obtener_por_id`, `guardar` y, donde aplica, `existe`) viven en `src/domain/repositorios.py`; `IUnitOfWork` en `src/application/puertos.py`. La transacción inicia con `with uow`, termina con `confirmar()` y cualquier salida sin confirmar hace rollback; ante un error de dominio no se publica ningún evento. Hay **dos implementaciones del mismo contrato**: SQL (`infrastructure/sql/`) y memoria (`infrastructure/en_memoria.py`). Las pruebas de integración corren contra ambas (y contra PostgreSQL en CI) con las mismas aserciones.

## Consecuencias
- Beneficio: el dominio no conoce SQL ni ORM; el contrato queda demostrado por dos implementaciones.
- Costo: una capa más de código y mantener dos implementaciones.
- Riesgo: que divergan; se mitiga ejecutando cada prueba de comportamiento sobre todos los backends (fixture parametrizado `backend`).

## Trazabilidad
N1, N2, N4; RNF-05; US-05, US-07, US-08, US-10; diagramas `05_secuencia_asignar_recursos`, `06_secuencia_registrar_entrega`; pruebas `test_error_de_dominio_revierte_la_transaccion`, `test_salir_sin_confirmar_no_deja_nada`, `test_unit_of_work_revierte_si_no_se_confirma` (ver `trazabilidad.md`, R-18).
