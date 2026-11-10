package cl.empresa.qa.bdd.helpers;

import cl.empresa.qa.login.RepositorioUsuarios;
import cl.empresa.qa.login.RepositorioUsuariosEnMemoria;
import cl.empresa.qa.login.ResultadoLogin;
import cl.empresa.qa.login.ServicioLogin;

import java.util.Map;

/**
 * Helper que concentra el "cómo" del login (preparar datos, llamar al
 * servicio, guardar el último resultado). Los step definitions solo
 * describen el "qué" y delegan aquí, como recomienda ME_4.
 *
 * Cucumber crea una instancia nueva de los steps (y de este helper) por
 * escenario, por lo que ningún escenario hereda estado de otro.
 */
public class LoginHelper {

    private final RepositorioUsuarios repositorio = new RepositorioUsuariosEnMemoria();
    private final ServicioLogin servicio = new ServicioLogin(repositorio);
    private ResultadoLogin ultimoResultado;

    public void registrarUsuarios(Iterable<Map<String, String>> filas) {
        for (Map<String, String> fila : filas) {
            repositorio.registrar(fila.get("usuario"), fila.get("clave"));
        }
    }

    public void intentarLogin(String usuario, String clave) {
        ultimoResultado = servicio.iniciarSesion(usuario, clave);
    }

    public void provocarIntentosFallidos(String usuario, int cantidad) {
        for (int i = 0; i < cantidad; i++) {
            servicio.iniciarSesion(usuario, "clave-incorrecta-" + i);
        }
    }

    public ResultadoLogin ultimoResultado() {
        if (ultimoResultado == null) {
            throw new IllegalStateException("Aún no se ha intentado iniciar sesión en este escenario");
        }
        return ultimoResultado;
    }
}
