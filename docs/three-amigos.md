# Sesión Three Amigos (simulada): inicio de sesión del portal de clientes

> Esta sesión es una **simulación** pedida por el Taller 1. Los tres roles los
> represento yo, pero la conversación sigue la dinámica real: cada rol aporta
> una mirada distinta y los acuerdos se transforman en escenarios Gherkin.

| Dato | Detalle |
|---|---|
| Historia de usuario | **HU-01**: Como cliente registrado quiero iniciar sesión con mi usuario y contraseña para acceder a mi cuenta de forma segura. |
| Duración | 30 minutos (timebox) |
| Resultado | 4 criterios de aceptación, 6 ejemplos concretos y `src/test/resources/features/login.feature` |

## Roles participantes

| Rol | Persona (simulada) | Qué aporta en la sesión |
|---|---|---|
| Negocio / Product Owner | Carolina, PO | Explica el *por qué* de la historia, prioriza y define qué es "aceptable" para el cliente. |
| Desarrollo | Matías, desarrollador backend | Explica cómo se implementa, qué es técnicamente posible y detecta dependencias. |
| QA / Testing | Yo, QA automatizador | Pregunta por los casos borde y negativos, propone ejemplos y cuida que todo sea comprobable. |

## Conversación resumida

1. **PO:** "Lo mínimo es que el cliente entre con su usuario y clave y vea un saludo. Hoy recibimos muchos reclamos por cuentas usadas por terceros."
2. **QA:** "¿Qué pasa si escribe mal la clave? ¿Le decimos si el usuario existe?"
3. **Dev:** "Por seguridad conviene un mensaje genérico, así nadie puede adivinar qué usuarios existen."
4. **PO:** "De acuerdo, un solo mensaje: *Usuario o contraseña incorrectos*."
5. **QA:** "¿Y si deja campos vacíos? ¿Cuenta como intento fallido?"
6. **Dev:** "No debería llegar a validar credenciales. Respondemos *Debe ingresar usuario y contraseña* y no sumamos intento."
7. **PO:** "Por los reclamos de acceso de terceros, quiero bloquear la cuenta después de varios intentos."
8. **QA:** "¿Cuántos exactamente? Necesito un número para escribir el ejemplo."
9. **PO:** "Tres intentos seguidos. Después el cliente debe llamar a soporte."
10. **Dev:** "Si entra bien antes del tercero, reinicio el contador. Y si está bloqueada, ni siquiera reviso la clave."
11. **QA:** "Entonces agrego un ejemplo donde el usuario pone la clave correcta después del bloqueo y aun así se le niega el acceso."

## Criterios de aceptación acordados

| ID | Criterio | Tag en el `.feature` |
|---|---|---|
| CA-01 | Con usuario y clave válidos se concede el acceso y se muestra "Bienvenido, &lt;usuario&gt;". | `@CA-01` |
| CA-02 | Si la clave es incorrecta o el usuario no existe, se deniega con el mensaje genérico "Usuario o contraseña incorrectos". | `@CA-02` |
| CA-03 | Si falta el usuario o la clave, se deniega con "Debe ingresar usuario y contraseña" y no se cuenta como intento. | `@CA-03` |
| CA-04 | Al tercer intento fallido seguido la cuenta se bloquea; incluso con la clave correcta se muestra "Cuenta bloqueada. Contacte a soporte". | `@CA-04` |

## Ejemplos concretos discutidos

| # | Usuario | Clave | Resultado esperado | Criterio |
|---|---|---|---|---|
| 1 | ana | Clave123! | Acceso concedido, "Bienvenido, ana" | CA-01 |
| 2 | ana | Clave999! | Denegado, mensaje genérico | CA-02 |
| 3 | maria (no existe) | Clave123! | Denegado, mensaje genérico | CA-02 |
| 4 | *(vacío)* | Clave123! | Denegado, "Debe ingresar usuario y contraseña" | CA-03 |
| 5 | pedro | *(vacío)* | Denegado, "Debe ingresar usuario y contraseña" | CA-03 |
| 6 | pedro (3 fallos previos) | Segura456# | Denegado, "Cuenta bloqueada. Contacte a soporte" | CA-04 |

## Glosario acordado

- **Usuario registrado:** cliente que existe en el sistema con usuario y clave.
- **Intento fallido:** intento con usuario y clave informados, pero que no coinciden.
- **Cuenta bloqueada:** cuenta con 3 intentos fallidos seguidos; solo soporte la desbloquea.

## Preguntas abiertas (fuera de alcance de este sprint)

- ¿Desbloqueo automático después de cierto tiempo? → queda en el backlog (PO).
- ¿Recuperación de clave por correo? → nueva historia HU-02.

## Cómo se llevaron los acuerdos al código

- Los ejemplos 2 a 5 se agruparon en un **Scenario Outline** con tabla **Examples**, porque comparten los mismos pasos y solo cambian los datos.
- Los usuarios de prueba se cargan en un **Background**, para no repetirlos en cada escenario.
- Cada escenario lleva el tag del criterio que valida, así el reporte de Cucumber muestra qué criterio pasó o falló.
