# language: en
@US-09 @RF-10
Feature: US-09 Recepción y validación de mercancía
  As a operador
  I want to registrar la recepción y validar la mercancía contra lo declarado
  So that detectar diferencias desde el origen y conservar la evidencia

  Scenario: Recepción con evidencia
    Given una orden UNIDAD_ASIGNADA
    When el operador registra la recepción con una fotografía de recepción
    Then la orden pasa a RECOLECTADO
    And la evidencia queda asociada a la orden

  Scenario: Recepción sin evidencia válida
    Given una orden UNIDAD_ASIGNADA
    When el operador registra la recepción con una evidencia de otro evento
    Then la API responde 400 con el código DatosInvalidos

  Scenario: Mercancía diferente a la declarada
    Given mercancía distinta a lo declarado
    When el operador registra una incidencia MERCANCIA_DIFERENTE con evidencia
    Then la incidencia queda en el historial sin cambiar el estado
