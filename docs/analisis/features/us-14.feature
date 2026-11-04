# language: en
@US-14 @RF-14
Feature: US-14 Consulta para Atención al Cliente
  As a personal de Atención al Cliente
  I want to consultar el estado, eventos, retrasos e incidencias de un servicio
  So that informar al cliente sin depender de Operaciones

  Scenario: Consulta de un servicio
    Given una orden con eventos y una incidencia RETRASO
    When Atención al Cliente consulta el estado
    Then ve el estado actual, los eventos, los retrasos, las incidencias y las acciones permitidas

  Scenario: Servicio inexistente
    Given un identificador que no existe
    When Atención al Cliente lo consulta
    Then la API responde 404
