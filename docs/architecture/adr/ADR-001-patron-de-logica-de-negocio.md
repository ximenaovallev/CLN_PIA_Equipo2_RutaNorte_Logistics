# ADR-001: Domain Model como patrón principal de lógica de negocio

**Estado:** Aceptada

## Contexto
RutaNorte Logistics debe controlar el ciclo de vida de una orden de servicio con ocho estados (solicitado, cotizado, confirmado, unidad asignada, recolectado, en tránsito, llegada a destino, entregado), nueve excepciones (operador no disponible, unidad averiada, mercancía diferente/rechazada/dañada, dirección incorrecta, destinatario ausente, entrega parcial) y un historial de cambios obligatorio. Reglas conocidas: la orden solo nace de una cotización aceptada; una cotización solo se modifica mientras está en proceso; la unidad debe tener capacidad suficiente y el operador debe estar disponible; las evidencias deben quedar asociadas al servicio; los cambios posteriores a la orden se revisan con Operaciones.
Pendientes del BRD (no se inventan; ver `docs/architecture/supuestos.md`): límites numéricos de capacidad, controles de alto valor, conservación de evidencias, autoridad para cancelar.

## Alternativas
| Criterio del caso | Transaction Script | Table Module | Domain Model |
|---|---|---|---|
| Complejidad de reglas | Reglas repartidas en un script por operación; se duplican (p. ej. validar estado en cada script). | Reglas por tabla; difícil expresar reglas que cruzan orden, unidad y operador. | Reglas junto a los datos que protegen (orden, cotización). |
| Cambios esperados | Cada política nueva (capacidad, alto valor) toca varios scripts. | Cambios localizados por tabla, pero reglas cruzadas se dispersan. | Cambios en una clase o en una política intercambiable. |
| Interacción entre conceptos | Coordinación manual y repetida. | Débil entre módulos. | Natural: orden ↔ asignación ↔ incidencias ↔ evidencias. |
| Estados e invariantes | Se validan por convención. | Se validan por convención. | La raíz del agregado impide transiciones inválidas. |
| Costo | Bajo al inicio, alto al crecer. | Medio. | Mayor modelado inicial y curva de aprendizaje. |

## Decisión
Se usa **Domain Model** para el proceso de cotización, orden de servicio, asignación, entrega e incidencias. Se acepta un enfoque simple (consulta directa, sin dominio rico) solo para la lectura de indicadores e historial (ver ADR-003).

## Evolución en el PIA
El Domain Model se completó con tres patrones que lo hacen explícito y verificable: **Specification** para las reglas componibles (ADR-007), **State Machine** para el ciclo de vida (ADR-008) y **Domain Events** publicados tras confirmar la transacción (ADR-012).

## Consecuencias
- Beneficio: las transiciones de estado, el historial y las excepciones quedan protegidos en `OrdenDeServicio`.
- Costo: más clases y más diseño previo; el equipo debe mantener el lenguaje ubicuo del glosario.
- Riesgo: sobre-modelar. Se mitiga modelando solo lo que aparece en el BRD.

## Trazabilidad
Necesidades N1, N2, N4, N5; US-03, US-06, US-07, US-08, US-10, US-11, US-12, US-17; BPMN: G1 (¿Respuesta del cliente?), G2 (¿Unidad adecuada y operador disponible?), G3 (¿Coincide con lo declarado?), G4 (¿Entrega posible, completa y sin daño?); CU-01 a CU-04.
