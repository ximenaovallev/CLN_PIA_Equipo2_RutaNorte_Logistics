# Glosario (versión PIA)

Lenguaje ubicuo del proyecto. Se conservan los 26 términos de la Unidad 2, se **corrigen** los que cambiaron al diseñar la arquitectura y se **agregan** los nuevos (Unidad 3 y PIA).
La columna «Nombre en diagramas y código» es el nombre exacto usado en el diagrama de clases, los secuencias y `src/`.
**S-0x** = supuesto pendiente de validar con el stakeholder (`architecture/supuestos.md`).

## A. Términos de la Unidad 2 (sin cambios)
| Término | Definición | Nombre en diagramas y código |
|---|---|---|
| Cotización | Propuesta de servicio preparada por Ventas con base en la información proporcionada por el cliente. | `Cotizacion` |
| Solicitud de cotización | Petición inicial del cliente con los datos necesarios para cotizar. | `SolicitudDeCotizacion` |
| Cliente | Persona o empresa que solicita el servicio de transporte. | `Cliente`, `cliente_id` |
| Ventas | Área que recibe solicitudes y prepara cotizaciones. | rol «Ventas» |
| Operaciones | Área que coordina la ejecución del servicio, asignaciones y seguimiento de incidencias. | rol «Operaciones» |
| Atención al Cliente | Área que consulta estado, eventos, retrasos e incidencias para informar al cliente. | rol «Atención al Cliente» |
| Operador | Persona responsable de la recolección, el traslado, el reporte y la entrega. | `Operador` |
| Unidad | Vehículo utilizado para transportar la mercancía. | `Unidad` |
| Asignación | Registro de la unidad y el operador que atenderán un servicio. | `Asignacion` |
| Mercancía | Carga que será transportada mediante el servicio. | `Mercancia` |
| Origen / Destino | Lugar de recolección / lugar al que debe llegar la mercancía. | `origen`, `destino` (`Ubicacion`) |
| Entrega | Actividad mediante la cual la mercancía es recibida en el destino. | `registrar_entrega` |
| Destinatario | Persona que recibe la mercancía en el destino. | `Destinatario` |
| Historial | Registro cronológico de estados, eventos y cambios de un servicio. | `EntradaDeHistorial` |
| Incidencia | Situación que afecta o puede afectar el desarrollo normal del servicio. | `Incidencia`, `TipoDeIncidencia` |
| Evidencia | Fotografía o documento asociado con la recepción, la entrega o una incidencia. | `Evidencia` |
| Retraso | Demora del servicio respecto de lo esperado; se registra como incidencia. | `TipoDeIncidencia.RETRASO` |
| Indicador | Medida de tiempos, retrasos, incidencias y cumplimiento de entregas. | `IndicadoresDTO` |

## B. Términos corregidos
| Término | Definición corregida | Motivo | Nombre en diagramas y código |
|---|---|---|---|
| Orden de servicio | Registro generado tras la aceptación de la cotización que coordina la operación. **Incluye el seguimiento del servicio**: estado, asignación, historial, incidencias y evidencias. | En el diseño, Orden y Servicio forman un solo agregado (ADR-005). | `OrdenDeServicio` |
| Servicio de transporte | Traslado solicitado de mercancía de un origen a un destino. Una vez aceptado se gestiona y rastrea mediante su orden de servicio. | Se identifica con su orden (ADR-005). | `OrdenDeServicio` |
| Recolección | Actividad en la que el operador recibe y valida la mercancía en origen. Su registro se llama **recepción** y genera la evidencia de recepción; el servicio pasa a «Recolectado». | Se unifica «recolección» (actividad) y «recepción» (registro). | `registrar_recepcion`, `EstadoServicio.RECOLECTADO` |
| Estado del servicio | Situación del servicio en su ciclo: solicitado, cotizado, confirmado, unidad asignada, recolectado, en tránsito, llegada a destino, entregado y **cancelado** (S-04). | Se agrega el estado terminal «cancelado». | `EstadoServicio` |
| Cancelación | Terminación de un servicio ya aceptado; registra quién la solicita y el motivo. La autoridad para autorizarla es el supuesto S-04 (Operaciones). | Se modela como estado y registro. | `Cancelacion`, `cancelar` |
| Capacidad | Carga (peso y volumen) que una unidad puede transportar. La unidad debe tener capacidad suficiente; los topes propios de la empresa son el supuesto S-01. | Se concreta con S-01. | `Capacidad`, `Peso`, `Volumen` |
| Carga de alto valor | Mercancía marcada como de alto valor, que requiere autorización antes de asignar recursos (S-02); los controles definitivos dependen de las políticas de la empresa. | Se concreta con S-02. | `Mercancia.alto_valor` |

## C. Términos nuevos
| Término | Definición | Nombre en diagramas y código |
|---|---|---|
| Fecha requerida | Fecha en que el cliente necesita el servicio; es la referencia para medir el cumplimiento de entregas. | `fecha_requerida` |
| Cumplimiento de entregas | Proporción de entregas realizadas en o antes de la fecha requerida respecto de las entregas realizadas (S-05). | `cumplimiento_de_entregas` |
| Autorización de carga de alto valor | Aprobación de Operaciones, previa a la asignación, para una carga de alto valor (S-02). | `autorizar_alto_valor` |
| Especificación | Regla de negocio pequeña y componible (Y, O, NO) que dice si algo se cumple y, si no, por qué (ADR-007). Reemplaza a la «política de capacidad» de la Unidad 3. | `Especificacion`, `UnidadConCapacidadSuficiente`, `OperadorDisponible`… |
| Importe | Monto en MXN de una cotización elaborada por Ventas; siempre Decimal con dos decimales. | `importe_mxn` |
| Cotización elaborada | Cotización a la que Ventas ya le asignó importe; el servicio está COTIZADO. | `CotizacionConImporte` |
| Cambio operativo | Solicitud posterior a la orden que afecta la operación; queda pendiente hasta que Operaciones la revisa y mientras tanto bloquea la orden. | `CambioOperativo`, `CambioOperativoPendiente` |
| Máquina de estados | Tabla que declara qué cambios de estado son válidos y a qué estado llevan (ADR-008). | `MaquinaDeEstados`, `CICLO_DE_VIDA_DEL_SERVICIO` |
| Disparador | Hecho del proceso que provoca un cambio de estado (p. ej. registrar recepción). | `Disparador` |
| Acciones permitidas | Disparadores válidos desde el estado actual de una orden; se muestran en la consulta de estado. | `acciones_permitidas` |
| Evento de dominio | Hecho del negocio ya ocurrido, publicado después de confirmar la transacción (ADR-012). | `EventoDeDominio` y subclases |
| Política de conservación | Plazo durante el cual se conservan las evidencias; sin plazo por defecto (S-03). | `PoliticaDeConservacion` |
| Autoridad de cancelación | Conjunto de roles que pueden cancelar un servicio; por defecto, Operaciones (S-04). | `AutoridadDeCancelacion` |
| Registro centralizado del servicio | Fuente única de estados, eventos, incidencias, evidencias e historial de cada servicio. | `IConsultaDeServicios`, tablas `ordenes`, `orden_historial`… |
| Supuesto pendiente de validar | Decisión sobre el negocio que el BRD no definió y que debe confirmar el stakeholder. | S-01 a S-05 |

## D. Vocabulario de arquitectura (no pertenece al negocio)
| Término | Significado en este proyecto | Ejemplo |
|---|---|---|
| Aggregate / raíz | Grupo de objetos con un límite de consistencia y una raíz que controla los cambios. | `OrdenDeServicio`, `Cotizacion` |
| Value Object | Concepto definido por sus valores, sin identidad propia. | `Asignacion`, `Mercancia` |
| Domain Service | Comportamiento del dominio que no pertenece a una sola entidad. | `AsignadorDeRecursos` |
| Specification | Patrón que encapsula una regla como objeto combinable con Y/O/NO. | `Especificacion` |
| State Machine | Patrón que modela el ciclo de vida como estados y transiciones declaradas. | `MaquinaDeEstados` |
| Command / Query | Intención de cambiar / consultar, con su handler (CQRS básico). | `AsignarRecursosCommand`, `ConsultarEstadoDelServicioQuery` |
| DTO / View Model | Objeto de lectura que no se usa para escribir. | `EstadoDelServicioDTO` |
| Domain Event | Hecho del negocio que ya ocurrió. | `RecursosAsignados`, `EntregaRegistrada` |
| Repository | Interfaz del dominio para recuperar y guardar objetos, sin exponer SQL. | `IOrdenServicioRepository` |
| Unit of Work | Límite transaccional de un caso de uso. | `IUnitOfWork` |
| Command / Query | Operación que cambia el estado / operación que solo consulta. | `AsignarRecursosCommand`, `ConsultarEstadoDelServicioQuery` |
| Handler (Application Service) | Clase que coordina un caso de uso sin contener las reglas del negocio. | `AsignarRecursosHandler` |
| DTO / View Model | Modelo de lectura, distinto del modelo de escritura. | `EstadoDelServicioDTO` |
