# ADR-005: OrdenDeServicio como agregado que contiene estado, asignación, historial e incidencias

**Estado:** Aceptada (decisión dudosa documentada)

## Contexto
El modelo de dominio de la Unidad 2 tenía `Orden de servicio` y `Servicio` como entidades 1:1, e `Incidencia` y `Evidencia` asociadas al servicio. El glosario define Historial, Incidencia, Evidencia y Asignación. Hay que decidir el límite de consistencia.

## Alternativas
1. Agregados separados Orden, Servicio e Incidencia: más flexible, pero el historial y las transiciones de estado se coordinarían entre agregados.
2. **Un solo agregado `OrdenDeServicio`** (el servicio se identifica con su orden), con `Asignacion`, `EntradaDeHistorial`, `Incidencia` y evidencias asociadas.
3. Cotización dentro de la orden: descartado; la cotización existe antes y puede ser rechazada.

## Decisión
`Cotizacion` y `OrdenDeServicio` son agregados distintos. `Unidad` y `Operador` son entidades propias (sus datos cambian con independencia de la orden). Todo cambio de estado, asignación o incidencia pasa por la raíz y deja entrada en el historial. Las referencias entre agregados son por identificador.

## Consecuencias
- Beneficio: invariantes (historial siempre actualizado, evidencias asociadas, transiciones válidas) se protegen en un solo punto.
- Costo: el agregado puede crecer con muchas incidencias; se acepta por el volumen esperado de un servicio.
- Refinamiento en el PIA: los estados SOLICITADO y COTIZADO ocurren antes de que exista la orden. Se resolvió haciendo que `Cotizacion` los derive de su importe (`estado_del_servicio`: sin importe = SOLICITADO, con importe = COTIZADO, aceptada = CONFIRMADO); así la máquina de estados no tiene estados inalcanzables y la cotización conserva su propio estado (EN_PROCESO / ACEPTADA / RECHAZADA).

## Trazabilidad
N1, N2, N4, N5; US-09 a US-13; BPMN: T4, T8, T10, T11, T15–T21; glosario: Orden de servicio, Servicio de transporte, Historial, Incidencia, Evidencia, Asignación.
