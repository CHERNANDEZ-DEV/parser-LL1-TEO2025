int a, b;                // decl múltiple
double x;                // decl simple
char s;                  // para ejercitar cadenas
;                        // sentencia vacía (EMPTY)

a = (b + 3) * -2;        // UNARY (-), +, *, paréntesis
x = (a + b * 2) / (3 - -2);  // / y doble unario negativo

// if con else y negación lógica, comparación y aritmética
if (a >= 0 && !(a == 10))
    a = a - 1;
else {
    a = 0;
}

// while con OR y comparación distinta
while (a < 5 || b != 0) {
    a = a + 1;
    b = b - 1;
}

// for con DECL_NO_SEMI en el init, condición y post como asignación
for (int i = 0, j; i <= 3; i = i + 1) {
    // bloque con asignaciones y comparaciones adicionales
    if (i > 0 && j == 0) { j = i; }
    x = x + i * 1;
    b = b + i;
}

// uso de cadena como PRIMARY (tu gramática lo permite)
s = "OK";

// expresión lógica completa guardada en una variable float
float flag;
flag = (1 + 2 * 3 == 7 || 0 && 5);
