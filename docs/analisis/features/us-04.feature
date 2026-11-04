# language: en
@US-04 @RF-08
Feature: US-04 Revisión de cambios operativos
  As a responsable de Operaciones
  I want to revisar los cambios que afectan una orden de servicio
  So that evitar que la operación continúe con condiciones no validadas

  Scenario: Un cambio pendiente bloquea la orden
    Given una orden CONFIRMADA
    When el cliente solicita cambiar el horario de recolección
    Then el cambio queda pendiente de revisión
    And asignar recursos responde 409 con el código CambioPendienteDeRevision

  Scenario: Operaciones revisa y la orden continúa
    Given una orden con un cambio pendiente
    When Operaciones aprueba o rechaza el cambio
    Then el cambio deja de estar pendiente y la orden puede continuar
