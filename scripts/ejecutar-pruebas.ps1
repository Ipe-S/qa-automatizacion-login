# Comando único para ejecutar toda la suite en Windows (PowerShell).
# Equivalente a scripts/ejecutar-pruebas.sh y al pipeline de CI.
#
# Uso:   .\scripts\ejecutar-pruebas.ps1
#        $env:LATENCIA_SIMULADA_MS = "700"; .\scripts\ejecutar-pruebas.ps1   # simula degradación
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

# "mvn clean" borra target/: se guarda el historial para ver la tendencia
if (Test-Path target/dashboard/historial.json) { Copy-Item target/dashboard/historial.json .historial-local.json }

Write-Host "==> 1-2. Compilar, pruebas unitarias y escenarios BDD"
mvn -B -ntp clean verify
if ($LASTEXITCODE -ne 0) { throw "Fallaron las pruebas unitarias o BDD" }

Write-Host "==> Reporte HTML de pruebas unitarias"
mvn -B -ntp surefire-report:report-only "-DoutputName=surefire"

Write-Host "==> 3. Levantar API y ejecutar prueba de performance"
$api = Start-Process java -ArgumentList "-jar", "target/qa-automatizacion-login.jar" -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput "target/api.log"
try {
    for ($i = 0; $i -lt 30; $i++) {
        try { Invoke-RestMethod http://localhost:8080/health | Out-Null; break } catch { Start-Sleep 1 }
    }
    New-Item -ItemType Directory -Force target/performance | Out-Null
    $env:K6_WEB_DASHBOARD = "true"
    $env:K6_WEB_DASHBOARD_EXPORT = "target/performance/k6-reporte.html"
    k6 run performance/login-carga.js
    if ($LASTEXITCODE -ne 0) { Write-Host "k6 informó thresholds no cumplidos (ver alertas)" }
}
finally {
    Stop-Process -Id $api.Id -ErrorAction SilentlyContinue
}

Write-Host "==> 4. Dashboard y alertas"
foreach ($d in "unitarias", "bdd", "performance") {
    New-Item -ItemType Directory -Force "target/dashboard/reportes/$d" | Out-Null
}
Copy-Item target/reports/* target/dashboard/reportes/unitarias/ -Recurse -Force
Copy-Item target/cucumber-reports/cucumber.html target/dashboard/reportes/bdd/
if (Test-Path target/performance/k6-reporte.html) {
    Copy-Item target/performance/k6-reporte.html target/dashboard/reportes/performance/
}
python scripts/generar_dashboard.py --historial .historial-local.json
python scripts/evaluar_alertas.py

Write-Host "Listo. Abre target/dashboard/index.html"
