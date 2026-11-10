package cl.empresa.qa.login;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Pruebas unitarias del servicio de login.
 * Cada prueba usa un repositorio en memoria nuevo: no hay base de datos,
 * red ni estado compartido (alta cohesión, bajo acoplamiento).
 */
@DisplayName("ServicioLogin")
class ServicioLoginTest {

    private ServicioLogin servicio;

    @BeforeEach
    void prepararDatos() {
        RepositorioUsuarios repositorio = new RepositorioUsuariosEnMemoria();
        repositorio.registrar("ana", "Clave123!");
        servicio = new ServicioLogin(repositorio);
    }

    @Test
    @DisplayName("concede acceso con credenciales válidas")
    void concedeAccesoConCredencialesValidas() {
        ResultadoLogin resultado = servicio.iniciarSesion("ana", "Clave123!");

        assertTrue(resultado.exitoso());
        assertEquals("Bienvenido, ana", resultado.mensaje());
    }

    @Test
    @DisplayName("rechaza una clave incorrecta")
    void rechazaClaveIncorrecta() {
        ResultadoLogin resultado = servicio.iniciarSesion("ana", "otra");

        assertFalse(resultado.exitoso());
        assertEquals(ResultadoLogin.Estado.CREDENCIALES_INVALIDAS, resultado.estado());
    }

    @Test
    @DisplayName("rechaza un usuario inexistente con el mismo mensaje genérico")
    void rechazaUsuarioInexistente() {
        ResultadoLogin resultado = servicio.iniciarSesion("noexiste", "Clave123!");

        assertEquals("Usuario o contraseña incorrectos", resultado.mensaje());
    }

    @Test
    @DisplayName("exige usuario y clave")
    void exigeUsuarioYClave() {
        ResultadoLogin resultado = servicio.iniciarSesion(" ", "");

        assertEquals(ResultadoLogin.Estado.DATOS_INCOMPLETOS, resultado.estado());
    }

    @Test
    @DisplayName("los campos vacíos no cuentan como intento fallido")
    void camposVaciosNoCuentanComoIntento() {
        for (int i = 0; i < 5; i++) {
            servicio.iniciarSesion("ana", "");
        }

        assertFalse(servicio.estaBloqueado("ana"));
    }

    @Test
    @DisplayName("bloquea la cuenta al tercer intento fallido")
    void bloqueaCuentaAlTercerIntentoFallido() {
        servicio.iniciarSesion("ana", "mala1");
        servicio.iniciarSesion("ana", "mala2");

        ResultadoLogin tercerIntento = servicio.iniciarSesion("ana", "mala3");

        assertEquals(ResultadoLogin.Estado.CUENTA_BLOQUEADA, tercerIntento.estado());
        assertTrue(servicio.estaBloqueado("ana"));
    }

    @Test
    @DisplayName("un ingreso exitoso reinicia el contador de intentos")
    void ingresoExitosoReiniciaContador() {
        servicio.iniciarSesion("ana", "mala1");
        servicio.iniciarSesion("ana", "mala2");
        servicio.iniciarSesion("ana", "Clave123!");

        ResultadoLogin resultado = servicio.iniciarSesion("ana", "mala3");

        assertEquals(ResultadoLogin.Estado.CREDENCIALES_INVALIDAS, resultado.estado());
    }
}
