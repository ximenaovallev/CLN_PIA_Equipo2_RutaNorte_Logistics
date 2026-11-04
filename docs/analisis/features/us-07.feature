# language: en
@US-07 @RF-06
Feature: US-07 Asignación de recursos
  As a responsable de Operaciones
  I want to asignar una unidad y un operador considerando carga, capacidad y disponibilidad
  So that garantizar que el servicio se ejecute con recursos adecuados

  Scenario: Asignación adecuada
    Given una orden CONFIRMADA de 800 kg y una unidad de 5000 kg / 30 m³ y un operador disponible
    When Operaciones asigna la unidad y el operador
    Then la orden pasa a UNIDAD_ASIGNADA
    And se publica el evento RecursosAsignados

  Scenario: Unidad sin capacidad suficiente
    Given una orden de 800 kg y una unidad de 500 kg
    When Operaciones intenta asignarla
    Then la API responde 422 con el código RecursosNoDisponibles y el motivo "no es adecuada"
    And la orden sigue CONFIRMADA

  Scenario: Operador no disponible
    Given un operador marcado como no disponible
    When Operaciones intenta asignarlo
    Then la API responde 422 con el motivo "no está disponible"
