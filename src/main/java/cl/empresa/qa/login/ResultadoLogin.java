package cl.empresa.qa.login;

/**
 * Resultado de un intento de inicio de sesión.
 *
 * @param exitoso   true si el acceso fue concedido
 * @param estado    código de negocio del resultado
 * @param mensaje   texto que se muestra al usuario
 */
public record ResultadoLogin(boolean exitoso, Estado estado, String mensaje) {

    public enum Estado {
        CONCEDIDO,
        CREDENCIALES_INVALIDAS,
        DATOS_INCOMPLETOS,
        CUENTA_BLOQUEADA
    }

    static ResultadoLogin concedido(String usuario) {
        return new ResultadoLogin(true, Estado.CONCEDIDO, "Bienvenido, " + usuario);
    }

    static ResultadoLogin credencialesInvalidas() {
        return new ResultadoLogin(false, Estado.CREDENCIALES_INVALIDAS, "Usuario o contraseña incorrectos");
    }

    static ResultadoLogin datosIncompletos() {
        return new ResultadoLogin(false, Estado.DATOS_INCOMPLETOS, "Debe ingresar usuario y contraseña");
    }

    static ResultadoLogin cuentaBloqueada() {
        return new ResultadoLogin(false, Estado.CUENTA_BLOQUEADA, "Cuenta bloqueada. Contacte a soporte");
    }
}
