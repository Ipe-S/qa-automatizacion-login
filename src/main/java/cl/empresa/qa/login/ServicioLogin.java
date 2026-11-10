package cl.empresa.qa.login;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Reglas de negocio del inicio de sesión acordadas en la sesión Three Amigos
 * (ver docs/three-amigos.md):
 * <ol>
 *   <li>Usuario y clave son obligatorios.</li>
 *   <li>Si el usuario no existe o la clave no coincide, se muestra el mismo
 *       mensaje genérico para no revelar qué dato falló.</li>
 *   <li>Después de 3 intentos fallidos seguidos la cuenta queda bloqueada,
 *       aunque luego se ingrese la clave correcta.</li>
 *   <li>Un ingreso exitoso reinicia el contador de intentos.</li>
 * </ol>
 */
public class ServicioLogin {

    public static final int MAX_INTENTOS_FALLIDOS = 3;

    private final RepositorioUsuarios repositorio;
    private final Map<String, Integer> intentosFallidos = new ConcurrentHashMap<>();

    public ServicioLogin(RepositorioUsuarios repositorio) {
        this.repositorio = repositorio;
    }

    public ResultadoLogin iniciarSesion(String usuario, String clave) {
        if (estaVacio(usuario) || estaVacio(clave)) {
            return ResultadoLogin.datosIncompletos();
        }
        if (estaBloqueado(usuario)) {
            return ResultadoLogin.cuentaBloqueada();
        }

        boolean claveCorrecta = repositorio.buscarHashClave(usuario)
                .map(hashGuardado -> hashGuardado.equals(HashClave.sha256(clave)))
                .orElse(false);

        if (claveCorrecta) {
            intentosFallidos.remove(usuario);
            return ResultadoLogin.concedido(usuario);
        }

        int intentos = intentosFallidos.merge(usuario, 1, Integer::sum);
        return intentos >= MAX_INTENTOS_FALLIDOS
                ? ResultadoLogin.cuentaBloqueada()
                : ResultadoLogin.credencialesInvalidas();
    }

    public boolean estaBloqueado(String usuario) {
        return intentosFallidos.getOrDefault(usuario, 0) >= MAX_INTENTOS_FALLIDOS;
    }

    private static boolean estaVacio(String valor) {
        return valor == null || valor.isBlank();
    }
}
