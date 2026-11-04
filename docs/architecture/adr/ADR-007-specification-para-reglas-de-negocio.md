# ADR-007: Specification (AND/OR/NOT) para las reglas de negocio componibles

**Estado:** Aceptada

## Contexto
Varias reglas del BRD son condiciones que se combinan y que deben explicar por qué fallan: la asignación exige *unidad adecuada Y operador disponible* (G2); la carga de alto valor exige *NO alto valor O autorizada* (S-02); un cambio pendiente bloquea la orden; la entrega exige *receptor identificado Y evidencia de entrega*. Con `if` anidados dentro de las entidades las reglas se duplican, no se reutilizan y no producen mensajes de negocio.

## Alternativas
| Opción | Ventaja | Problema |
|---|---|---|
| `if` dentro de los métodos | Simple | Se duplican; no se componen; mensajes de error ad hoc |
| Interfaz de política por regla (ADR-004) | Intercambiable | Una clase por política sin composición |
| **Specification con `&`, `\|`, `~`** | Reglas pequeñas y componibles; cada una explica su incumplimiento | Más clases |

## Decisión
`src/domain/especificaciones.py` define la base `Especificacion` con `es_satisfecha_por` y `motivos_de_incumplimiento`, los combinadores `Y`, `O`, `No` (operadores `&`, `|`, `~`) y 11 reglas concretas: `UnidadConCapacidadSuficiente`, `DentroDeLosLimitesDeLaEmpresa` (S-01), `OperadorDisponible`, `CargaDeAltoValor`, `AltoValorAutorizado`, `CambioOperativoPendiente`, `ReceptorIdentificado`, `EvidenciaDelEvento`, `CotizacionEnProceso`, `CotizacionConImporte`, `AceptadaPorElCliente` y fábricas (`asignacion_permitida()`, `control_de_alto_valor_cumplido()` = `~CargaDeAltoValor() | AltoValorAutorizado()`, `sin_cambio_pendiente()`, `entrega_documentada()`, `recepcion_documentada()`). `AsignadorDeRecursos` recibe la regla por constructor (inyectada con los límites S-01 desde la configuración).

## Consecuencias
- Beneficio: cambiar o ampliar una regla no toca el servicio; los mensajes de error salen de la propia regla; se prueban de forma aislada (`tests/unit/test_especificaciones.py`).
- Costo: más clases pequeñas; hay que cuidar que sus nombres sigan el glosario.
- El paquete de datos del profesor (reglas `puede_procesarse` y `beneficio_referencia`) se implementa con el mismo patrón en `tests/dataset/modelo_de_referencia.py`.

## Trazabilidad
RF-06, RF-08, RF-10, RF-13, RF-16; US-07, US-13, US-16; BPMN G2, G3, G4; diagrama `01b_especificaciones_eventos_y_estados`; reglas R-01 a R-09, R-11, R-12.
