# language: en
@US-12 @RF-13
Feature: US-12 Registro de llegada y entrega
  As a operador
  I want to registrar la llegada al destino y la realización de la entrega
  So that cerrar el servicio con los eventos correspondientes

  Scenario: Entrega completa
    Given una orden en LLEGADA_A_DESTINO
    When el operador registra la entrega con receptor y evidencia
    Then la orden queda ENTREGADA
    And se publica el evento EntregaRegistrada

  Scenario: No se entrega sin haber llegado
    Given una orden en CONFIRMADA
    When el operador intenta registrar la entrega
    Then la API responde 409 con el código TransicionDeEstadoInvalida
