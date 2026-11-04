# ADR-008: State Machine explícita para el ciclo de vida del servicio

**Estado:** Aceptada

## Contexto
El BRD define ocho estados (solicitado, cotizado, confirmado, unidad asignada, recolectado, en tránsito, llegada a destino, entregado) y exige registrar cada cambio. El supuesto S-04 agrega CANCELADO. En la Unidad 3 la validez de cada transición estaba repartida en condiciones dentro de cada método.

## Alternativas
1. Condicionales por método (`if self._estado != ...`): se repiten y es fácil olvidar una.
2. Patrón State con una clase por estado: demasiadas clases para transiciones sin comportamiento propio.
3. **Tabla de transiciones** `(estado, disparador) → estado` con una clase genérica `MaquinaDeEstados`.

## Decisión
`src/domain/maquina_de_estados.py` declara `EstadoServicio` (9 estados), `Disparador` (8 hechos del proceso, cada uno ligado a una tarea del BPMN) y la tabla `CICLO_DE_VIDA_DEL_SERVICIO`. `OrdenDeServicio` y `Cotizacion` llaman a `CICLO.aplicar(...)`; un movimiento no declarado lanza `TransicionDeEstadoInvalida` con el mensaje «No se puede X en estado Y (se requiere A o B)», que la API traduce a 409. La consulta de estado muestra las **acciones permitidas** leyendo la misma tabla. El diagrama `02_estados_del_servicio` se **genera** desde la tabla, por lo que no puede divergir.

## Consecuencias
- Beneficio: una sola fuente de verdad; pruebas de propiedades (todos los estados alcanzables, ninguno no terminal sin salida, todo disparador usado).
- Costo: los disparadores deben mantenerse alineados con el BPMN.
- Reasignar (US-08) es una transición UNIDAD_ASIGNADA → UNIDAD_ASIGNADA; es la diferencia con el flujo de referencia del paquete del profesor (ver `paquete_de_datos.md`).

## Trazabilidad
RF-11; US-10; BPMN T4, T8, T10, T11, T16, T19, T5A; regla R-10; pruebas `tests/unit/test_maquina_de_estados.py`.
