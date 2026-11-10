package cl.empresa.qa.login;

import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Repositorio en memoria. Cada instancia parte vacía, así cada prueba arma
 * sus propios datos y no hereda estado de otra (idempotencia).
 * Las claves se guardan como hash SHA-256, nunca en texto plano.
 */
public class RepositorioUsuariosEnMemoria implements RepositorioUsuarios {

    private final Map<String, String> usuarios = new ConcurrentHashMap<>();

    @Override
    public void registrar(String usuario, String clave) {
        usuarios.put(usuario, HashClave.sha256(clave));
    }

    @Override
    public Optional<String> buscarHashClave(String usuario) {
        return Optional.ofNullable(usuarios.get(usuario));
    }
}
