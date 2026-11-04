# language: en
@US-13 @RF-13 @RF-10
Feature: US-13 Evidencia y receptor
  As a operador
  I want to asociar la evidencia de recepción y entrega y registrar quién recibió
  So that que las evidencias permanezcan ligadas al servicio

  Scenario: Entrega con receptor y evidencia
    Given una orden en LLEGADA_A_DESTINO
    When el operador registra la entrega indicando quién recibió (INE-9) y una fotografía
    Then ambos quedan asociados a la orden y se conservan al recargarla

  Scenario: Entrega sin receptor
    Given una orden en LLEGADA_A_DESTINO
    When el operador registra la entrega sin identificar a quien recibe
    Then la API responde 400 con el código DatosInvalidos
    And la orden sigue en LLEGADA_A_DESTINO
