# Documento de decisiones técnicas

Resume las decisiones de arquitectura e implementación del PIA, por qué se tomaron y dónde viven en el código. El detalle (alternativas, consecuencias) está en los ADR (`adr/`).

## 1. Mapa DDD → código
| Concepto | Elementos | Ubicación |
|---|---|---|
| Aggregates (raíz) | `Cotizacion`, `OrdenDeServicio` (con historial, incidencias, evidencias, asignación, cancelación, cambio pendiente) | `src/domain/cotizacion.py`, `orden_de_servicio.py` (ADR-005) |
| Entidades de apoyo | `Cliente`, `Unidad`, `Operador` | `src/domain/cliente.py`, `recursos.py` |
| Value Objects | `Mercancia`, `Peso`, `Volumen`, `Dimensiones`, `Capacidad`, `Ubicacion`, `Horario`, `Asignacion`, `Destinatario`, `Evidencia`, `SolicitudDeCotizacion`, `PoliticaDeConservacion` (inmutables, validan al construirse) | `src/domain/valores.py` |
| Domain Services | `AsignadorDeRecursos`, `AutoridadDeCancelacion` | `src/domain/servicios.py` |
| Domain Events | 11 eventos | `src/domain/eventos.py` (ADR-012) |
| Repositories (puertos) | 5 interfaces | `src/domain/repositorios.py` (ADR-002) |
| Specification | base + `Y`/`O`/`No` + 11 reglas | `src/domain/especificaciones.py` (ADR-007) |
| State Machine | tabla de 13 transiciones, 9 estados, 8 disparadores | `src/domain/maquina_de_estados.py` (ADR-008) |
| Service Layer / CQRS | 19 commands, 7 queries, un handler por caso de uso | `src/application/` (ADR-003) |
| Infraestructura | SQL (SQLAlchemy Core), memoria, composición, configuración | `src/infrastructure/` (ADR-009, 011) |
| API | FastAPI, esquemas, tabla de errores | `src/api/` (ADR-010) |

Regla de dependencias: `api → application → domain ← infrastructure`; el dominio no importa ninguna librería externa (verificable: `src/domain` solo usa la biblioteca estándar). Diagrama: `diagramas/04_capas_y_componentes`.

## 2. Principios SOLID aplicados
| Principio | Evidencia |
|---|---|
| S — responsabilidad única | Un handler por caso de uso; cada Specification expresa una sola regla; la API solo traduce |
| O — abierto/cerrado | Nuevas reglas = nueva Specification sin editar `AsignadorDeRecursos`; nueva persistencia = nueva implementación de los puertos |
| L — sustitución | `EnMemoriaUnitOfWork` y `SqlUnitOfWork` son intercambiables: las mismas pruebas pasan con ambas |
| I — segregación | Puertos pequeños: `IUnitOfWork`, `IPublicadorDeEventos`, `IConsultaDeServicios` (lectura) separado de los repositorios (escritura) |
| D — inversión | Los handlers dependen de abstracciones; `composicion.py` es el único lugar que elige implementaciones |

## 3. Decisiones transversales
| Decisión | Razón |
|---|---|
| Importes `Decimal` + `Numeric(12,2)` | Evitar errores de punto flotante en dinero (RNF-01); probado con el paquete (`test_total_se_calcula_con_decimal…`) |
| Fechas en UTC | SQLite no conserva zona horaria; se normaliza al guardar y al leer |
| Errores de dominio con nombre | La API traduce por nombre a 400/404/409/422 sin que el dominio conozca HTTP |
| Resultado en vez de excepciones en los handlers | Los casos de uso devuelven `Resultado(exito, mensaje, codigo)`; no se filtran excepciones de dominio a la capa web |
| Eventos tras el commit | Sin eventos de cambios revertidos (ADR-012) |
| Mismo contrato en memoria y SQL | Prueba que el dominio no depende de la tecnología (ADR-002/009) |
| Supuestos configurables | No se inventan políticas del negocio (ADR-006) |

## 4. Estrategia de pruebas
- **Unitarias** (`tests/unit/`): máquina de estados (propiedades), Specifications, invariantes del dominio.
- **Integración** (`tests/integration/`): casos de uso, supuestos, persistencia, API y paquete de datos. Cada prueba de comportamiento se ejecuta sobre **memoria, SQLite y PostgreSQL** (fixture `backend`; PostgreSQL cuando existe `TEST_DATABASE_URL`).
- **Trazabilidad** (`tests/test_trazabilidad.py`): comprueba que cada prueba, componente, endpoint y elemento BPMN citado en la matriz exista, que cada requisito esté cubierto y que los diagramas coincidan con el código.
- **Cobertura**: ≥ 80 % exigida en CI y en Compose; el valor medido se registra en el reporte final.

## 5. Limitaciones conocidas (honestidad técnica)
| Limitación | Impacto | Mejora |
|---|---|---|
| Sin autenticación ni autorización en la API | El rol (`rol_que_autoriza`, `autorizado_por`) lo declara quien llama | Agregar OAuth2/JWT y derivar el rol del token |
| Esquema creado con `create_all`, sin migraciones | Cambios de esquema requieren recrear | Alembic |
| Eventos sin *outbox* | Un fallo entre commit y publicación pierde el evento | Patrón outbox (ADR-012) |
| Consultas reconstruyen agregados | Indicadores recorren todas las órdenes | SQL directo o vista materializada |
| Evidencias guardadas como referencia (URL/folio), no como archivo | El almacenamiento del archivo queda fuera | Almacenamiento de objetos (S3) |
| Plan gratuito de Render duerme el servicio | Primera petición lenta | Abrir `/health` antes de la demostración |
| Los supuestos S-01 a S-05 siguen sin validarse con el stakeholder | Pueden cambiar reglas | Confirmarlos y actualizar ADR-006 |
