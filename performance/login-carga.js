// Prueba básica de performance del endpoint POST /api/login con k6.
//
// Uso local:  k6 run performance/login-carga.js
//             k6 run -e BASE_URL=http://localhost:8080 performance/login-carga.js
//
// Indicadores que se monitorean:
//   - TPS (throughput) ......... métrica http_reqs (rate = requests por segundo)
//   - Latencia ................. http_req_duration: promedio, p(90) y p(95)
//   - Tasa de errores .......... http_req_failed (status >= 400 inesperado)
//   - Logins exitosos .......... métrica personalizada login_exitoso
//
// Los thresholds son el "contrato" de rendimiento: si se rompe uno,
// k6 termina con código distinto de 0 y el pipeline marca el job como fallido.

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

const loginExitoso = new Rate('login_exitoso');
const duracionLogin = new Trend('duracion_login', true);

export const options = {
  // Carga escalonada: subida, carga sostenida y bajada (~40 s en total)
  stages: [
    { duration: '10s', target: 10 },
    { duration: '20s', target: 20 },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'avg<200'], // latencia en ms
    http_req_failed: ['rate<0.01'],               // menos de 1 % de errores
    login_exitoso: ['rate>0.99'],                 // más de 99 % de logins correctos
    http_reqs: ['rate>10'],                       // TPS mínimo esperado
  },
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)'],
};

// Verifica que la API esté arriba antes de empezar a medir
export function setup() {
  const salud = http.get(`${BASE_URL}/health`);
  if (salud.status !== 200) {
    throw new Error(`La API no responde en ${BASE_URL} (status ${salud.status})`);
  }
}

export default function () {
  // Cada usuario virtual usa una cuenta de prueba distinta (perf01..perf50)
  const usuario = `perf${String((__VU % 50) + 1).padStart(2, '0')}`;

  const respuesta = http.post(
    `${BASE_URL}/api/login`,
    { usuario: usuario, clave: 'Perf2025!' },
    { tags: { endpoint: 'login' } },
  );

  const ok = check(respuesta, {
    'status es 200': (r) => r.status === 200,
    'respuesta indica acceso concedido': (r) => r.json('exitoso') === true,
  });

  loginExitoso.add(ok);
  duracionLogin.add(respuesta.timings.duration);

  sleep(0.5); // tiempo de "pensar" de un usuario real
}

// Guarda el resumen en JSON para el dashboard y lo muestra en consola
export function handleSummary(data) {
  const salida = __ENV.SUMMARY_PATH || 'target/performance/k6-summary.json';
  return {
    [salida]: JSON.stringify(data, null, 2),
    stdout: resumenTexto(data),
  };
}

function resumenTexto(data) {
  const m = data.metrics;
  const valor = (metrica, stat) => (m[metrica] && m[metrica].values[stat] !== undefined ? m[metrica].values[stat] : 0);
  const lineas = [
    '',
    '===== Resumen de performance: POST /api/login =====',
    `TPS (requests/s) ........ ${valor('http_reqs', 'rate').toFixed(2)}`,
    `Requests totales ........ ${valor('http_reqs', 'count')}`,
    `Latencia promedio ....... ${valor('http_req_duration', 'avg').toFixed(2)} ms`,
    `Latencia p(90) .......... ${valor('http_req_duration', 'p(90)').toFixed(2)} ms`,
    `Latencia p(95) .......... ${valor('http_req_duration', 'p(95)').toFixed(2)} ms`,
    `Latencia máxima ......... ${valor('http_req_duration', 'max').toFixed(2)} ms`,
    `Tasa de errores ......... ${(valor('http_req_failed', 'rate') * 100).toFixed(2)} %`,
    `Logins exitosos ......... ${(valor('login_exitoso', 'rate') * 100).toFixed(2)} %`,
    '',
    'Thresholds:',
  ];
  for (const [nombre, metrica] of Object.entries(m)) {
    if (metrica.thresholds) {
      for (const [regla, estado] of Object.entries(metrica.thresholds)) {
        lineas.push(`  ${estado.ok ? 'OK   ' : 'FALLA'} ${nombre}: ${regla}`);
      }
    }
  }
  return lineas.join('\n') + '\n';
}
