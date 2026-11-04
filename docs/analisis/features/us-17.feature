# language: en
@US-17 @RF-04 @RF-03
Feature: US-17 Respuesta a la cotización
  As a cliente
  I want to aceptar, rechazar o solicitar ajustes a la cotización recibida
  So that decidir si contrato el servicio

  Scenario: El cliente acepta
    Given una cotización elaborada (COTIZADO)
    When el cliente la acepta
    Then la cotización queda ACEPTADA y puede generarse la orden
    And se publica el evento CotizacionAceptada

  Scenario: El cliente rechaza
    Given una cotización elaborada
    When el cliente la rechaza
    Then la cotización queda RECHAZADA y no admite otra respuesta

  Scenario: El cliente pide ajustes
    Given una cotización elaborada
    When el cliente pide ajustes y Ventas modifica la solicitud
    Then el importe debe elaborarse de nuevo antes de poder aceptarla

  Scenario: No se acepta una cotización sin elaborar
    Given una cotización en estado SOLICITADO
    When el cliente intenta aceptarla
    Then la API responde 422 con el código CotizacionNoElaborada
