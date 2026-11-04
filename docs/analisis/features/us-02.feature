# language: en
@US-02 @RF-02 @RNF-01
Feature: US-02 Elaboración de cotización
  As a vendedor
  I want to elaborar una cotización utilizando la información proporcionada por el cliente
  So that presentar al cliente una propuesta con su importe

  Scenario: Cotización elaborada
    Given una solicitud de cotización en estado SOLICITADO
    When Ventas registra el importe 1234.56 MXN
    Then el servicio pasa a COTIZADO
    And el importe se conserva exacto como Decimal

  Scenario: El importe debe ser positivo
    Given una solicitud de cotización en estado SOLICITADO
    When Ventas registra el importe 0
    Then la API responde 400 y la cotización sigue en SOLICITADO
