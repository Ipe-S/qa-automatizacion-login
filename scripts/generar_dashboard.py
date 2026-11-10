#!/usr/bin/env python3
"""
Genera el dashboard de calidad del pipeline a partir de los reportes reales:

  - target/surefire-reports/TEST-*.xml        -> pruebas unitarias (JUnit)
  - target/cucumber-reports/cucumber.json     -> escenarios BDD (Cucumber)
  - target/performance/k6-summary.json        -> performance (k6)

Salidas (en --salida, por defecto target/dashboard):
  - metricas.json   métricas consolidadas de esta ejecución
  - historial.json  métricas de ejecuciones anteriores + la actual (tendencia)
  - index.html      dashboard navegable
  - Si existe la variable GITHUB_STEP_SUMMARY, agrega un resumen Markdown
    que GitHub Actions muestra en la página de la ejecución del pipeline.

Solo usa la biblioteca estándar de Python, así corre en cualquier runner.
"""
import argparse
import datetime as dt
import glob
import html
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

# La consola de Windows usa cp1252: forzamos UTF-8 para los emojis del resumen
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------- lectura
def leer_junit(carpeta):
    """Suma los resultados de todos los TEST-*.xml de una carpeta."""
    total = fallidas = omitidas = 0
    tiempo = 0.0
    casos = []
    for archivo in sorted(glob.glob(os.path.join(carpeta, "TEST-*.xml"))):
        raiz = ET.parse(archivo).getroot()
        total += int(raiz.get("tests", 0))
        fallidas += int(raiz.get("failures", 0)) + int(raiz.get("errors", 0))
        omitidas += int(raiz.get("skipped", 0))
        tiempo += float(raiz.get("time", 0) or 0)
        for caso in raiz.iter("testcase"):
            estado = "passed"
            if caso.find("failure") is not None or caso.find("error") is not None:
                estado = "failed"
            elif caso.find("skipped") is not None:
                estado = "skipped"
            casos.append({
                "clase": caso.get("classname", "").split(".")[-1],
                "nombre": caso.get("name", ""),
                "tiempo_s": float(caso.get("time", 0) or 0),
                "estado": estado,
            })
    if total == 0:
        return None
    return {
        "total": total,
        "exitosas": total - fallidas - omitidas,
        "fallidas": fallidas,
        "omitidas": omitidas,
        "tiempo_s": round(tiempo, 3),
        "casos": casos,
    }


def leer_cucumber(archivo):
    if not os.path.exists(archivo):
        return None
    with open(archivo, encoding="utf-8") as f:
        features = json.load(f)
    escenarios = []
    for feature in features:
        for elemento in feature.get("elements", []):
            if elemento.get("type") != "scenario":
                continue
            pasos = elemento.get("steps", [])
            estados = [p.get("result", {}).get("status", "undefined") for p in pasos]
            duracion_ns = sum(p.get("result", {}).get("duration", 0) for p in pasos)
            escenarios.append({
                "feature": feature.get("name", ""),
                "nombre": elemento.get("name", ""),
                "tags": [t["name"] for t in elemento.get("tags", [])],
                "pasos": len(pasos),
                "estado": "passed" if estados and all(s == "passed" for s in estados) else "failed",
                "tiempo_ms": round(duracion_ns / 1_000_000, 2),
            })
    total = len(escenarios)
    exitosos = sum(1 for e in escenarios if e["estado"] == "passed")
    return {
        "total": total,
        "exitosos": exitosos,
        "fallidos": total - exitosos,
        "pasos": sum(e["pasos"] for e in escenarios),
        "escenarios": escenarios,
    }


def leer_k6(archivo):
    if not os.path.exists(archivo):
        return None
    with open(archivo, encoding="utf-8") as f:
        datos = json.load(f)
    m = datos.get("metrics", {})

    def valor(metrica, stat, defecto=0.0):
        return m.get(metrica, {}).get("values", {}).get(stat, defecto)

    umbrales = []
    for nombre, metrica in m.items():
        for regla, estado in (metrica.get("thresholds") or {}).items():
            umbrales.append({"metrica": nombre, "regla": regla, "ok": bool(estado.get("ok"))})
    return {
        "tps": round(valor("http_reqs", "rate"), 2),
        "requests": int(valor("http_reqs", "count")),
        "latencia_avg_ms": round(valor("http_req_duration", "avg"), 2),
        "latencia_p90_ms": round(valor("http_req_duration", "p(90)"), 2),
        "latencia_p95_ms": round(valor("http_req_duration", "p(95)"), 2),
        "latencia_max_ms": round(valor("http_req_duration", "max"), 2),
        "tasa_errores_pct": round(valor("http_req_failed", "rate") * 100, 3),
        "login_exitoso_pct": round(valor("login_exitoso", "rate") * 100, 2),
        "vus_max": int(valor("vus_max", "max", valor("vus_max", "value", 0))),
        "umbrales": umbrales,
    }


# ---------------------------------------------------------------- html
CSS = """
:root{--bg:#f5f7f9;--card:#fff;--ink:#17222d;--muted:#5b6876;--line:#dbe2e8;
--ok:#1a7f4b;--ok-bg:#e3f5ea;--bad:#b42318;--bad-bg:#fde8e6;--warn:#9a5b00;--warn-bg:#fff2d9;--acc:#1f5f8b}
@media (prefers-color-scheme:dark){:root{--bg:#10161c;--card:#18212a;--ink:#e6edf3;--muted:#9aa7b4;
--line:#2a3742;--ok:#5fd394;--ok-bg:#163526;--bad:#ff8a80;--bad-bg:#3d1c1a;--warn:#f5c26b;--warn-bg:#3a2c12;--acc:#7cb8e6}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,Arial,sans-serif}
.wrap{max-width:1100px;margin:auto;padding:24px 16px 48px}h1{margin:0 0 4px;font-size:1.6rem}
h2{font-size:1.15rem;margin:28px 0 10px}.meta{color:var(--muted);font-size:.9rem}
.estado{display:inline-block;margin-top:12px;padding:6px 14px;border-radius:999px;font-weight:700}
.estado.ok{background:var(--ok-bg);color:var(--ok)}.estado.bad{background:var(--bad-bg);color:var(--bad)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-top:18px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.kpi span{display:block;color:var(--muted);font-size:.8rem}.kpi strong{font-size:1.5rem;font-variant-numeric:tabular-nums}
.kpi.ok{border-left:5px solid var(--ok)}.kpi.bad{border-left:5px solid var(--bad)}.kpi.warn{border-left:5px solid var(--warn)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.9rem}th,td{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600}td.num{text-align:right;font-variant-numeric:tabular-nums}
.b{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.78rem;font-weight:700}
.b.passed,.b.ok{background:var(--ok-bg);color:var(--ok)}.b.failed,.b.bad{background:var(--bad-bg);color:var(--bad)}
.b.skipped{background:var(--warn-bg);color:var(--warn)}
.links a{display:inline-block;margin:4px 10px 4px 0;color:var(--acc);font-weight:600}
svg text{fill:var(--muted);font-size:11px}
.alertas{margin-top:16px;border:1px solid var(--line);border-radius:12px;background:var(--card);padding:12px 16px}
.alertas h2{margin:0 0 8px}.b.CRITICA{background:var(--bad-bg);color:var(--bad)}.b.ADVERTENCIA{background:var(--warn-bg);color:var(--warn)}
"""


def kpi(etiqueta, valor, clase=""):
    return f'<div class="kpi {clase}"><span>{html.escape(etiqueta)}</span><strong>{html.escape(str(valor))}</strong></div>'


def tendencia_svg(historial, campo, titulo, unidad):
    puntos = [h for h in historial if h.get(campo) is not None][-15:]
    if len(puntos) < 2:
        return f"<p class='meta'>{titulo}: se necesitan al menos dos ejecuciones para mostrar tendencia.</p>"
    ancho, alto, margen = 520, 140, 30
    maximo = max(p[campo] for p in puntos) or 1
    paso = (ancho - 2 * margen) / (len(puntos) - 1)
    coords = [(margen + i * paso, alto - margen - (p[campo] / maximo) * (alto - 2 * margen)) for i, p in enumerate(puntos)]
    linea = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
    marcas = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="currentColor"/>' for x, y in coords)
    return (f'<div style="margin-bottom:12px"><strong style="display:block;margin-bottom:4px">{titulo}</strong><svg viewBox="0 0 {ancho} {alto}" width="100%" style="max-width:{ancho}px;color:var(--acc)" role="img" aria-label="{titulo}">'
            f'<polyline points="{linea}" fill="none" stroke="currentColor" stroke-width="2"/>{marcas}'
            f'<text x="{margen}" y="{alto - 8}">ejecución más antigua</text>'
            f'<text x="{ancho - margen}" y="{alto - 8}" text-anchor="end">última: {puntos[-1][campo]} {unidad}</text>'
            f'<text x="4" y="14">máx {maximo} {unidad}</text></svg></div>')


def construir_html(met, historial):
    u, b, p = met["unitarias"], met["bdd"], met["performance"]
    aprobado = met["build_verde"]
    partes = [f"<!doctype html><html lang='es'><head><meta charset='utf-8'>"
              f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
              f"<title>Dashboard de calidad</title><style>{CSS}</style></head><body><div class='wrap'>",
              "<h1>Dashboard de calidad del pipeline</h1>",
              f"<div class='meta'>Proyecto qa-automatizacion-login · ejecución {html.escape(met['ejecucion'])} · "
              f"commit {html.escape(met['commit'][:7])} · rama {html.escape(met['rama'])} · {html.escape(met['fecha'])}</div>",
              f"<div class='estado {'ok' if aprobado else 'bad'}'>{'BUILD VERDE: todas las pruebas y umbrales OK' if aprobado else 'BUILD CON PROBLEMAS: revisar alertas'}</div>",
              "<!--ALERTAS-->",  # evaluar_alertas.py reemplaza esta marca con el panel de alertas
              "<div class='kpis'>"]
    if u:
        partes.append(kpi("Pruebas unitarias", f"{u['exitosas']}/{u['total']}", "ok" if u["fallidas"] == 0 else "bad"))
    if b:
        partes.append(kpi("Escenarios BDD", f"{b['exitosos']}/{b['total']}", "ok" if b["fallidos"] == 0 else "bad"))
    if p:
        p95_ok = all(x["ok"] for x in p["umbrales"] if x["metrica"] == "http_req_duration")
        partes += [kpi("TPS (req/s)", p["tps"]),
                   kpi("Latencia p95", f"{p['latencia_p95_ms']} ms", "ok" if p95_ok else "bad"),
                   kpi("Tasa de errores", f"{p['tasa_errores_pct']} %", "ok" if p["tasa_errores_pct"] < 1 else "bad"),
                   kpi("Requests totales", p["requests"])]
    partes.append("</div>")

    partes.append("<h2>Reportes detallados</h2><div class='card links'>"
                  "<a href='reportes/unitarias/surefire.html'>Reporte de pruebas unitarias</a>"
                  "<a href='reportes/bdd/cucumber.html'>Reporte BDD (Cucumber)</a>"
                  "<a href='reportes/performance/k6-reporte.html'>Reporte de performance (k6)</a>"
                  "<a href='metricas.json'>metricas.json</a><a href='alertas.json'>alertas.json</a></div>")

    if b:
        partes.append("<h2>Escenarios BDD</h2><div class='card'><table><tr><th>Escenario</th><th>Tags</th><th>Pasos</th><th>Tiempo</th><th>Estado</th></tr>")
        for e in b["escenarios"]:
            partes.append(f"<tr><td>{html.escape(e['nombre'])}</td><td>{html.escape(' '.join(e['tags']))}</td>"
                          f"<td class='num'>{e['pasos']}</td><td class='num'>{e['tiempo_ms']} ms</td>"
                          f"<td><span class='b {e['estado']}'>{e['estado']}</span></td></tr>")
        partes.append("</table></div>")

    if u:
        partes.append(f"<h2>Pruebas unitarias ({u['tiempo_s']} s)</h2><div class='card'><table><tr><th>Clase</th><th>Prueba</th><th>Tiempo</th><th>Estado</th></tr>")
        for c in u["casos"]:
            partes.append(f"<tr><td>{html.escape(c['clase'])}</td><td>{html.escape(c['nombre'])}</td>"
                          f"<td class='num'>{c['tiempo_s']} s</td><td><span class='b {c['estado']}'>{c['estado']}</span></td></tr>")
        partes.append("</table></div>")

    if p:
        partes.append("<h2>Performance: POST /api/login</h2><div class='card'><table><tr><th>Indicador</th><th>Valor</th></tr>")
        for etiqueta, clave, unidad in [("TPS", "tps", "req/s"), ("Latencia promedio", "latencia_avg_ms", "ms"),
                                        ("Latencia p90", "latencia_p90_ms", "ms"), ("Latencia p95", "latencia_p95_ms", "ms"),
                                        ("Latencia máxima", "latencia_max_ms", "ms"), ("Tasa de errores", "tasa_errores_pct", "%"),
                                        ("Logins exitosos", "login_exitoso_pct", "%"), ("Usuarios virtuales máx.", "vus_max", "")]:
            partes.append(f"<tr><td>{etiqueta}</td><td class='num'>{p[clave]} {unidad}</td></tr>")
        partes.append("</table><h3>Thresholds de k6</h3><table><tr><th>Métrica</th><th>Regla</th><th>Resultado</th></tr>")
        for t in p["umbrales"]:
            partes.append(f"<tr><td>{html.escape(t['metrica'])}</td><td>{html.escape(t['regla'])}</td>"
                          f"<td><span class='b {'ok' if t['ok'] else 'bad'}'>{'OK' if t['ok'] else 'FALLA'}</span></td></tr>")
        partes.append("</table></div>")

    partes.append("<h2>Tendencia entre ejecuciones</h2><div class='card'>")
    partes.append(tendencia_svg(historial, "latencia_p95_ms", "Latencia p95 del login", "ms"))
    partes.append(tendencia_svg(historial, "tasa_exito_pct", "Tasa de éxito funcional", "%"))
    partes.append("</div></div></body></html>")
    return "".join(partes)


def resumen_markdown(met):
    u, b, p = met["unitarias"], met["bdd"], met["performance"]
    icono = lambda ok: "✅" if ok else "❌"
    filas = ["## Dashboard de calidad", "", "| Indicador | Valor | Estado |", "|---|---|---|"]
    if u:
        filas.append(f"| Pruebas unitarias | {u['exitosas']}/{u['total']} | {icono(u['fallidas'] == 0)} |")
    if b:
        filas.append(f"| Escenarios BDD | {b['exitosos']}/{b['total']} | {icono(b['fallidos'] == 0)} |")
    if p:
        filas += [f"| TPS | {p['tps']} req/s | |",
                  f"| Latencia p95 | {p['latencia_p95_ms']} ms | {icono(p['latencia_p95_ms'] < 500)} |",
                  f"| Tasa de errores | {p['tasa_errores_pct']} % | {icono(p['tasa_errores_pct'] < 1)} |"]
    return "\n".join(filas) + "\n"


# ---------------------------------------------------------------- main
def git(*argumentos):
    """Datos del commit cuando se ejecuta en local (fuera de GitHub Actions)."""
    try:
        return subprocess.run(["git", *argumentos], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--surefire", default="target/surefire-reports")
    ap.add_argument("--cucumber", default="target/cucumber-reports/cucumber.json")
    ap.add_argument("--k6", default="target/performance/k6-summary.json")
    ap.add_argument("--historial", default=None, help="historial.json de ejecuciones anteriores (opcional)")
    ap.add_argument("--salida", default="target/dashboard")
    args = ap.parse_args()

    unitarias = leer_junit(args.surefire)
    bdd = leer_cucumber(args.cucumber)
    perf = leer_k6(args.k6)

    total = (unitarias or {}).get("total", 0) + (bdd or {}).get("total", 0)
    exitosas = (unitarias or {}).get("exitosas", 0) + (bdd or {}).get("exitosos", 0)
    umbrales_ok = all(t["ok"] for t in (perf or {}).get("umbrales", []))

    metricas = {
        "fecha": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ejecucion": os.environ.get("GITHUB_RUN_NUMBER", "local"),
        "commit": os.environ.get("GITHUB_SHA") or git("rev-parse", "HEAD") or "sin-commit",
        "rama": os.environ.get("GITHUB_REF_NAME") or git("rev-parse", "--abbrev-ref", "HEAD") or "local",
        "unitarias": unitarias,
        "bdd": bdd,
        "performance": perf,
        "tasa_exito_pct": round(exitosas * 100 / total, 2) if total else None,
        "build_verde": bool(total) and exitosas == total and umbrales_ok,
    }

    historial = []
    if args.historial and os.path.exists(args.historial):
        with open(args.historial, encoding="utf-8") as f:
            historial = json.load(f)
    historial.append({
        "fecha": metricas["fecha"],
        "ejecucion": metricas["ejecucion"],
        "commit": metricas["commit"][:7],
        "tasa_exito_pct": metricas["tasa_exito_pct"],
        "latencia_p95_ms": (perf or {}).get("latencia_p95_ms"),
        "tps": (perf or {}).get("tps"),
    })
    historial = historial[-50:]

    os.makedirs(args.salida, exist_ok=True)
    with open(os.path.join(args.salida, "metricas.json"), "w", encoding="utf-8") as f:
        json.dump(metricas, f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.salida, "historial.json"), "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.salida, "index.html"), "w", encoding="utf-8") as f:
        f.write(construir_html(metricas, historial))

    resumen = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumen:
        with open(resumen, "a", encoding="utf-8") as f:
            f.write(resumen_markdown(metricas))

    print(f"Dashboard generado en {os.path.join(args.salida, 'index.html')}")
    print(resumen_markdown(metricas))


if __name__ == "__main__":
    main()
