# ADR-004: Capacidad de la unidad mediante la abstracción PoliticaDeCapacidad

**Estado:** Reemplazada por ADR-007 (Specification)

## Contexto
El stakeholder confirmó que la unidad debe tener capacidad suficiente, pero los límites "tendrían que definirse según las políticas y capacidades de la empresa". El BRD prohíbe inventar valores.

## Decisión original (Unidad 3)
Una interfaz `PoliticaDeCapacidad.permite(unidad, mercancia)` usada por `AsignadorDeRecursos`, con una implementación `PoliticaDeCapacidadEmpresa`.

## Por qué se reemplazó
La revisión de la Unidad 3 señaló que la regla de alto valor seguía fija en `OrdenDeServicio` y que la abstracción tenía una sola implementación. En el PIA la regla de asignación se expresa como una **Specification** compuesta (`UnidadConCapacidadSuficiente & DentroDeLosLimitesDeLaEmpresa & OperadorDisponible`), que además reporta los motivos de incumplimiento y es reutilizable para alto valor, cambios pendientes y evidencias. `PoliticaDeCapacidad` dejó de existir en el código.

## Consecuencias
Ver ADR-007. El supuesto S-01 se conserva como `DentroDeLosLimitesDeLaEmpresa(peso_maximo_kg, volumen_maximo_m3)`.

## Trazabilidad
N8; US-07, US-16; reglas R-04 a R-06 de `trazabilidad.md`.
