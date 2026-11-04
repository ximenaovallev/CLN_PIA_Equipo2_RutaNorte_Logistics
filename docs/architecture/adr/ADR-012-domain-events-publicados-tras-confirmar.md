# ADR-012: Domain Events publicados solo después de confirmar la transacción

**Estado:** Aceptada

## Contexto
Los agregados registran hechos del negocio (`RecursosAsignados`, `EntregaRegistrada`…). Publicarlos antes del commit informaría de cambios que luego podrían revertirse.

## Decisión
Los agregados acumulan eventos (`extraer_eventos()`); el handler los publica **después** de `uow.confirmar()`; si hay error de dominio no se publica nada. `IPublicadorDeEventos` tiene dos implementaciones: memoria (pruebas) y `SqlPublicadorDeEventos`, que registra cada evento en la tabla `eventos_de_dominio` (tipo, agregado, datos JSON, fecha) como bitácora auditable. Eventos: `CotizacionElaborada`, `CotizacionAceptada`, `OrdenDeServicioGenerada`, `RecursosAsignados`, `CargaDeAltoValorAutorizada`, `ServicioCancelado`, `EntregaRegistrada`, `IncidenciaRegistrada`, `EstadoDelServicioCambiado`, `CambioOperativoSolicitado`, `CambioOperativoRevisado`.

## Consecuencias
- Beneficio: no hay eventos «fantasma»; el registro sirve para auditoría.
- Riesgo: si el proceso cae entre el commit y la publicación se pierde un evento (la orden sí queda guardada y su historial la refleja). Mejora futura: patrón *outbox* (guardar el evento en la misma transacción).

## Trazabilidad
RF-11; N2; pruebas `test_los_domain_events_se_registran_tras_confirmar`, `test_los_eventos_sql_quedan_en_la_tabla_con_su_agregado`.
