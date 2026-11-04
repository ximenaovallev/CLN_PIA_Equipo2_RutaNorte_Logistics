# language: en
@US-11 @RF-12
Feature: US-11 Registro de incidencias
  As a operador
  I want to reportar incidencias y retrasos ocurridos durante el servicio
  So that que Operaciones conozca la situación sin depender de WhatsApp

  Scenario: Incidencia durante el traslado
    Given una orden EN_TRANSITO
    When el operador reporta un RETRASO por tráfico
    Then la incidencia queda registrada y disponible para Operaciones
    And el estado sigue EN_TRANSITO

  Scenario: Destinatario ausente
    Given una orden en LLEGADA_A_DESTINO
    When el operador registra DESTINATARIO_AUSENTE con evidencia
    Then la orden NO pasa a ENTREGADO
    And la incidencia queda con su evidencia

  Scenario: Servicio terminado no admite incidencias
    Given una orden CANCELADA
    When se intenta registrar una incidencia
    Then la API responde 409
