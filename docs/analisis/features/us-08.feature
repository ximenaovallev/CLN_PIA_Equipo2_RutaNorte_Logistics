# language: en
@US-08 @RF-07
Feature: US-08 Reasignación de operador
  As a responsable de Operaciones
  I want to actualizar la asignación cuando un operador no está disponible
  So that mantener la continuidad del servicio y conservar el historial del cambio

  Scenario: Reasignación con historial
    Given una orden UNIDAD_ASIGNADA con el operador OP-1
    And el operador OP-2 está disponible
    When Operaciones reasigna la orden a OP-2
    Then la asignación vigente es OP-2
    And el historial conserva la asignación anterior y registra la actualización
