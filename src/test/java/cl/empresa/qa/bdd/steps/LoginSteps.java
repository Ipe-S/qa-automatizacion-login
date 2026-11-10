package cl.empresa.qa.bdd.steps;

import cl.empresa.qa.bdd.helpers.LoginHelper;
import io.cucumber.datatable.DataTable;
import io.cucumber.java.Before;
import io.cucumber.java.Scenario;
import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Step definitions del login. Son delgados: traducen cada paso Gherkin a
 * una llamada del helper y a una aserción. Usan expresiones {string} e {int}
 * para no duplicar pasos.
 */
public class LoginSteps {

    private LoginHelper login;

    @Before
    public void prepararEscenario(Scenario escenario) {
        // Estado limpio por escenario (idempotencia)
        login = new LoginHelper();
        escenario.log("Escenario preparado con repositorio en memoria vacío");
    }

    @Given("existen los siguientes usuarios registrados:")
    public void existenLosSiguientesUsuariosRegistrados(DataTable usuarios) {
        login.registrarUsuarios(usuarios.asMaps());
    }

    @Given("el usuario {string} falló el inicio de sesión {int} veces")
    public void elUsuarioFalloElInicioDeSesionVeces(String usuario, int veces) {
        login.provocarIntentosFallidos(usuario, veces);
    }

    @When("el usuario {string} ingresa la clave {string}")
    public void elUsuarioIngresaLaClave(String usuario, String clave) {
        login.intentarLogin(usuario, clave);
    }

    @Then("el acceso es concedido")
    public void elAccesoEsConcedido() {
        assertTrue(login.ultimoResultado().exitoso(), "Se esperaba acceso concedido");
    }

    @Then("el acceso es denegado")
    public void elAccesoEsDenegado() {
        assertFalse(login.ultimoResultado().exitoso(), "Se esperaba acceso denegado");
    }

    @Then("se muestra el mensaje {string}")
    public void seMuestraElMensaje(String mensajeEsperado) {
        assertEquals(mensajeEsperado, login.ultimoResultado().mensaje());
    }
}
