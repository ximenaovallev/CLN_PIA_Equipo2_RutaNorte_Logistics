# language: en
@US-06 @RF-05
Feature: US-06 Generación de orden
  As a responsable de Operaciones
  I want to generar una orden de servicio después de la aceptación de la cotización
  So that iniciar formalmente la operación

  Scenario: Orden generada tras la aceptación
    Given una cotización ACEPTADA
    When Operaciones genera la orden con la ruta MTY-QRO y el horario de recolección
    Then la orden queda CONFIRMADA con un evento en su historial
    And se publica el evento OrdenDeServicioGenerada

  Scenario: Sin aceptación no hay orden
    Given una cotización que el cliente no ha aceptado
    When Operaciones intenta generar la orden
    Then la API responde 422 con el código OrdenNoGenerable
    And no se crea ninguna orden
