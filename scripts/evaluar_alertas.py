#!/usr/bin/env python3
"""
Evalúa las métricas del dashboard contra los umbrales de config/umbrales.json
y genera alertas automáticas.

Severidades:
  CRITICA      -> falla el pipeline (código de salida 1) y dispara notificación
  ADVERTENCIA  -> queda registrada en el resumen, no bloquea el merge

Canales de alerta:
  1. Consola / anotaciones de GitHub Actions (::error:: y ::warning::), que
     aparecen en la pestaña del pull request.
  2. Archivos alertas.json y alertas.md (los usa el pipeline para abrir un issue).
  3. Slack: si existe la variable SLACK_WEBHOOK_URL (secreto del repositorio)
     se envía un mensaje al canal del equipo.

Uso:
  python scripts/evaluar_alertas.py --metricas target/dashboard/metricas.json
  python scripts/evaluar_alertas.py --no-fallar   # simulación: muestra alertas sin cortar
"""
import argparse
import html
import json
import os
import sys
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def alerta(severidad, regla, detalle):
    return {"severidad": severidad, "regla": regla, "detalle": detalle}


def evaluar(met, umbrales, historial):
    f, p = umbrales["funcional"], umbrales["performance"]
    alertas = []

    u = met.get("unitarias")
    if u is None:
        alertas.append(alerta("CRITICA", "pruebas-unitarias", "No se encontraron resultados de pruebas unitarias"))
    elif u["fallidas"] > f["max_pruebas_unitarias_fallidas"]:
        nombres = ", ".join(c["nombre"] for c in u["casos"] if c["estado"] == "failed")
        alertas.append(alerta("CRITICA", "pruebas-unitarias", f"{u['fallidas']} prueba(s) unitaria(s) fallida(s): {nombres}"))

    b = met.get("bdd")
    if b is None:
        alertas.append(alerta("CRITICA", "escenarios-bdd", "No se encontró el reporte cucumber.json"))
    elif b["fallidos"] > f["max_escenarios_bdd_fallidos"]:
        nombres = ", ".join(e["nombre"] for e in b["escenarios"] if e["estado"] == "failed")
        alertas.append(alerta("CRITICA", "escenarios-bdd", f"{b['fallidos']} escenario(s) BDD fallido(s): {nombres}"))

    perf = met.get("performance")
    if perf is None:
        alertas.append(alerta("ADVERTENCIA", "performance", "No hay resultados de k6 en esta ejecución"))
    else:
        p95 = perf["latencia_p95_ms"]
        if p95 >= p["latencia_p95_ms_critica"]:
            alertas.append(alerta("CRITICA", "latencia-p95", f"p95 = {p95} ms supera el límite crítico de {p['latencia_p95_ms_critica']} ms"))
        elif p95 >= p["latencia_p95_ms_advertencia"]:
            alertas.append(alerta("ADVERTENCIA", "latencia-p95", f"p95 = {p95} ms supera el umbral de advertencia de {p['latencia_p95_ms_advertencia']} ms"))

        if perf["tasa_errores_pct"] >= p["tasa_errores_porcentaje_critica"]:
            alertas.append(alerta("CRITICA", "tasa-errores", f"Errores HTTP = {perf['tasa_errores_pct']} % (límite {p['tasa_errores_porcentaje_critica']} %)"))

        if perf["tps"] < p["tps_minimo_advertencia"]:
            alertas.append(alerta("ADVERTENCIA", "tps", f"TPS = {perf['tps']} bajo el mínimo esperado de {p['tps_minimo_advertencia']}"))

        # Degradación: compara con la ejecución anterior registrada en el historial
        anteriores = [h for h in historial[:-1] if h.get("latencia_p95_ms")]
        if anteriores:
            base = anteriores[-1]["latencia_p95_ms"]
            aumento = (p95 - base) * 100 / base
            if aumento > p["degradacion_p95_porcentaje_vs_ejecucion_anterior"]:
                alertas.append(alerta("ADVERTENCIA", "degradacion-p95",
                                      f"p95 subió {aumento:.1f} % respecto a la ejecución anterior ({base} ms -> {p95} ms)"))

        for t in perf["umbrales"]:
            if not t["ok"]:
                alertas.append(alerta("CRITICA", "threshold-k6", f"Threshold de k6 no cumplido: {t['metrica']} {t['regla']}"))
    return alertas


def a_markdown(alertas, met):
    if not alertas:
        return "## Alertas\n\nSin alertas: todas las pruebas y umbrales están dentro de lo esperado. ✅\n"
    filas = ["## Alertas de calidad", "",
             f"Commit `{met.get('commit', '')[:7]}` · rama `{met.get('rama', '')}` · ejecución {met.get('ejecucion', '')}", "",
             "| Severidad | Regla | Detalle |", "|---|---|---|"]
    filas += [f"| {'🔴' if a['severidad'] == 'CRITICA' else '🟡'} {a['severidad']} | {a['regla']} | {a['detalle']} |" for a in alertas]
    return "\n".join(filas) + "\n"


def insertar_en_dashboard(alertas, carpeta):
    """Agrega el panel de alertas al dashboard (marca <!--ALERTAS--> de index.html)."""
    ruta = os.path.join(carpeta, "index.html")
    if not os.path.exists(ruta):
        return
    if alertas:
        filas = "".join(f"<tr><td><span class='b {a['severidad']}'>{a['severidad']}</span></td>"
                        f"<td>{html.escape(a['regla'])}</td><td>{html.escape(a['detalle'])}</td></tr>" for a in alertas)
        panel = (f"<div class='alertas'><h2>Alertas activas ({len(alertas)})</h2>"
                 f"<table><tr><th>Severidad</th><th>Regla</th><th>Detalle</th></tr>{filas}</table></div>")
    else:
        panel = "<div class='alertas'><h2>Alertas activas</h2><p>Sin alertas: todo dentro de los umbrales.</p></div>"
    with open(ruta, encoding="utf-8") as f:
        contenido = f.read()
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido.replace("<!--ALERTAS-->", panel, 1))


def notificar_slack(texto):
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        print("SLACK_WEBHOOK_URL no configurado: se omite la notificación a Slack.")
        return
    cuerpo = json.dumps({"text": texto}).encode("utf-8")
    peticion = urllib.request.Request(url, data=cuerpo, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(peticion, timeout=10) as r:
        print(f"Notificación enviada a Slack (HTTP {r.status})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metricas", default="target/dashboard/metricas.json")
    ap.add_argument("--historial", default="target/dashboard/historial.json")
    ap.add_argument("--umbrales", default="config/umbrales.json")
    ap.add_argument("--salida", default="target/dashboard")
    ap.add_argument("--no-fallar", action="store_true", help="no devolver código 1 (modo simulación)")
    args = ap.parse_args()

    with open(args.metricas, encoding="utf-8") as f:
        met = json.load(f)
    with open(args.umbrales, encoding="utf-8") as f:
        umbrales = json.load(f)
    historial = []
    if os.path.exists(args.historial):
        with open(args.historial, encoding="utf-8") as f:
            historial = json.load(f)

    alertas = evaluar(met, umbrales, historial)
    criticas = [a for a in alertas if a["severidad"] == "CRITICA"]
    en_actions = os.environ.get("GITHUB_ACTIONS") == "true"

    print(f"Alertas: {len(alertas)} (críticas: {len(criticas)})")
    for a in alertas:
        if en_actions:
            nivel = "error" if a["severidad"] == "CRITICA" else "warning"
            print(f"::{nivel} title=Alerta {a['regla']}::{a['detalle']}")
        else:
            print(f"  [{a['severidad']}] {a['regla']}: {a['detalle']}")

    md = a_markdown(alertas, met)
    os.makedirs(args.salida, exist_ok=True)
    with open(os.path.join(args.salida, "alertas.json"), "w", encoding="utf-8") as f:
        json.dump({"criticas": len(criticas), "alertas": alertas}, f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.salida, "alertas.md"), "w", encoding="utf-8") as f:
        f.write(md)

    insertar_en_dashboard(alertas, args.salida)

    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("\n" + md)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"criticas={len(criticas)}\n")

    if criticas:
        try:
            notificar_slack(f":rotating_light: {len(criticas)} alerta(s) crítica(s) en qa-automatizacion-login\n"
                            + "\n".join(f"• {a['regla']}: {a['detalle']}" for a in criticas))
        except Exception as e:  # una falla de Slack no debe ocultar la alerta original
            print(f"No se pudo notificar a Slack: {e}")
        if not args.no_fallar:
            sys.exit(1)


if __name__ == "__main__":
    main()
