package cl.empresa.qa.login;

import java.util.Optional;

/**
 * Acceso a los usuarios registrados. Es una interfaz para que el servicio
 * no dependa de una base de datos concreta (bajo acoplamiento) y las pruebas
 * puedan usar una implementación en memoria.
 */
public interface RepositorioUsuarios {

    void registrar(String usuario, String clave);

    /** Devuelve el hash de la clave del usuario, si existe. */
    Optional<String> buscarHashClave(String usuario);
}
