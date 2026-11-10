package cl.empresa.qa.calculadora;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

/**
 * Pruebas unitarias atómicas: cada método verifica UNA sola regla,
 * crea su propio objeto (@BeforeEach) y no depende del orden de ejecución.
 * Estructura Arrange / Act / Assert en cada prueba.
 */
@DisplayName("Calculadora")
class CalculadoraTest {

    private Calculadora calculadora;

    @BeforeEach
    void prepararCalculadoraNueva() {
        calculadora = new Calculadora();
    }

    @Test
    @DisplayName("suma dos números positivos")
    void sumaDosNumerosPositivos() {
        int resultado = calculadora.sumar(2, 3);

        assertEquals(5, resultado);
    }

    @Test
    @DisplayName("resta dos números y puede dar negativo")
    void restaDosNumeros() {
        int resultado = calculadora.restar(3, 5);

        assertEquals(-2, resultado);
    }

    @Test
    @DisplayName("multiplica dos números")
    void multiplicaDosNumeros() {
        assertEquals(12, calculadora.multiplicar(3, 4));
    }

    @Test
    @DisplayName("divide dos números con resultado entero")
    void divideDosNumeros() {
        assertEquals(4, calculadora.dividir(8, 2));
    }

    @Test
    @DisplayName("lanza error al dividir por cero")
    void lanzaErrorAlDividirPorCero() {
        IllegalArgumentException error = assertThrows(IllegalArgumentException.class,
                () -> calculadora.dividir(10, 0));

        assertEquals("No se puede dividir por cero", error.getMessage());
    }

    @Test
    @DisplayName("detecta desbordamiento al sumar")
    void detectaDesbordamientoAlSumar() {
        assertThrows(ArithmeticException.class, () -> calculadora.sumar(Integer.MAX_VALUE, 1));
    }

    @ParameterizedTest(name = "{0} + {1} = {2}")
    @DisplayName("suma con distintos datos (datos parametrizados)")
    @CsvSource({
            "0, 0, 0",
            "-4, 4, 0",
            "-2, -3, -5",
            "100, 250, 350"
    })
    void sumaConDistintosDatos(int a, int b, int esperado) {
        assertEquals(esperado, calculadora.sumar(a, b));
    }
}
