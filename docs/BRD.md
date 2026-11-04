# BRD: Business Requirements Document — RutaNorte Logistics

Versión PIA (integra y refina el BRD de la Unidad 2 con el diseño de la Unidad 3 y la implementación). Equipo: Ximena Montserrat Ovalle Vallejo, Santiago Almanza Moreno, Javier Hernández Huerta. Curso: Componentes de Lógica de Negocio. Profesor: Miguel Ángel Gómez Marroquín.

> **Regla de este documento:** no se inventan políticas del negocio. Lo que el stakeholder no definió aparece como **supuesto pendiente de validar** (S-01 a S-05, `architecture/supuestos.md`).

## 1. Contexto del negocio
RutaNorte Logistics es una empresa de logística y transporte terrestre de mercancías entre Monterrey, Saltillo, Reynosa, San Luis Potosí y Querétaro. Atiende clientes empresariales recurrentes y servicios ocasionales. El costo depende de distancia, peso, volumen, tipo de unidad y características especiales de la carga.

El proceso inicia con la solicitud de cotización del cliente. Ventas prepara la cotización y, cuando el cliente la acepta, Operaciones genera la orden de servicio y coordina unidad, operador, ruta y horario de recolección. El operador recibe y valida la mercancía, registra incidencias y participa en el traslado y la entrega.

## 2. Problema y oportunidad
Los operadores reportan retrasos e incidentes por WhatsApp; Atención al Cliente depende de Operaciones para conocer el estado; las evidencias quedan dispersas y es difícil medir tiempos reales, retrasos, incidencias y cumplimiento. **Oportunidad:** centralizar la información de cada servicio, registrar estados y eventos, conservar evidencias asociadas, facilitar la consulta y generar información histórica.

## 3. Stakeholders
| Stakeholder | Interés / responsabilidad |
|---|---|
| Cliente | Solicita el servicio, proporciona información y acepta o rechaza la cotización. |
| Ventas | Recibe la solicitud, elabora la cotización y puede modificarla mientras está en proceso. |
| Operaciones | Genera la orden, coordina recursos, gestiona cambios e incidencias y da seguimiento. |
| Operador | Recolecta, valida la mercancía, reporta incidencias y registra la entrega. |
| Destinatario | Recibe la mercancía en el destino. |
| Atención al Cliente | Consulta estado, eventos, retrasos e incidencias para informar al cliente. |

## 4. Alcance
**Dentro:** solicitud y elaboración de cotización; aceptación y confirmación; generación de orden; asignación de unidad y operador; recepción y validación; actualización de estados; llegada y entrega; identificación del receptor; evidencias; incidencias; consulta de estado; indicadores históricos; **y, en el PIA,** API REST documentada, persistencia, contenedores, CI/CD y despliegue.

**Fuera (no definido por el stakeholder):** límites numéricos de peso/volumen/capacidad, controles concretos de alto valor, plazos de conservación de evidencias y autoridad final de cancelación. Se cubren como supuestos configurables; no se tratan como hechos.

## 5. Necesidades del negocio
| ID | Necesidad |
|---|---|
| N1 | Centralizar la información de los servicios. |
| N2 | Mejorar el seguimiento mediante estados y eventos registrados. |
| N3 | Reducir la dependencia de WhatsApp y facilitar la comunicación interna. |
| N4 | Conservar evidencias de recepción, entrega e incidencias asociadas al servicio. |
| N5 | Registrar y dar seguimiento a excepciones. |
| N6 | Permitir consultar información desde Atención al Cliente. |
| N7 | Obtener información histórica para medir tiempos, retrasos, incidencias y cumplimiento. |
| N8 | Aplicar controles adicionales a cargas de alto valor (condiciones por definir → supuesto S-02). |

## 6. Levantamiento (entrevista al Encargado de Operaciones)
**Proceso y estados.** El servicio inicia operativamente cuando el cliente acepta la cotización y se genera la orden; termina con la entrega registrada y su evidencia. Estados: solicitado, cotizado, confirmado, unidad asignada, recolectado, en tránsito, llegada a destino y entregado; cada cambio queda registrado.

**Responsables.** Ventas cotiza y modifica mientras está en proceso; si ya existe orden, los cambios que afectan la operación se revisan con Operaciones; Operaciones administra la orden y las asignaciones; el operador registra recepción, traslado, incidencias y entrega; Atención al Cliente consulta. La cancelación registra quién la solicita y el motivo; la autoridad final no se definió.

**Excepciones.** Operador no disponible, unidad averiada, mercancía diferente a la declarada, rechazada o dañada, dirección incorrecta, destinatario ausente, entrega parcial y situaciones de alto valor. Toda incidencia se documenta con evidencia y Operaciones decide el siguiente paso.

**Datos.** Cliente, origen, destino, mercancía (peso, dimensiones, características), fecha requerida, horario de recolección, unidad, operador, estado, incidencia, destinatario, evidencia de recepción y de entrega.

## 7. Restricciones
- No inventar políticas ni valores que el stakeholder no definió.
- La unidad asignada debe tener capacidad suficiente para la carga.
- Los cambios que afectan una orden se revisan con Operaciones.
- Las evidencias permanecen asociadas al servicio.
- Las excepciones deben poder registrarse y comunicarse a Operaciones.

## 8. Supuestos
Del BRD original: el cliente proporciona la información para cotizar; Ventas puede modificar mientras está en proceso; Operaciones coordina; el operador registra; Atención al Cliente consulta. **Supuestos adoptados en el diseño (por validar):** S-01 topes de capacidad, S-02 autorización de alto valor, S-03 conservación de evidencias, S-04 autoridad de cancelación (+ estado CANCELADO), S-05 definición de cumplimiento.

## 9. Criterios de éxito
1. La información de cada servicio está centralizada y es consultable.
2. El estado actual y los eventos importantes pueden consultarse.
3. Los cambios e incidencias quedan registrados con su contexto.
4. Las evidencias de recepción y entrega están asociadas al servicio.
5. Atención al Cliente obtiene información sin depender de mensajes dispersos.
6. Se consulta información histórica de tiempos, retrasos, incidencias y cumplimiento.

## 10. Requisitos refinados
Los requisitos funcionales (RF) y no funcionales (RNF) son la base de la trazabilidad (`architecture/trazabilidad.md`): cada uno enlaza historias, BPMN, endpoints, componentes y pruebas.

| ID | Necesidad | Requisito |
|---|---|---|
| RF-01 | N1 | Registrar la solicitud de cotización con origen, destino, mercancía, peso, dimensiones, fecha requerida y características especiales. |
| RF-02 | N1, N2 | Ventas elabora la cotización capturando su importe en MXN; el servicio pasa de SOLICITADO a COTIZADO. |
| RF-03 | N1 | Ventas puede modificar la solicitud solo mientras la cotización está en proceso; al modificarla debe elaborarse de nuevo el importe. |
| RF-04 | N1, N2 | El cliente acepta o rechaza la cotización elaborada; solo una cotización aceptada puede originar una orden. Pedir ajustes equivale a RF-03. |
| RF-05 | N1, N2 | La orden de servicio se genera después de la aceptación, queda CONFIRMADA y registra el primer evento en su historial. |
| RF-06 | N2, N5 | Operaciones asigna unidad y operador: la unidad debe tener capacidad suficiente y el operador debe estar disponible. |
| RF-07 | N2, N5 | Si el operador no está disponible, Operaciones reasigna y la asignación anterior permanece en el historial. |
| RF-08 | N2, N5 | Un cambio que afecta la operación se solicita a Operaciones y bloquea la orden hasta que se revise. |
| RF-09 | N1, N2, N5 | La cancelación de un servicio aceptado registra quién la solicita y el motivo; la autoridad es configurable (S-04). |
| RF-10 | N4, N5 | El operador registra la recepción de la mercancía con evidencia; el servicio pasa a RECOLECTADO. Las diferencias respecto a lo declarado se registran como incidencia. |
| RF-11 | N2 | Todo cambio de estado sigue el ciclo de vida del servicio (máquina de estados) y queda en el historial. |
| RF-12 | N3, N5 | Las incidencias y retrasos se registran en el sistema, sin cambiar el estado, con evidencia opcional, disponibles para Operaciones. |
| RF-13 | N4 | La entrega exige llegada a destino, receptor identificado y evidencia; si no es posible, se registra una incidencia y el servicio no se entrega. |
| RF-14 | N3, N6 | Atención al Cliente consulta estado, eventos, retrasos e incidencias de un servicio sin depender de Operaciones. |
| RF-15 | N7 | Se consultan indicadores históricos: tiempos reales de entrega, retrasos, incidencias y cumplimiento (S-05). |
| RF-16 | N8 | Una carga de alto valor requiere la autorización de Operaciones antes de asignar recursos (S-02). |
| RNF-01 | N1 | Los importes son Decimal con dos decimales (nunca float). |
| RNF-02 | — | La API REST responde con 200/201/400/404/409/422 y está documentada con OpenAPI (Swagger UI en /docs). |
| RNF-03 | — | La configuración (BD, supuestos S-01/S-03/S-04) llega por variables de entorno (12-Factor); no hay secretos en el repositorio. |
| RNF-04 | — | Cobertura de pruebas de al menos 80 % verificada en CI. |
| RNF-05 | N1, N4 | Cada caso de uso es una transacción: si falla, no queda ningún cambio (Unit of Work). |
| RNF-06 | — | Trazabilidad verificable BRD → regla → componente → prueba. |

## 11. Refinamientos respecto a la Unidad 2
| Tema | Unidad 2 | PIA | Motivo |
|---|---|---|---|
| Elaboración de la cotización | Estado COTIZADO sin dato asociado | La cotización captura un **importe** (Decimal); sin importe = SOLICITADO, con importe = COTIZADO | Evita estados inalcanzables y permite medir (RNF-01) |
| Aceptación | «Se registra la respuesta» | Solo una cotización **elaborada** puede aceptarse; pedir ajustes = modificar y volver a elaborar | Coherencia con US-02, US-03 y US-17 |
| Cancelación | Pendiente | Estado CANCELADO, registro de solicitante y motivo, autoridad configurable (S-04) | Exigido por el BRD («debe registrarse») |
| Alto valor | Pendiente | Autorización de Operaciones antes de asignar (S-02) | N8 |
| Cambios posteriores a la orden | Se revisan con Operaciones | Un cambio pendiente bloquea la orden hasta su revisión (RF-08) | US-04 |
| Cumplimiento | Sin definición | Entregas en o antes de la fecha requerida ÷ entregas (S-05) | N7 |
| Historias | 17 con un criterio genérico | 17 con escenarios concretos (feliz + excepción), endpoint y pruebas | Verificabilidad |

## 12. Documentos relacionados
Historias de usuario y Gherkin: `analisis/historias_de_usuario.md` y `analisis/features/` · BPMN: `analisis/bpmn/` · Glosario: `analisis/glosario.md` · Arquitectura: `architecture/` · API: `api/openapi.json`.
