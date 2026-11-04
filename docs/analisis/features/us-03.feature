# language: en
@US-03 @RF-03
Feature: US-03 Modificación de cotización
  As a vendedor
  I want to modificar una cotización mientras está en proceso
  So that corregir o ajustar la información antes de que el cliente responda

  Scenario: Modificación mientras está en proceso
    Given una cotización en proceso
    When Ventas cambia el destino a Guadalajara
    Then la información actualizada queda registrada

  Scenario: No se modifica una cotización ya respondida
    Given una cotización que el cliente rechazó
    When Ventas intenta modificarla
    Then la API responde 409 con el código CotizacionNoModificable
