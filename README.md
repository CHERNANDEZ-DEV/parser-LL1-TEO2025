# parser-LL1-TEO2025

Este repositorio contiene una implementación didáctica de un analizador sintáctico LL(1) junto con un analizador léxico mínimo y una batería de pruebas. El objetivo principal es ilustrar la construcción de un parser LL(1) para una gramática similar a un subconjunto de C, mostrar el cálculo de First/Follow/Tabla de parseo y ofrecer un runner de tests para validar comportamientos esperados.

**Contenido principal:** código del analizador, utilidades para First/Follow, tabla de parsing y carpeta de tests con casos esperados (ok / fail).

**Uso rápido**

- **Ejecutar un caso de prueba (muestra traza):**

```bash
python3 main.py tests/ok/001_suite_grande.c
```

- **Ejecutar un caso de prueba (muestra traza) con arbol de derivación:**

```bash
python3 ll1_parser_tree.py tests/ok/001_suite_grande.c
```

**Requisitos**
- Python 3.8+ (probado con CPython en macOS y Linux)
- PLY unicamente para el componente del lexer.
- No se usan dependencias externas; el proyecto es auto-contenido.

**Estructura del repositorio**
- `c_lexer.py`: Analizador léxico (tokenizador) para el subconjunto de lenguaje que acepta el parser.
- `ll1_parser.py`: Implementación principal del parser LL(1). Expone la función `parse(codigo: str, trazar: bool=False) -> bool` usada por `main.py`.
- `ll1_parser_tree.py`: Posible variante/ayuda para construir/recorrer el árbol sintáctico (dependiendo de la implementación interna).
- `main.py`: Runner de pruebas y utilidad para ejecutar parsing sobre archivos de `tests/`.
- `components/`
	- `First.md`, `Follow.md`, `Grammar.md`: Documentos con notas sobre el cálculo de First/Follow y la gramática usada.
	- `parsing_table.py`: Módulo que genera o contiene la tabla de parsing (dependiente del cálculo de First/Follow y de la gramática).
- `tests/`
	- `ok/`: Casos fuente que deben parsear correctamente (esperado: OK).
	- `fail/`: Casos que deben producir error de parseo (esperado: FALLO).
	- `mixed/`: Casos donde la expectativa debe definirse explícitamente en la primera línea del archivo con una directiva `//! EXPECT=OK` o `//! EXPECT=FAIL`.

Dentro de `tests/`, el runner permite una directiva por archivo para sobreescribir la expectativa por defecto: la primera línea puede contener `//! EXPECT=OK` o `//! EXPECT=FAIL`.

**Detalles funcionales**
- `main.py` procesa cada archivo de prueba leyendo su contenido y la expectativa (por carpeta o por directiva), llama a `parse(...)` y compara el resultado con lo esperado.
- La función `parse` devuelve `True` si la entrada fue aceptada por el parser, `False` en caso de error sintáctico.
- El runner imprime una traza cuando se ejecuta un único caso individual (útil para depuración).

**Cómo añadir tests**
- Para agregar un caso que debe ser aceptado: añádalo en `tests/ok/`.
- Para agregar un caso que debe fallar: añádalo en `tests/fail/`.
- Si quieres que la expectativa sea parte del propio archivo, coloca al inicio: `//! EXPECT=OK` o `//! EXPECT=FAIL`.

**Desarrollo y debugging**
- Para depurar un archivo y ver la traza del parser, ejecuta: `python3 main.py path/al/archivo.c`.
- Si quieres usar la API interna desde otro script, importa `parse` así:

```python
from ll1_parser import parse

codigo = open('tests/ok/001_suite_grande.c', encoding='utf-8').read()
ok = parse(codigo, trazar=True)
print(ok)
```

**Limitaciones conocidas**
- Implementación orientada a fines educativos: no es una herramienta industrial ni soporta todo el lenguaje C.
- No hay manejo avanzado de errores semánticos; foco en la sintaxis y la construcción de la tabla LL(1).
