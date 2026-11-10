package cl.empresa.qa.calculadora;

/**
 * Calculadora simple usada para demostrar pruebas unitarias atómicas.
 * No guarda estado: cada operación depende solo de sus parámetros,
 * por eso cada prueba puede ejecutarse sola y en cualquier orden.
 */
public class Calculadora {

    public int sumar(int a, int b) {
        return Math.addExact(a, b);
    }

    public int restar(int a, int b) {
        return Math.subtractExact(a, b);
    }

    public int multiplicar(int a, int b) {
        return Math.multiplyExact(a, b);
    }

    /**
     * División entera.
     *
     * @throws IllegalArgumentException si el divisor es cero
     */
    public int dividir(int dividendo, int divisor) {
        if (divisor == 0) {
            throw new IllegalArgumentException("No se puede dividir por cero");
        }
        return dividendo / divisor;
    }
}
