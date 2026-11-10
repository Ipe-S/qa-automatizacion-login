# qa-automatizacion-login

Proyecto del **Taller 1 – Evaluación Unidad II** (Automatización de Pruebas).
Una empresa necesita profesionalizar las pruebas automatizadas de un proyecto Java:
este repositorio muestra el flujo completo, desde el commit hasta el dashboard y las alertas.

| Actividad | Qué se resuelve aquí |
|---|---|
| **Actividad 1** | Git con ramas y commits claros, proyecto Maven con JUnit 5, pruebas unitarias atómicas, estructura ordenada, `.gitignore`, pipeline CI con reporte navegable. |
| **Actividad 2** | Sesión Three Amigos, escenarios Gherkin con `Scenario Outline`, step definitions en Java + Cucumber, BDD en el pipeline con reporte HTML, prueba de performance con k6, dashboard de métricas y alertas automáticas. |

---

## 1. Objetivos

1. Que **cada push o pull request** compile el proyecto y ejecute todas las pruebas sin intervención manual.
2. Que las pruebas sean **atómicas e independientes**: cada una prueba una sola cosa y puede correr sola y en cualquier orden.
3. Que los requisitos se escriban como **ejemplos ejecutables (BDD)** acordados entre negocio, desarrollo y QA.
4. Que el equipo **vea** el estado de la calidad (reportes HTML y dashboard) y **se entere** cuando algo falla o se degrada (alertas).

## 2. Tecnologías y por qué las elegí

| Herramienta | Uso | Motivo |
|---|---|---|
| Java 17 + Maven 3.9 | Lenguaje y build | El enunciado pide Java y Maven. Java 17 es LTS y viene en los runners de GitHub. |
| JUnit 5.11 | Pruebas unitarias | Estándar actual; soporta `@DisplayName` y pruebas parametrizadas. |
| Cucumber 7.20 (JUnit Platform) | BDD | Es el framework de referencia de ME_4; corre sobre el mismo JUnit, sin otra herramienta. |
| Surefire / Failsafe | Ejecución | Surefire corre unitarias (`*Test`) en `test`; Failsafe corre BDD (`*IT`) en `verify`. Así se separan las etapas. |
| GitHub Actions | CI | El pipeline queda versionado junto al código (*pipeline as code*, ME_3) y no hay que mantener un servidor. |
| k6 | Performance | Script en JavaScript, thresholds que pueden cortar el pipeline y reporte HTML incluido. |
| Python 3 (solo librería estándar) | Dashboard y alertas | Ya viene en el runner; no agrega dependencias. |

## 3. Estructura del proyecto

```
qa-automatizacion-login/
├── .github/workflows/ci.yml        # Pipeline CI (5 etapas)
├── .gitignore
├── pom.xml                         # Dependencias y plugins de prueba
├── README.md
├── config/
│   └── umbrales.json               # Umbrales de alertas (versionados)
├── docs/
│   ├── three-amigos.md             # Sesión Three Amigos: roles, criterios, ejemplos
│   └── evidencias/                 # Capturas de pantalla
├── performance/
│   └── login-carga.js              # Prueba de carga k6 con thresholds
├── scripts/
│   ├── ejecutar-pruebas.sh / .ps1  # Comando único: corre todo en local
│   ├── generar_dashboard.py        # Consolida métricas -> dashboard HTML
│   └── evaluar_alertas.py          # Compara métricas vs umbrales -> alertas
└── src/
    ├── main/java/cl/empresa/qa/
    │   ├── calculadora/Calculadora.java
    │   ├── login/                  # Reglas de negocio del login
    │   │   ├── ServicioLogin.java
    │   │   ├── RepositorioUsuarios.java (+ EnMemoria)
    │   │   ├── ResultadoLogin.java
    │   │   └── HashClave.java
    │   └── api/ServidorApi.java    # API HTTP para la prueba de performance
    └── test/
        ├── java/cl/empresa/qa/
        │   ├── calculadora/CalculadoraTest.java   # unitarias
        │   ├── login/ServicioLoginTest.java        # unitarias
        │   └── bdd/
        │       ├── RunCucumberIT.java              # runner BDD
        │       ├── steps/LoginSteps.java           # step definitions (delgados)
        │       └── helpers/LoginHelper.java        # lógica reutilizable
        └── resources/features/login.feature       # escenarios Gherkin
```

**Criterio de organización:** el código de producción (`src/main`) y el de pruebas (`src/test`) usan los mismos paquetes; las pruebas están separadas por nivel (unitarias por paquete de dominio, BDD en `bdd/`), y lo que no es Java (performance, scripts, configuración, documentación) tiene su carpeta propia.

## 4. Requisitos y comandos

Requisitos: JDK 17, Maven 3.9+, Git, k6 (solo para performance) y Python 3 (solo para el dashboard).

| Objetivo | Comando |
|---|---|
| Solo pruebas unitarias | `mvn clean test` |
| Unitarias + BDD | `mvn clean verify` |
| Solo BDD | `mvn clean verify -DskipUTs=true` |
| Reporte HTML de unitarias | `mvn surefire-report:report-only -DoutputName=surefire` |
| Levantar la API | `mvn package -DskipTests` y luego `java -jar target/qa-automatizacion-login.jar` |
| Prueba de performance | `k6 run performance/login-carga.js` (con la API arriba) |
| Dashboard | `python scripts/generar_dashboard.py` |
| Alertas | `python scripts/evaluar_alertas.py` |
| **Todo, en un solo comando** | `./scripts/ejecutar-pruebas.sh` (Linux/macOS/Git Bash) o `.\scripts\ejecutar-pruebas.ps1` (Windows) |

Dónde quedan los resultados:

| Resultado | Ruta |
|---|---|
| XML de JUnit | `target/surefire-reports/` |
| Reporte HTML de unitarias | `target/reports/surefire.html` |
| Reporte HTML de Cucumber | `target/cucumber-reports/cucumber.html` |
| Resumen k6 (JSON) y reporte HTML | `target/performance/` |
| Dashboard | `target/dashboard/index.html` |

## 5. Gestión de versiones (Git)

### Estrategia de ramas

```
main      ── versión estable; solo recibe merges desde develop (se etiqueta v1.0.0)
develop   ── integración; recibe los merges de cada feature
feature/* ── una rama por tarea; se borra después del merge
```

Ramas usadas: `feature/estructura-maven`, `feature/pruebas-unitarias`, `feature/pipeline-ci`,
`feature/bdd-login`, `feature/performance-k6`, `feature/dashboard-alertas`, `feature/panel-alertas`,
`docs/readme`, `docs/evidencias`, y ramas `fix/*` y `chore/*` para las correcciones que aparecieron al ejecutar la suite.
Cada una se integró con `git merge --no-ff` para que el historial muestre dónde empieza y termina cada trabajo.

### Convención de commits

Uso *Conventional Commits* en español: `tipo: qué cambia, en imperativo`.

| Tipo | Uso | Ejemplo |
|---|---|---|
| `feat` | funcionalidad nueva | `feat: agregar servicio de login con bloqueo por intentos` |
| `test` | pruebas | `test: agregar pruebas unitarias atómicas de la calculadora` |
| `build` | Maven, dependencias | `build: configurar Maven con JUnit 5 y Cucumber` |
| `ci` | pipeline | `ci: agregar pipeline de GitHub Actions con reporte de pruebas` |
| `docs` | documentación | `docs: documentar pipeline y comandos en README` |
| `chore` | mantenimiento | `chore: inicializar repositorio con .gitignore` |
| `fix` | corrección | `fix: detectar un intérprete de Python funcional en el script local` |

### Comandos usados

```bash
git init -b main
git add .gitignore README.md && git commit -m "chore: inicializar repositorio con .gitignore y README"
git switch -c develop
git switch -c feature/estructura-maven
git add pom.xml && git commit -m "build: configurar Maven con JUnit 5 y Cucumber"
git switch develop && git merge --no-ff feature/estructura-maven -m "merge: integrar estructura Maven"
# ... se repite por cada feature ...
git switch main && git merge --no-ff develop -m "release: versión 1.0.0"
git tag -a v1.0.0 -m "Taller 1 completo"
git log --oneline --graph --all     # ver historial
```

Evidencia: `docs/evidencias/01-git-ramas.png` y `docs/evidencias/02-git-log.png`.

## 6. Pruebas unitarias (Actividad 1)

- `CalculadoraTest`: suma, resta, multiplicación, división, división por cero, desbordamiento y una prueba **parametrizada** de suma.
- `ServicioLoginTest`: login válido, clave incorrecta, usuario inexistente, campos vacíos, bloqueo al tercer intento y reinicio del contador.

**Cómo se asegura la atomicidad:**

- Cada prueba verifica **una sola regla** y su nombre la describe (`bloqueaCuentaAlTercerIntentoFallido`).
- `@BeforeEach` crea objetos nuevos en cada prueba: no hay estado compartido ni orden obligatorio.
- El servicio depende de la **interfaz** `RepositorioUsuarios`; las pruebas usan una implementación en memoria, sin base de datos ni red (bajo acoplamiento).
- Patrón *Arrange / Act / Assert* en cada método.

## 7. BDD (Actividad 2)

1. **Three Amigos:** ver [`docs/three-amigos.md`](docs/three-amigos.md) (roles, conversación, criterios CA-01 a CA-04, ejemplos y glosario).
2. **Gherkin:** [`login.feature`](src/test/resources/features/login.feature) tiene un `Background`, dos `Scenario` y un `Scenario Outline` con `Examples` de 4 filas: **6 escenarios ejecutados**.
3. **Step definitions:** [`LoginSteps.java`](src/test/java/cl/empresa/qa/bdd/steps/LoginSteps.java) usa expresiones `{string}` e `{int}` y delega en [`LoginHelper.java`](src/test/java/cl/empresa/qa/bdd/helpers/LoginHelper.java). Un `@Before` deja un estado limpio por escenario.
4. **Runner:** [`RunCucumberIT.java`](src/test/java/cl/empresa/qa/bdd/RunCucumberIT.java) genera `cucumber.html` (navegable), `cucumber.json` (lo lee el dashboard) y `cucumber.xml`.
5. **Trazabilidad:** cada escenario tiene el tag del criterio que valida (`@CA-01`, etc.).

## 8. Pipeline de CI (`.github/workflows/ci.yml`)

**Disparadores:** `push` a cualquier rama, `pull_request` hacia `main` o `develop`, y ejecución manual.

```
push / PR
   │
   ▼
1. Build + unitarias ──► 2. BDD Cucumber ──► 3. Performance k6 ──► 4. Dashboard + alertas ──► 5. GitHub Pages (solo main)
   reporte-unitarias      reporte-bdd          reporte-performance    dashboard-calidad           sitio público
```

| Etapa | Qué hace | Si falla |
|---|---|---|
| 1. Build y unitarias | `mvn clean test` + reporte HTML Surefire | Se detiene el pipeline: feedback en ~1 minuto. |
| 2. BDD | `mvn verify -DskipUTs=true` (Failsafe + Cucumber) | No se corre performance. |
| 3. Performance | Empaqueta la API, la levanta, instala k6 y corre la carga | Un threshold roto hace fallar el job (k6 sale con código 99). |
| 4. Dashboard y alertas | Siempre corre (`if: always()`): junta reportes, genera dashboard, evalúa umbrales, anota el PR, abre un issue y avisa a Slack si hay alertas críticas. | El job falla si hay alertas críticas. |
| 5. Publicar | Solo en `main`: publica dashboard y reportes en GitHub Pages. | — |

Decisiones importantes:

- **Primero lo rápido:** las unitarias van solas en la primera etapa para dar feedback rápido; lo lento va después (ME_3, 2.6).
- **Caché de `~/.m2`** con `actions/setup-java` para que cada build no descargue todo de nuevo.
- **`concurrency`** cancela ejecuciones viejas de la misma rama.
- **Secretos fuera del código:** el webhook de Slack se lee de `secrets.SLACK_WEBHOOK_URL`.

### Reportes accesibles para el equipo

- **Artefactos** descargables en cada ejecución: `reporte-unitarias`, `reporte-bdd`, `reporte-performance`, `dashboard-calidad`.
- **Resumen del job** (*Job Summary*): tabla con el estado de cada indicador en la página de la ejecución.
- **GitHub Pages** (rama `main`): `https://<usuario>.github.io/qa-automatizacion-login/` con el dashboard y enlaces a los tres reportes HTML.

## 9. Prueba de performance

Script: [`performance/login-carga.js`](performance/login-carga.js), contra `POST /api/login`.

- **Carga:** sube a 10 usuarios virtuales en 10 s, sube a 20 y se mantiene 20 s, y baja en 10 s. Cada usuario espera 0,5 s entre requests.
- **Por qué el login:** es la puerta de entrada; si se pone lento, afecta a todos los clientes.

| Indicador | Métrica k6 | Qué indica | Umbral |
|---|---|---|---|
| TPS | `http_reqs` (rate) | Requests atendidas por segundo (capacidad) | > 10 req/s |
| Latencia promedio | `http_req_duration` avg | Experiencia típica | < 200 ms |
| Latencia p95 | `http_req_duration` p(95) | El 95 % responde en menos de este tiempo; detecta lentitud que el promedio esconde | < 500 ms |
| Tasa de errores | `http_req_failed` | % de respuestas con error | < 1 % |
| Logins exitosos | `login_exitoso` (propia) | % de logins correctos según el negocio | > 99 % |

## 10. Dashboard de métricas

`scripts/generar_dashboard.py` lee los reportes reales (JUnit XML, `cucumber.json`, resumen k6) y genera `index.html` con:

- Tarjetas: pruebas unitarias OK/total, escenarios BDD OK/total, TPS, latencia p95, tasa de errores y requests.
- Tablas por escenario BDD (con tags de criterio), por prueba unitaria y por threshold de k6.
- **Tendencia** de latencia p95 y tasa de éxito entre ejecuciones (`historial.json`, que el pipeline recupera desde GitHub Pages).

En el pipeline, el mismo resumen aparece en el *Job Summary*. Para una empresa más grande, el siguiente paso sería enviar las métricas de k6 a InfluxDB o Prometheus (`k6 run --out ...`) y verlas en Grafana, que es la herramienta mencionada en ME_4.

## 11. Alertas automáticas

`scripts/evaluar_alertas.py` compara las métricas con [`config/umbrales.json`](config/umbrales.json):

| Regla | Severidad |
|---|---|
| Cualquier prueba unitaria o escenario BDD fallido | CRÍTICA |
| Latencia p95 ≥ 500 ms | CRÍTICA |
| Latencia p95 ≥ 300 ms | ADVERTENCIA |
| Tasa de errores ≥ 1 % | CRÍTICA |
| TPS < 10 | ADVERTENCIA |
| p95 sube más de 20 % respecto a la ejecución anterior | ADVERTENCIA (degradación) |
| Threshold de k6 no cumplido | CRÍTICA |

**Canales:** anotaciones `::error::` en el PR, resumen del job, **issue automático** con etiqueta `alerta-calidad` (o comentario si ya existe) y **Slack** si se configura el secreto `SLACK_WEBHOOK_URL`. Una alerta crítica deja el pipeline en rojo; con una regla de protección de rama en `main` se bloquea el merge.

**Simulación de degradación:** la API acepta `LATENCIA_SIMULADA_MS` para agregar retardo artificial.

```bash
LATENCIA_SIMULADA_MS=700 java -jar target/qa-automatizacion-login.jar &
k6 run performance/login-carga.js         # thresholds de latencia fallan
python scripts/generar_dashboard.py --historial target/dashboard/historial.json
python scripts/evaluar_alertas.py --no-fallar
```

## 12. Cómo publicarlo en GitHub

1. Crear un repositorio vacío `qa-automatizacion-login` en GitHub.
2. `git remote add origin https://github.com/<usuario>/qa-automatizacion-login.git`
3. `git push -u origin main develop --tags` (y las ramas feature si se quieren mostrar).
4. En **Settings → Pages**, elegir *Source: GitHub Actions*.
5. (Opcional) En **Settings → Secrets → Actions**, crear `SLACK_WEBHOOK_URL`.
6. Revisar la pestaña **Actions**: se ejecuta el workflow **CI**.

## 13. Evidencias

| Evidencia | Archivo |
|---|---|
| Ramas del repositorio | `docs/evidencias/01-git-ramas.png` |
| Historial de commits | `docs/evidencias/02-git-log.png` |
| Pruebas unitarias en local | `docs/evidencias/03-mvn-test-local.png` |
| Escenarios BDD en local | `docs/evidencias/04-bdd-local.png` |
| Reporte HTML de unitarias | `docs/evidencias/05-reporte-unitarias.png` |
| Reporte HTML de Cucumber | `docs/evidencias/06-reporte-cucumber.png` |
| Ejecución de k6 | `docs/evidencias/07-k6-local.png` |
| Reporte HTML de k6 | `docs/evidencias/08-reporte-k6.png` |
| Dashboard de calidad | `docs/evidencias/09-dashboard.png` |
| Alertas con degradación simulada | `docs/evidencias/10-alertas-simuladas.png` |
| Dashboard con alerta | `docs/evidencias/11-dashboard-alerta.png` |
| Pipeline en GitHub Actions | `docs/evidencias/12-ci-pipeline.png` *(se toma después del push)* |
| Resumen del job en CI | `docs/evidencias/13-ci-resumen.png` *(se toma después del push)* |
| Artefactos publicados en CI | `docs/evidencias/14-ci-artefactos.png` *(se toma después del push)* |

## 14. Referencias

- Material de estudio ME_3: *Configuración de software para la automatización de pruebas* (integración continua, pipeline as code, diseño de suites).
- Material de estudio ME_4: BDD, Three Amigos, equipos, estrategia de pruebas, performance, dashboards y alertas.
- JUnit 5 User Guide: https://junit.org/junit5/docs/current/user-guide/
- Cucumber: https://cucumber.io/docs/
- k6: https://grafana.com/docs/k6/latest/
- GitHub Actions: https://docs.github.com/actions
