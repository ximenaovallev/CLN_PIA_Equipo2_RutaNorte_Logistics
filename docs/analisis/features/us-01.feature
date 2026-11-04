# language: en
@US-01 @RF-01
Feature: US-01 Solicitud de cotización
  As a cliente
  I want to solicitar una cotización proporcionando origen, destino, mercancía, peso, dimensiones, fecha requerida y características especiales cuando sean necesarias
  So that obtener una propuesta de transporte adecuada

  Scenario: Solicitud registrada con los datos proporcionados
    Given que el cliente CLI-1 está registrado
    When solicita una cotización de Monterrey a Querétaro con 800 kg de refacciones de 2 x 1.5 x 1.5 m para el 2026-12-01
    Then se registra la solicitud en estado SOLICITADO
    And se devuelve el identificador de la cotización con código 201

  Scenario: Datos inválidos no se registran
    Given que el cliente CLI-1 está registrado
    When solicita una cotización con peso de -5 kg
    Then la API responde 400 con el código DatosInvalidos
    And no se crea ninguna cotización

  Scenario: El solicitante debe existir
    Given que el cliente NO-EXISTE no está registrado
    When solicita una cotización
    Then la API responde 404 con el código EntidadNoEncontrada
