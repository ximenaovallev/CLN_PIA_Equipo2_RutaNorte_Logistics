# language: en
@US-10 @RF-11
Feature: US-10 Actualización de estados
  As a Ventas, Operaciones u Operador
  I want to registrar los cambios de estado según la actividad realizada
  So that conocer en qué etapa se encuentra cada servicio

  Scenario: Recorrido normal de estados
    Given una orden CONFIRMADA
    When se asignan recursos, se recibe la mercancía, inicia el traslado, llega a destino y se entrega
    Then los estados son UNIDAD_ASIGNADA, RECOLECTADO, EN_TRANSITO, LLEGADA_A_DESTINO y ENTREGADO
    And cada cambio queda en el historial

  Scenario: Transición inválida
    Given una orden CONFIRMADA
    When se intenta registrar la llegada a destino
    Then la API responde 409 con el código TransicionDeEstadoInvalida y "se requiere EN_TRANSITO"
    And el estado no cambia
