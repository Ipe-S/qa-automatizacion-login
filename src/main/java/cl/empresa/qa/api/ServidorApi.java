package cl.empresa.qa.api;

import cl.empresa.qa.login.RepositorioUsuariosEnMemoria;
import cl.empresa.qa.login.ResultadoLogin;
import cl.empresa.qa.login.ServicioLogin;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.Executors;

/**
 * API HTTP mínima (solo JDK, sin frameworks) que expone el login para la
 * prueba de performance con k6.
 *
 * <pre>
 *   GET  /health        -> 200 {"estado":"ok"}
 *   POST /api/login     -> body: usuario=ana&amp;clave=Clave123!
 *                          200 concedido | 401 credenciales inválidas
 *                          400 datos incompletos | 423 cuenta bloqueada
 * </pre>
 *
 * Variables de entorno:
 *   PORT                  puerto (por defecto 8080)
 *   LATENCIA_SIMULADA_MS  retardo artificial por request; se usa SOLO para
 *                         simular una degradación y comprobar que las alertas
 *                         se disparan (por defecto 0)
 */
public final class ServidorApi {

    private ServidorApi() {
    }

    public static void main(String[] args) throws IOException {
        int puerto = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));
        long latenciaSimuladaMs = Long.parseLong(System.getenv().getOrDefault("LATENCIA_SIMULADA_MS", "0"));

        HttpServer servidor = crear(puerto, latenciaSimuladaMs);
        servidor.start();
        System.out.printf("API de login escuchando en http://localhost:%d (latencia simulada: %d ms)%n",
                puerto, latenciaSimuladaMs);
    }

    public static HttpServer crear(int puerto, long latenciaSimuladaMs) throws IOException {
        RepositorioUsuariosEnMemoria repositorio = new RepositorioUsuariosEnMemoria();
        // Usuarios de demostración para la prueba de carga (no son credenciales reales)
        repositorio.registrar("ana", "Clave123!");
        for (int i = 1; i <= 50; i++) {
            repositorio.registrar(String.format("perf%02d", i), "Perf2025!");
        }
        ServicioLogin servicio = new ServicioLogin(repositorio);

        HttpServer servidor = HttpServer.create(new InetSocketAddress(puerto), 0);
        servidor.setExecutor(Executors.newFixedThreadPool(32));

        servidor.createContext("/health", intercambio ->
                responder(intercambio, 200, "{\"estado\":\"ok\"}"));

        servidor.createContext("/api/login", intercambio -> {
            if (!"POST".equals(intercambio.getRequestMethod())) {
                responder(intercambio, 405, "{\"mensaje\":\"Método no permitido\"}");
                return;
            }
            simularLatencia(latenciaSimuladaMs);
            Map<String, String> datos = leerFormulario(intercambio);
            ResultadoLogin resultado = servicio.iniciarSesion(datos.get("usuario"), datos.get("clave"));
            responder(intercambio, codigoHttp(resultado), String.format(
                    "{\"exitoso\":%s,\"estado\":\"%s\",\"mensaje\":\"%s\"}",
                    resultado.exitoso(), resultado.estado(), resultado.mensaje()));
        });
        return servidor;
    }

    static int codigoHttp(ResultadoLogin resultado) {
        return switch (resultado.estado()) {
            case CONCEDIDO -> 200;
            case CREDENCIALES_INVALIDAS -> 401;
            case DATOS_INCOMPLETOS -> 400;
            case CUENTA_BLOQUEADA -> 423;
        };
    }

    private static Map<String, String> leerFormulario(HttpExchange intercambio) throws IOException {
        String cuerpo = new String(intercambio.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
        Map<String, String> datos = new HashMap<>();
        for (String par : cuerpo.split("&")) {
            String[] partes = par.split("=", 2);
            if (partes.length == 2) {
                datos.put(URLDecoder.decode(partes[0], StandardCharsets.UTF_8),
                        URLDecoder.decode(partes[1], StandardCharsets.UTF_8));
            }
        }
        return datos;
    }

    private static void simularLatencia(long milisegundos) {
        if (milisegundos <= 0) {
            return;
        }
        try {
            Thread.sleep(milisegundos);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private static void responder(HttpExchange intercambio, int codigo, String json) throws IOException {
        byte[] cuerpo = json.getBytes(StandardCharsets.UTF_8);
        intercambio.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
        intercambio.sendResponseHeaders(codigo, cuerpo.length);
        try (OutputStream salida = intercambio.getResponseBody()) {
            salida.write(cuerpo);
        }
    }
}
