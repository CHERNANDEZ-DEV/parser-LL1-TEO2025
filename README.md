# Parser LL(1) - Compilador de "C" simplificado

Este proyecto implementa un analizador sintáctico LL(1) para un subconjunto del lenguaje C, incluyendo análisis léxico, sintáctico y semántico. Es un proyecto académico diseñado para la asignatura de Teória de lenguajes de programación, que demuestra las fases fundamentales de un compilador.

## Características

### Lenguaje soportado
El parser maneja un subconjunto de C que incluye:

- **Tipos de datos**: `int`, `char`, `float`, `double`, `void`
- **Declaraciones**: Variables y funciones
- **Arrays**: Declaración y acceso con índices
- **Estructuras de control**: 
  - `if`/`else`
  - `while`
  - `for`
- **Expresiones**: 
  - Operadores aritméticos (`+`, `-`, `*`, `/`, `%`)
  - Operadores de comparación (`<`, `<=`, `>`, `>=`, `==`, `!=`)
  - Operadores lógicos (`&&`, `||`, `!`)
  - Asignaciones (`=`)
  - Llamadas a función
- **Punteros**: Declaración y desreferenciamiento básico

### Arquitectura
El proyecto está organizado en módulos bien diferenciados:

```
parser-LL1-TEO2025/
├── cli.py              # Interfaz de línea de comandos
├── ast/                # Árbol de sintaxis abstracta
│   ├── nodes.py        # Definiciones de nodos AST
│   └── pretty.py       # Impresión formateada del AST
├── lexer/              # Analizador léxico
│   ├── lexer.py        # Tokenizador principal
│   └── tokens.py       # Definiciones de tokens
├── parser/             # Analizador sintáctico LL(1)
│   ├── parser.py       # Parser principal
│   └── errors.py       # Manejo de errores de parsing
├── sema/               # Análisis semántico
│   ├── checker.py      # Verificador semántico
│   └── symtab.py       # Tabla de símbolos
└── tests/              # Suite de pruebas
    ├── test_lexer.py
    ├── test_parser_ok.py
    ├── test_parser_error.py
    ├── test_sema_ok.py
    └── test_sema_error.py
```

## Requisitos

- **Python 3.7+** (probado con Python 3.13)
- No requiere dependencias externas (solo biblioteca estándar de Python)

## Instalación

1. Clona o descarga este repositorio:
```bash
git clone <url-del-repositorio>
cd parser-LL1-TEO2025
```

2. El proyecto no requiere instalación adicional, solo Python 3.7+

## Uso

### Ejecutar el parser

#### Con el ejemplo integrado:
```bash
PYTHONPATH=. python3 cli.py
```

#### Con un archivo de código fuente:
```bash
PYTHONPATH=. python3 cli.py mi_programa.c
```

### Ejemplo de Salida

Para el código de ejemplo integrado:
```c
int sum(int n){
  int i = 0, acc = 0;
  for(i = 0; i < n; i = i + 1){
    acc = acc + i;
  }
  return acc;
}
```

El parser genera:
```
Func int sum(int n)
{
  Var int i = 0, acc = 0
  For (init=(i = 0), cond=(i < n), it=(i = (i + 1)))
    {
      Expr (acc = (acc + i))
    }
  Return acc
}
```

### Manejo de errores

El parser reporta errores tanto de análisis sintáctico como semántico:

```bash
# Ejemplo con errores
echo 'int x = y + 1;' > error_test.c
PYTHONPATH=. python3 cli.py error_test.c
```

Salida:
```
Error en línea 1, columna 9: 'y' no declarada
<salida del AST con errores>
```

## Ejecutar las pruebas

### Ejecutar todas las pruebas
```bash
# Método 1: Usando el script de prueba manual
cd /Users/ch/Documents/DEV/parser-LL1-TEO2025
PYTHONPATH=. python3 -c "
import tests.test_lexer
import tests.test_parser_ok  
import tests.test_parser_error
import tests.test_sema_ok
import tests.test_sema_error

# Ejecutar pruebas del lexer
try:
    tests.test_lexer.test_keywords_and_ops()
    print('✓ test_lexer.test_keywords_and_ops: PASS')
except Exception as e:
    print(f'✗ test_lexer.test_keywords_and_ops: FAIL - {e}')

# Ejecutar pruebas del parser (casos exitosos)
try:
    tests.test_parser_ok.test_parse_function_sum()
    print('✓ test_parser_ok.test_parse_function_sum: PASS')
except Exception as e:
    print(f'✗ test_parser_ok.test_parse_function_sum: FAIL - {e}')

# Ejecutar pruebas del parser (casos con errores)
try:
    tests.test_parser_error.test_error_recovery_missing_semi()
    print('✓ test_parser_error.test_error_recovery_missing_semi: PASS')
except Exception as e:
    print(f'✗ test_parser_error.test_error_recovery_missing_semi: FAIL - {e}')

# Ejecutar pruebas semánticas (casos exitosos)  
try:
    tests.test_sema_ok.test_sema_ok_sum()
    print('✓ test_sema_ok.test_sema_ok_sum: PASS')
except Exception as e:
    print(f'✗ test_sema_ok.test_sema_ok_sum: FAIL - {e}')

# Ejecutar pruebas semánticas (casos con errores)
try:
    tests.test_sema_error.test_undeclared_and_bad_call()
    print('✓ test_sema_error.test_undeclared_and_bad_call: PASS')
except Exception as e:
    print(f'✗ test_sema_error.test_undeclared_and_bad_call: FAIL - {e}')
"
```

### Ejecutar pruebas individuales

#### Pruebas del lexer:
```bash
PYTHONPATH=. python3 -c "
import tests.test_lexer
tests.test_lexer.test_keywords_and_ops()
print('Lexer tests: PASS')
"
```

#### Pruebas del parser:
```bash
PYTHONPATH=. python3 -c "
import tests.test_parser_ok
tests.test_parser_ok.test_parse_function_sum()
print('Parser tests: PASS')
"
```

#### Pruebas semánticas:
```bash
PYTHONPATH=. python3 -c "
import tests.test_sema_ok
tests.test_sema_ok.test_sema_ok_sum()
print('Semantic analysis tests: PASS')
"
```

## Componentes del sistema

### 1. Analizador léxico (`lexer/`)
- **`tokens.py`**: Define los tipos de tokens (palabras clave, operadores, identificadores, etc.)
- **`lexer.py`**: Implementa el tokenizador que convierte el código fuente en tokens

### 2. Analizador sintáctico (`parser/`)
- **`parser.py`**: Implementa un parser LL(1) con recuperación de errores
- **`errors.py`**: Manejo de errores de parsing
- Soporta precedencia de operadores y análisis descendente recursivo

### 3. AST (`ast/`)
- **`nodes.py`**: Definiciones de todos los nodos del árbol de sintaxis abstracta
- **`pretty.py`**: Formateo e impresión del AST para visualización

### 4. Análisis semántico (`sema/`)
- **`checker.py`**: Verificación de tipos, declaraciones y reglas semánticas
- **`symtab.py`**: Tabla de símbolos con soporte para ámbitos anidados

### 5. Interfaz CLI (`cli.py`)
- Punto de entrada principal que integra todos los componentes
- Acepta archivos de entrada o usa el ejemplo integrado
- Muestra errores y el AST resultante

## Ejemplos de código soportado

### Función simple
```c
int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}
```

### Arrays
```c
int main() {
    int arr[10];
    int i;
    for (i = 0; i < 10; i = i + 1) {
        arr[i] = i * i;
    }
    return arr[5];
}
```

### Variables y expresiones
```c
int calculate() {
    int x = 5, y = 10;
    int result = x + y * 2;
    return result;
}
```

## Limitaciones conocidas

1. **No soporta**:
   - Estructuras (`struct`)  
   - Uniones (`union`)
   - Preprocesador (`#include`, `#define`)
   - Strings literales completas
   - Múltiples archivos fuente

2. **Análisis semántico básico**:
   - Verificación de tipos simplificada
   - Conversiones implícitas limitadas

## Desarrollo y contribución

### Estructura de desarrollo

- Cada módulo es independiente y puede probarse por separado
- Los tests están organizados por componente
- El sistema usa tipado estático con `typing` para mayor claridad

## Notas Técnicas

- El parser utiliza análisis LL(1) con recuperación de errores
- La tabla de símbolos soporta ámbitos anidados
- El sistema maneja precedencia de operadores correctamente
- El AST es inmutable y fácil de recorrer para análisis posteriores