# language: en
@US-15 @RF-15
Feature: US-15 Indicadores históricos
  As a responsable de Operaciones
  I want to consultar información histórica sobre tiempos, retrasos, incidencias y cumplimiento
  So that medir el desempeño de la operación

  Scenario: Indicadores del periodo
    Given una entrega en plazo y otra tardía respecto de su fecha requerida
    When Operaciones consulta los indicadores del periodo
    Then entregas realizadas = 2, entregas a tiempo = 1 y cumplimiento = 0.5 (S-05)

  Scenario: Sin entregas no hay cumplimiento
    Given un periodo sin entregas
    When se consultan los indicadores
    Then el cumplimiento no está definido (null)
