# language: en
@US-16 @RF-16
Feature: US-16 Controles para carga de alto valor
  As a responsable de Operaciones
  I want to aplicar controles adicionales de seguimiento a las cargas de alto valor
  So that reducir el riesgo de pérdida; condiciones definitivas pendientes (supuesto S-02)

  Scenario: Alto valor sin autorizar
    Given una orden con carga de alto valor
    When Operaciones intenta asignar recursos sin autorizarla
    Then la API responde 422 con el código ControlDeAltoValorPendiente

  Scenario: Alto valor autorizado
    Given una orden con carga de alto valor
    When Operaciones la autoriza y después asigna recursos
    Then la asignación se realiza y la autorización queda en el historial

  Scenario: Carga normal no requiere autorización
    Given una orden con carga que no es de alto valor
    When Operaciones intenta autorizarla
    Then se rechaza porque no aplica
