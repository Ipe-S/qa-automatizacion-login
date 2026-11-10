# Funcionalidad definida en la sesión Three Amigos (docs/three-amigos.md).
# Palabras clave Gherkin en inglés y pasos en español, como acordó el equipo.
@login
Feature: Inicio de sesión en el portal de clientes
  Como cliente registrado
  Quiero iniciar sesión con mi usuario y contraseña
  Para acceder a mi cuenta de forma segura

  Background:
    Given existen los siguientes usuarios registrados:
      | usuario | clave      |
      | ana     | Clave123!  |
      | pedro   | Segura456# |

  @smoke @CA-01
  Scenario: Inicio de sesión exitoso con credenciales válidas
    When el usuario "ana" ingresa la clave "Clave123!"
    Then el acceso es concedido
    And se muestra el mensaje "Bienvenido, ana"

  @negativo @CA-02 @CA-03
  Scenario Outline: Inicio de sesión rechazado por <caso>
    When el usuario "<usuario>" ingresa la clave "<clave>"
    Then el acceso es denegado
    And se muestra el mensaje "<mensaje>"

    Examples:
      | caso                | usuario  | clave      | mensaje                            |
      | clave incorrecta    | ana      | Clave999!  | Usuario o contraseña incorrectos   |
      | usuario inexistente | maria    | Clave123!  | Usuario o contraseña incorrectos   |
      | usuario vacío       |          | Clave123!  | Debe ingresar usuario y contraseña |
      | clave vacía         | pedro    |            | Debe ingresar usuario y contraseña |

  @seguridad @CA-04
  Scenario: Bloqueo de la cuenta después de tres intentos fallidos
    Given el usuario "pedro" falló el inicio de sesión 3 veces
    When el usuario "pedro" ingresa la clave "Segura456#"
    Then el acceso es denegado
    And se muestra el mensaje "Cuenta bloqueada. Contacte a soporte"
