# language: en
@US-05 @RF-09 @RF-05
Feature: US-05 Confirmación y registro de cancelación
  As a responsable del servicio
  I want to que la confirmación y las cancelaciones queden registradas
  So that conservar quién solicitó la acción y por qué

  Scenario: Cancelación registrada con solicitante y motivo
    Given una orden CONFIRMADA
    When Cliente ACME solicita cancelar por "Ya no requiere el envío" y Operaciones la autoriza
    Then la orden queda CANCELADA
    And se conservan quién la solicitó y el motivo

  Scenario: Un rol sin autoridad no cancela
    Given una orden CONFIRMADA y que solo Operaciones puede cancelar
    When Ventas intenta autorizar la cancelación
    Then la API responde 422 con el código SinAutoridadParaCancelar
    And la orden sigue CONFIRMADA

  Scenario: Un servicio terminado no se cancela
    Given una orden ya CANCELADA o ENTREGADA
    When se solicita cancelar de nuevo
    Then la API responde 409 con el código TransicionDeEstadoInvalida
