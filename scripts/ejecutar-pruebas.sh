#!/usr/bin/env bash
# Comando único para ejecutar toda la suite en local (Linux, macOS o Git Bash).
# Hace lo mismo que el pipeline, en el mismo orden:
#   unitarias -> BDD -> reportes -> API + k6 -> dashboard -> alertas
#
# Uso:  ./scripts/ejecutar-pruebas.sh
#       LATENCIA_SIMULADA_MS=700 ./scripts/ejecutar-pruebas.sh   # simula degradación
set -euo pipefail
cd "$(dirname "$0")/.."

# En Windows "python3" puede ser un acceso directo de la Microsoft Store que no
# funciona: se usa el primer intérprete que responda de verdad.
PYTHON=""
for candidato in python3 python; do
  if "$candidato" --version >/dev/null 2>&1; then PYTHON=$candidato; break; fi
done
[ -n "$PYTHON" ] || { echo "No se encontró Python 3"; exit 1; }

# "mvn clean" borra target/: se guarda el historial para ver la tendencia
if [ -f target/dashboard/historial.json ]; then cp target/dashboard/historial.json .historial-local.json; fi

echo "==> 1-2. Compilar, pruebas unitarias y escenarios BDD"
mvn -B -ntp clean verify

echo "==> Reporte HTML de pruebas unitarias"
mvn -B -ntp surefire-report:report-only -DoutputName=surefire

echo "==> 3. Levantar API y ejecutar prueba de performance"
java -jar target/qa-automatizacion-login.jar > target/api.log 2>&1 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null || true' EXIT
for i in $(seq 1 30); do curl -sf http://localhost:8080/health >/dev/null && break; sleep 1; done

mkdir -p target/performance
K6_WEB_DASHBOARD=true K6_WEB_DASHBOARD_EXPORT=target/performance/k6-reporte.html \
  k6 run performance/login-carga.js || echo "k6 informó thresholds no cumplidos (ver alertas)"

echo "==> 4. Dashboard y alertas"
mkdir -p target/dashboard/reportes/{unitarias,bdd,performance}
cp -r target/reports/. target/dashboard/reportes/unitarias/
cp target/cucumber-reports/cucumber.html target/dashboard/reportes/bdd/
cp target/performance/k6-reporte.html target/dashboard/reportes/performance/ 2>/dev/null || true
"$PYTHON" scripts/generar_dashboard.py --historial .historial-local.json
"$PYTHON" scripts/evaluar_alertas.py

echo "Listo. Abre target/dashboard/index.html"
