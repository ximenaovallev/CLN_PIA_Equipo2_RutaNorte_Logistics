# Paquete de datos del profesor (02_RutaNorte_Logistics): uso, correspondencias y diferencias

El LEEME del paquete aclara que sus reglas, estados e importes son un **«modelo de pruebas propuesto»** y que, si difieren de los requerimientos del equipo, se deben **documentar las diferencias y adaptar fixtures y oráculos, sin reemplazar los requerimientos propios**. Esta página es esa documentación. Los datos están en `tests/data/paquete/`; el adaptador, en `tests/dataset/`; la evidencia de la ejecución, en `docs/evidencias/`.

## 1. Qué se hizo con cada archivo
| Archivo | Contenido | Uso |
|---|---|---|
| `actores.csv` | 40 clientes (preferente, activo, ciudad) | Se registran como `Cliente` por el caso de uso real; `activo` y `preferente` solo se usan en las reglas de referencia |
| `catalogo.csv` | 20 servicios con precio, capacidad y habilitado | Precio × cantidad para calcular el **total con Decimal** de la cotización |
| `operaciones.csv` + `detalle_operaciones.csv` | 60 operaciones y 117 líneas (2 operaciones sin líneas) | Cada operación se convierte en solicitud → cotización (importe = total) → aceptación (campo `autorizado`) → orden |
| `casos_prueba.csv` | 120 casos: 60 `validar_operacion`, 60 `evaluar_beneficio` | Se evalúan con Specifications (mismo patrón del dominio) y se comparan con un **oráculo independiente** escrito con expresiones planas |
| `transiciones_prueba.csv` | 20 acciones sobre operaciones REGISTRADO | Se ejecutan con el **código real** (handlers + base de datos) y se comparan con el oráculo de transición |

## 2. Correspondencia de conceptos
| Paquete | Dominio del equipo | Nota |
|---|---|---|
| Actor (cliente) | `Cliente` | `activo` / `preferente` no existen en el BRD |
| Recurso del catálogo | Línea de servicio que determina el **importe** de la `Cotizacion` | El BRD no define tarifas; el importe se captura |
| Operación | `Cotizacion` aceptada + `OrdenDeServicio` | |
| `autorizado = 1` | El cliente **acepta** la cotización (RF-04) | `autorizado = 0` → no se genera orden (`OrdenNoGenerable`, 422) |
| Detalle no vacío | Importe > 0 (RF-02) | Sin líneas → `DatosInvalidos` (400) al elaborar |
| REGISTRADO | CONFIRMADO | Orden generada |
| ASIGNADO | UNIDAD_ASIGNADA (y RECOLECTADO) | |
| EN_RUTA | EN_TRANSITO (y LLEGADA_A_DESTINO) | |
| ENTREGADO / CANCELADO | ENTREGADO / CANCELADO | CANCELADO viene del supuesto S-04 |
| `completar` | Recorrido completo: asignar → recepción → traslado → llegada → entrega | |
| `aprobar` | Asignar unidad y operador | |
| `saltar_estado` | Registrar la entrega desde CONFIRMADO | Rechazada con 409 |

## 3. Diferencias documentadas y cómo se trataron
| # | Diferencia | Decisión | Dónde queda |
|---|---|---|---|
| D-1 | **Repetir la aprobación** es, en el paquete, una transición inválida; en el BRD (US-08) **reasignar es válido** y conserva el historial | El oráculo espera `UNIDAD_ASIGNADA` y evento `RecursosAsignados`, no una excepción | `oraculo_de_transicion`, prueba `test_diferencia_documentada_repetir_aprobacion_es_una_reasignacion_valida` |
| D-2 | El paquete define **5 estados** y el BRD **9** (además: solicitado, cotizado, recolectado y llegada a destino) | Se usa la tabla del BRD y se muestra el estado equivalente del paquete en la columna `equivalente_en_el_paquete` | `ESTADO_DE_REFERENCIA`, CSV de transiciones |
| D-3 | Cliente **activo / preferente**, **promoción** y **beneficio de referencia** no aparecen en el BRD | No se agregan al dominio (no se reemplazan requerimientos propios); las reglas `puede_procesarse` y `beneficio_referencia` se implementan como Specifications solo en el adaptador de pruebas | `tests/dataset/modelo_de_referencia.py` |
| D-4 | Catálogo con `habilitado` y `capacidad_o_stock` | No hay catálogo en el BRD. Se valida en el adaptador (6 operaciones usan un servicio deshabilitado; ninguna cantidad excede la capacidad) pero no bloquea el flujo del dominio | `ServiciosHabilitados`, `CantidadesDentroDeLaCapacidad` |
| D-5 | Todas las operaciones arrancan **REGISTRADO**, incluso las no autorizadas o sin detalle | Esas operaciones no llegan a CONFIRMADO en el dominio: el oráculo espera `SIN_ORDEN` con `OrdenNoGenerable` (422) o `DatosInvalidos` (400) | CSV de transiciones (ENV-S008, S013, S016) |
| D-6 | Cliente inactivo (p. ej. ENV-C007) | El BRD no define clientes inactivos; el dominio los procesa. Solo la regla de referencia `puede_procesarse` lo considera | `ActorActivo` |

## 4. Resultados
| Ejecución | Resultado |
|---|---|
| 120 casos de reglas | 120 PASA — `puede_procesarse` verdadero en 44 operaciones y falso en 16; `beneficio_referencia` verdadero en 11 y falso en 49 |
| 20 transiciones | 20 PASA (ver `docs/evidencias/transiciones_resultados.csv`) |
| Importes | Calculados con `Decimal`; total máximo 12 059.00 MXN, mínimo 676.00 MXN entre operaciones con detalle |

Reproducir: `python scripts/ejecutar_paquete.py` (con `DATABASE_URL` apunta a PostgreSQL; sin ella usa SQLite en memoria) y `pytest tests/integration/test_paquete_de_datos.py`.
