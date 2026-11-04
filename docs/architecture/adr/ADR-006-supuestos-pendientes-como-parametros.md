# ADR-006: Los pendientes del BRD se modelan como supuestos explícitos y configurables

**Estado:** Propuesta (los supuestos deben validarse con el stakeholder)

## Contexto
El BRD dejó sin definir los límites de capacidad, los controles de carga de alto valor, la conservación de evidencias, la autoridad de cancelación y la definición de "cumplimiento de entregas". La guía prohíbe inventar reglas, pero permite supuestos identificados como pendientes de validar. Un diseño que ignora esos puntos no puede completarse ni probarse.

## Alternativas
1. Dejarlos sin modelar: respeta el BRD pero deja huecos en el diseño y en las pruebas.
2. Fijar valores concretos (p. ej. "máximo 20 t", "conservar 5 años"): inventa políticas del negocio.
3. **Supuestos explícitos y configurables**: se implementa el mecanismo, el valor es un parámetro y cada supuesto queda numerado, documentado y probado.

## Decisión
Se adoptan los supuestos S-01 a S-05 descritos en `docs/architecture/supuestos.md`. Ninguno fija una cifra del negocio: S-01 y S-03 usan `None` (sin tope / sin caducidad) por defecto y se configuran con las variables de entorno `LIMITE_PESO_KG`, `LIMITE_VOLUMEN_M3` y `DIAS_CONSERVACION_EVIDENCIAS`; S-04 con `ROLES_QUE_CANCELAN`; S-02 y S-04 asumen que Operaciones autoriza; S-05 calcula el cumplimiento contra la fecha requerida del cliente. Se agrega el estado `CANCELADO`.

## Consecuencias
- Beneficio: el diseño queda completo, probado y cada decisión es reversible sin tocar la arquitectura.
- Costo: más código (2 handlers, 2 políticas, 1 estado) que podría cambiar si el stakeholder responde distinto.
- Riesgo: que un supuesto se tome por regla real; se mitiga marcándolos en código, diagramas y documentos.
- Trabajo posterior: confirmar cada supuesto con el stakeholder y actualizar este ADR a "Aceptada" o "Reemplazada".

## Trazabilidad
N8, N4, N5, N7; US-05, US-16; BPMN: G2, S2, T5, G5, T5A, E2; pruebas `test_s01_*` a `test_s05_*`.
