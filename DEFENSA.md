# Preguntas y respuestas para defensa - Parser LL(1)

## Preguntas básicas (Fundamentos)

### **P1: ¿Qué significa LL(1) y por qué eligieron esta técnica para su proyecto?**

**Respuesta:**
LL(1) significa:
- **L** (Left-to-right): Leemos los tokens de izquierda a derecha
- **L** (Leftmost derivation): Construimos derivaciones por la izquierda
- **(1)**: Usamos 1 token de lookahead para tomar decisiones

Elegimos LL(1) porque:
1. **Simplicidad de implementación**: Es más directo implementar que LR(1)
2. **Detección temprana de errores**: Los errores se detectan tan pronto como aparecen
3. **Recuperación de errores predecible**: Podemos implementar estrategias de recuperación claras
4. **Comprensión didáctica**: Es más fácil entender el flujo del algoritmo
5. **Eficiencia**: O(n) tiempo lineal, sin backtracking

---

### **P2: Explique las fases de su compilador y cómo se relacionan entre sí.**

**Respuesta:**
Nuestro compilador tiene 4 fases principales:

1. **Análisis Léxico (lexer/)**:
   - **Input**: Código fuente (string)
   - **Output**: Lista de tokens
   - **Función**: Convierte caracteres en unidades léxicas (palabras clave, operadores, identificadores)

2. **Análisis Sintáctico (parser/)**:
   - **Input**: Lista de tokens
   - **Output**: AST + lista de errores sintácticos
   - **Función**: Verifica estructura gramatical y construye árbol de sintaxis

3. **Análisis Semántico (sema/)**:
   - **Input**: AST
   - **Output**: Lista de errores semánticos
   - **Función**: Verifica tipos, declaraciones, ámbitos

4. **Pretty Printer (ast/pretty.py)**:
   - **Input**: AST
   - **Output**: Representación textual del árbol
   - **Función**: Visualización para debugging y análisis

**Flujo de datos:**
```
Código fuente → [Lexer] → Tokens → [Parser] → AST → [Semantic] → AST validado
                                      ↓
                              [Pretty Printer] → Visualización
```

---

### **P3: ¿Cómo maneja su parser la precedencia de operadores?**

**Respuesta:**
Usamos la técnica de **precedence climbing** con una tabla de precedencia:

```python
_PREC = [
    {TokenKind.OROR},           # Precedencia 0 (más baja)
    {TokenKind.ANDAND},         # Precedencia 1
    {TokenKind.EQEQ, TokenKind.NEQ},     # Precedencia 2
    {TokenKind.LT, TokenKind.LE, TokenKind.GT, TokenKind.GE}, # Precedencia 3
    {TokenKind.PLUS, TokenKind.MINUS},   # Precedencia 4
    {TokenKind.STAR, TokenKind.SLASH, TokenKind.PERCENT},     # Precedencia 5 (más alta)
]
```

**Algoritmo:**
```python
def parse_bin_level(level: int) -> Expr:
    if level >= len(_PREC):
        return parse_unary()  # Base case
    left = parse_bin_level(level + 1)  # Operadores de mayor precedencia primero
    while tokens[i].kind in _PREC[level]:
        op_tok = tokens[i]
        right = parse_bin_level(level + 1)  # Recursión para mantener precedencia
        left = Binary(_BIN_OP_STR[op_tok.kind], left, right)
    return left
```

**Ejemplo**: `2 + 3 * 4` se parsea como `2 + (3 * 4)` porque `*` (nivel 5) tiene mayor precedencia que `+` (nivel 4).

---

## Preguntas intermedias (Implementación)

### **P4: ¿Cómo implementaron la recuperación de errores en su parser?**

**Respuesta:**
Implementamos recuperación de errores usando **panic mode recovery**:

1. **Detección**: Cuando `expect()` falla, lanzamos `ParseError`
2. **Sincronización**: Usamos `synchronize()` para buscar tokens de sincronización
3. **Continuación**: El parser continúa desde el punto de sincronización

```python
def expect(kind: TokenKind, msg: str):
    if tokens[i].kind == kind:
        i += 1
        return tokens[i-1]
    t = tokens[i]
    report(errors, t.line, t.col, msg + f"; se encontró '{t.lexeme}'")
    raise ParseError()  # ← Detección

def synchronize(sync_kinds: set[TokenKind]):
    while tokens[i].kind not in sync_kinds and tokens[i].kind != TokenKind.EOF:
        i += 1  # ← Sincronización

# Uso en declaraciones:
try:
    ts = parse_type()
except ParseError:
    synchronize({TokenKind.SEMI, TokenKind.RBRACE})  # ← Recuperación
    match(TokenKind.SEMI)
    return None
```

**Ventajas:**
- Reporta múltiples errores en una sola pasada
- No se detiene en el primer error
- Tokens de sincronización bien elegidos (`;`, `}`)

---

### **P5: Explique cómo funciona su tabla de símbolos y el manejo de ámbitos.**

**Respuesta:**
Implementamos una **pila de ámbitos** para manejar la visibilidad de símbolos:

```python
# Stack de scopes
_scope_stack: List[Dict[str, Symbol]] = []

def enter_scope():
    _scope_stack.append({})  # Nuevo ámbito

def leave_scope():
    if _scope_stack:
        _scope_stack.pop()  # Salir del ámbito actual

def declare(symbol: Symbol, errors: List[str], line: int, col: int):
    current_scope = _scope_stack[-1]  # Ámbito más interno
    if name in current_scope:
        errors.append(f"'{name}' ya declarado en este ámbito")
    else:
        current_scope[name] = symbol

def lookup(name: str) -> Optional[Symbol]:
    # Buscar desde el ámbito más interno hacia afuera
    for scope in reversed(_scope_stack):
        if name in scope:
            return scope[name]
    return None  # No encontrado
```

**Ejemplo de uso:**
```c
int global_var = 10;    // Ámbito global
int func(int param) {   // Nuevo ámbito (función)
    int local = 5;      // Variable local
    if (param > 0) {    // Nuevo ámbito (if)
        int nested = 3; // Variable anidada
        return local + nested;  // ✅ Ambas visibles
    }
    return nested;      // ❌ Error: 'nested' no visible
}
```

---

### **P6: ¿Cómo verifican la compatibilidad de tipos en las expresiones?**

**Respuesta:**
Implementamos verificación de tipos en el análisis semántico:

```python
def is_integer(t: TypeSpec | ArrayType | None) -> bool:
    return isinstance(t, TypeSpec) and t.ptr_depth == 0 and t.base in {"int", "char"}

def is_arith(t: TypeSpec | ArrayType | None) -> bool:
    return isinstance(t, TypeSpec) and t.ptr_depth == 0 and t.base in {"int", "char", "float", "double"}

def assignable(dst: TypeSpec | ArrayType, src: TypeSpec | ArrayType) -> bool:
    # Tipos exactamente iguales
    if dst.base == src.base and dst.ptr_depth == src.ptr_depth:
        return True
    
    # Conversión entre tipos numéricos
    num = {"char", "int", "float", "double"}
    if dst.ptr_depth == 0 and src.ptr_depth == 0 and dst.base in num and src.base in num:
        return True
    
    # Conversión entre punteros
    if dst.ptr_depth > 0 and src.ptr_depth > 0:
        return True
    
    return False
```

**Verificaciones específicas:**
1. **Operaciones aritméticas**: Ambos operandos deben ser tipos aritméticos
2. **Operaciones lógicas**: Operandos deben ser enteros o punteros
3. **Asignaciones**: Tipos deben ser asignables según `assignable()`
4. **Índices de arrays**: El índice debe ser entero
5. **Llamadas a función**: Número y tipos de parámetros deben coincidir

---

## Preguntas avanzadas (Diseño y Optimización)

### **P7: ¿Qué limitaciones tiene su gramática LL(1) y cómo las resolvieron?**

**Respuesta:**

**Limitaciones principales:**

1. **Recursión izquierda**: No permitida en LL(1)
2. **Factorización izquierda**: Necesaria para prefijos comunes  
3. **Ambigüedades**: Como el "dangling else"

**Soluciones implementadas:**

### **1. Recursión Izquierda - Solución con Precedence Climbing:**

**El problema clásico:**
```
❌ Gramática con recursión izquierda (NO funciona en LL(1)):
Expresión → Expresión '+' Término    // Bucle infinito
Expresión → Expresión '-' Término    // Bucle infinito  
Expresión → Término                  // Caso base
```

**Transformación clásica (teórica):**
```
✅ Transformación estándar:
Expresión → Término RestExpresión
RestExpresión → '+' Término RestExpresión | '-' Término RestExpresión | ε
```

**Nuestra solución superior - Precedence Climbing:**
```python
# parser/parser.py - líneas 207-215
def parse_bin_level(level: int) -> Expr:
    if level >= len(_PREC):
        return parse_unary()  # Base case - no recursión izquierda
    
    left = parse_bin_level(level + 1)  # Recursión hacia ADELANTE (mayor precedencia)
    
    while tokens[i].kind in _PREC[level]:  # ITERACIÓN en lugar de recursión
        op_tok = tokens[i]; i_inc()
        right = parse_bin_level(level + 1)  # Recursión hacia ADELANTE
        left = Binary(_BIN_OP_STR[op_tok.kind], left, right)  # Acumulación
    return left
```

**Tabla de precedencia:**
```python
# parser/parser.py - líneas 11-18  
_PREC = [
    {TokenKind.OROR},           # Precedencia 0 (más baja)
    {TokenKind.ANDAND},         # Precedencia 1
    {TokenKind.EQEQ, TokenKind.NEQ},     # Precedencia 2
    {TokenKind.LT, TokenKind.LE, TokenKind.GT, TokenKind.GE}, # Precedencia 3
    {TokenKind.PLUS, TokenKind.MINUS},   # Precedencia 4
    {TokenKind.STAR, TokenKind.SLASH, TokenKind.PERCENT},     # Precedencia 5 (más alta)
]
```

**Ejemplo de traza para `2 + 3 + 4`:**
```
parse_bin_level(4)  // Nivel de + y -
├── left = parse_bin_level(5) → Number(2)  // Sin recursión izquierda
├── while PLUS in _PREC[4]:
│   ├── right = parse_bin_level(5) → Number(3)  
│   └── left = Binary('+', Number(2), Number(3))  // Acumulación
└── while PLUS in _PREC[4]:
    ├── right = parse_bin_level(5) → Number(4)
    └── left = Binary('+', Binary('+', 2, 3), Number(4))  // Asociatividad izquierda correcta
```

**Ventajas de nuestra implementación:**
- ✅ **Una sola función** maneja todos los operadores binarios
- ✅ **Precedencia automática** basada en tabla
- ✅ **Escalable**: Agregar operadores es trivial
- ✅ **Eficiente**: O(n) sin backtracking
- ✅ **Asociatividad correcta** sin recursión izquierda

### **2. Para el dangling else:** 
Regla implícita greedy matching - el `else` se asocia con el `if` más cercano

### **3. Para factorización izquierda:** 
Reestructuramos reglas para eliminar prefijos comunes

**Gramáticas que NO podemos manejar:**
- Lenguajes que requieren contexto (LL(1) es libre de contexto)
- Construcciones que necesitan más de 1 token lookahead
- Gramáticas inherentemente ambiguas

---

### **P8: Explique específicamente cómo resolvieron el problema de la recursión izquierda en las expresiones aritméticas.**

**Respuesta:**

**El problema fundamental:**
La recursión izquierda causa **bucles infinitos** en parsers LL(1):

```python
# ❌ Esto NO funcionaría:
def parse_expresion():
    left = parse_expresion()  # ← ¡BUCLE INFINITO!
    if current_token == PLUS:
        consume(PLUS)
        right = parse_termino()
        return Binary('+', left, right)
    return left
```

**Nuestra solución - Precedence Climbing Algorithm:**

**Paso 1**: Definimos tabla de precedencia (de menor a mayor):
```python
_PREC = [
    {TokenKind.OROR},           # 0: ||
    {TokenKind.ANDAND},         # 1: &&  
    {TokenKind.EQEQ, TokenKind.NEQ},     # 2: == !=
    {TokenKind.LT, TokenKind.LE, TokenKind.GT, TokenKind.GE}, # 3: < <= > >=
    {TokenKind.PLUS, TokenKind.MINUS},   # 4: + -
    {TokenKind.STAR, TokenKind.SLASH, TokenKind.PERCENT},     # 5: * / %
]
```

**Paso 2**: Algoritmo que evita recursión izquierda:
```python
def parse_bin_level(level: int) -> Expr:
    # Base case: nivel más alto → operadores unarios
    if level >= len(_PREC):
        return parse_unary()
    
    # ✅ CLAVE: Empezar con operadores de MAYOR precedencia
    left = parse_bin_level(level + 1)  # No es recursión izquierda
    
    # ✅ ITERACIÓN en lugar de recursión para mismo nivel
    while tokens[i].kind in _PREC[level]:
        op_tok = tokens[i]; i_inc()
        right = parse_bin_level(level + 1)  # Otra vez mayor precedencia
        left = Binary(_BIN_OP_STR[op_tok.kind], left, right)
    
    return left
```

**Ejemplo paso a paso con `2 + 3 * 4`:**

```
parse_bin_level(4)  // Nivel de + y -
├── left = parse_bin_level(5)  // Nivel de * / %
│   ├── left = parse_bin_level(6)  // Base case
│   │   └── return parse_unary() → Number(2)
│   └── while: no hay * o /, return Number(2)
├── while tokens[i] == PLUS:  // Encontró +
│   ├── right = parse_bin_level(5)  // Nivel de * / %
│   │   ├── left = parse_unary() → Number(3)
│   │   ├── while tokens[i] == STAR:  // Encontró *
│   │   │   ├── right = parse_unary() → Number(4)  
│   │   │   └── left = Binary('*', Number(3), Number(4))
│   │   └── return Binary('*', Number(3), Number(4))
│   └── left = Binary('+', Number(2), Binary('*', Number(3), Number(4)))
└── return Binary('+', Number(2), Binary('*', Number(3), Number(4)))
```

**Resultado AST correcto:**
```
Binary('+')
├── Number(2)
└── Binary('*')
    ├── Number(3)  
    └── Number(4)
```

**¿Por qué NO hay recursión izquierda?**

1. **Nunca llamamos `parse_bin_level(level)`** - siempre `level + 1`
2. **Siempre avanzamos hacia mayor precedencia** - progreso garantizado  
3. **Usamos iteración (`while`)** para operadores del mismo nivel
4. **El nivel eventualmente llega a `parse_unary()`** - caso base real

**Ventajas sobre transformación clásica:**
- ✅ **Más simple**: Una función vs múltiples reglas
- ✅ **Más eficiente**: O(n) vs O(n log n)  
- ✅ **Más mantenible**: Cambiar precedencia es editar una tabla
- ✅ **Más legible**: El código refleja la intención

---

### **P9: ¿Cómo extenderían su compilador para generar código intermedio?**

**Respuesta:**
Para generar código intermedio agregaríamos una nueva fase:

```python
# Nueva fase: Generación de código intermedio
def generate_ir(ast: Program) -> List[Instruction]:
    instructions = []
    temp_counter = 0
    
    def new_temp():
        nonlocal temp_counter
        temp_counter += 1
        return f"t{temp_counter}"
    
    def visit_binary(node: Binary) -> str:
        left_temp = visit_expr(node.left)
        right_temp = visit_expr(node.right)
        result_temp = new_temp()
        instructions.append(f"{result_temp} = {left_temp} {node.op} {right_temp}")
        return result_temp
    
    def visit_assign(node: Assign) -> str:
        right_temp = visit_expr(node.right)
        if isinstance(node.left, Var):
            instructions.append(f"{node.left.name} = {right_temp}")
        return right_temp
```

**Tipos de código intermedio posibles:**
1. **Código de tres direcciones**: `t1 = a + b`
2. **Bytecode**: Instrucciones de máquina virtual
3. **SSA (Static Single Assignment)**: Cada variable se asigna una sola vez
4. **LLVM IR**: Para usar el backend de LLVM

**Ventajas del código intermedio:**
- Independiente de la máquina target
- Facilita optimizaciones
- Permite múltiples backends
- Debugging más claro

---

### **P10: ¿Cómo optimizarían el AST generado por su parser?**

**Respuesta:**
Implementaríamos optimizaciones en múltiples niveles:

**1. Optimizaciones en el AST:**

```python
def optimize_ast(node):
    # Constant folding
    if isinstance(node, Binary) and isinstance(node.left, Number) and isinstance(node.right, Number):
        if node.op == '+':
            return Number(node.left.value + node.right.value)
        elif node.op == '*':
            return Number(node.left.value * node.right.value)
    
    # Dead code elimination
    if isinstance(node, IfStmt) and isinstance(node.cond, Number):
        if node.cond.value != 0:
            return node.then  # Condición siempre verdadera
        elif node.els:
            return node.els   # Condición siempre falsa
        else:
            return None       # Eliminar if completo
    
    # Strength reduction
    if isinstance(node, Binary) and node.op == '*' and isinstance(node.right, Number):
        if node.right.value == 2:
            return Binary('+', node.left, node.left)  # x * 2 → x + x
```

**2. Optimizaciones de control de flujo:**
- Eliminación de saltos innecesarios
- Fusión de bloques básicos consecutivos
- Eliminación de código unreachable

**3. Optimizaciones de expresiones:**
- Propagación de constantes
- Eliminación de subexpresiones comunes
- Reducción de fuerza (multiplicación → suma)

---

### **P12: ¿Cómo manejarían la concurrencia si quisieran paralelizar el compilador?**

**Respuesta:**

**Análisis de dependencias:**
```
Código fuente → [Lexer] → Tokens → [Parser] → AST → [Semantic] → AST validado
    ↑              ↑          ↑         ↑          ↑
Secuencial    Secuencial  Secuencial  Paralelo   Paralelo
```

**Oportunidades de paralelización:**

1. **Análisis semántico por funciones**:
```python
def parallel_semantic_check(functions: List[FuncDecl]) -> List[str]:
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(check_function, func) for func in functions]
        errors = []
        for future in futures:
            errors.extend(future.result())
    return errors
```

2. **Múltiples archivos fuente**:
```python
def compile_files(files: List[str]) -> Dict[str, AST]:
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(compile_single_file, f): f for f in files}
        results = {}
        for future in futures:
            filename = futures[future]
            results[filename] = future.result()
    return results
```

**Desafíos de concurrencia:**
- **Tabla de símbolos compartida**: Requiere sincronización
- **Dependencias entre módulos**: Límites a la paralelización
- **Orden de errores**: Puede cambiar con paralelización

**Soluciones:**
- **Lock-free data structures** para tabla de símbolos
- **Message passing** en lugar de memoria compartida
- **Fork-join pattern** para análisis independientes

---

### **P13: ¿Cómo implementarían herramientas de desarrollo como autocompletado o refactoring?**

**Respuesta:**

**1. Language Server Protocol (LSP):**
```python
class LanguageServer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.ast_cache = {}
    
    def on_text_changed(self, document_uri: str, text: str):
        # Reparse incrementalmente
        tokens = tokenize(text)
        ast, errors = parse(tokens)
        self.ast_cache[document_uri] = ast
        
        # Análisis semántico en background
        semantic_errors = check(ast)
        self.send_diagnostics(document_uri, errors + semantic_errors)
    
    def provide_completions(self, position: Position) -> List[CompletionItem]:
        # Usar tabla de símbolos para sugerir variables/funciones
        visible_symbols = self.symbol_table.get_visible_at(position)
        return [CompletionItem(sym.name, sym.type) for sym in visible_symbols]
```

**2. Análisis estático avanzado:**
```python
def find_all_references(ast: Program, target_symbol: str) -> List[Position]:
    references = []
    
    class ReferenceVisitor:
        def visit_var(self, node: Var):
            if node.name == target_symbol:
                references.append(node.position)
    
    visitor = ReferenceVisitor()
    visitor.visit(ast)
    return references

def rename_symbol(ast: Program, old_name: str, new_name: str) -> Program:
    # AST transformation para renaming seguro
    transformer = RenameTransformer(old_name, new_name)
    return transformer.transform(ast)
```

**3. Herramientas específicas:**
- **Syntax highlighting**: Basado en tokens del lexer
- **Error squiggles**: Posiciones de errores del parser/semantic analyzer
- **Go to definition**: Usando tabla de símbolos
- **Hover information**: Información de tipos del análisis semántico
- **Code formatting**: Basado en el pretty printer

---

## Preguntas de casos específicos

### **P14: Muestren cómo su parser maneja este código con errores: `int x = y + 1; int y = 5;`**

**Respuesta:**

**Fase 1 - Análisis Léxico**: ✅ Sin problemas
```
[KW_INT] [IDENT:"x"] [ASSIGN] [IDENT:"y"] [PLUS] [NUMBER:1] [SEMI] 
[KW_INT] [IDENT:"y"] [ASSIGN] [NUMBER:5] [SEMI]
```

**Fase 2 - Análisis Sintáctico**: ✅ AST válido
```
Program
├── VarDecl(type=int, name="x", init=Binary(+, Var("y"), Number(1)))
└── VarDecl(type=int, name="y", init=Number(5))
```

**Fase 3 - Análisis Semántico**: ❌ Error semántico
```python
# En check_var_decl():
for vi in d.inits:
    if vi.init:
        init_type = type_of_expr(vi.init)  # Evalúa y + 1
        # En type_of_expr para Binary:
        if isinstance(e, Binary):
            left_type = type_of_expr(e.left)  # type_of_expr(Var("y"))
            # En type_of_expr para Var:
            if isinstance(e, Var):
                sym = lookup(e.name)  # lookup("y") → None
                if sym is None:
                    errors.append(f"'{e.name}' no declarada")  # ← ERROR AQUÍ
```

**Output del compilador:**
```
Error en línea 1, columna 9: 'y' no declarada
Program
├── VarDecl(type=int, name="x", init=Binary(+, Var("y"), Number(1)))
└── VarDecl(type=int, name="y", init=Number(5))
```

**¿Por qué sucede esto?**
- Las declaraciones se procesan secuencialmente
- `y` no existe cuando se evalúa `x = y + 1`
- Nuestro compilador no hace forward declarations automáticas

---

### **P15: ¿Cómo maneja su parser la ambigüedad del "dangling else"?**

**Respuesta:**

**El problema:**
```c
if (a > 0)
    if (b > 0)
        printf("ambos positivos");
else  // ¿A cuál if pertenece?
    printf("a no es positivo");
```

**Posibles interpretaciones:**
```c
// Interpretación 1:
if (a > 0) {
    if (b > 0) {
        printf("ambos positivos");
    } else {
        printf("a no es positivo");  // ← Incorrecto semánticamente
    }
}

// Interpretación 2 (correcta):
if (a > 0) {
    if (b > 0) {
        printf("ambos positivos");
    }
} else {
    printf("a no es positivo");
}
```

**Solución en nuestro parser:**
```python
def parse_stmt() -> Optional[Stmt]:
    if k == TokenKind.KW_IF:
        match(TokenKind.KW_IF)
        expect(TokenKind.LPAREN, "( tras if")
        cond = parse_expr()
        expect(TokenKind.RPAREN, ") tras condición")
        then = parse_stmt()  # ← Recursión que consume el else más cercano
        els = None
        if match(TokenKind.KW_ELSE):  # ← Greedy matching
            els = parse_stmt()
        return IfStmt(cond, then, els)
```

**Regla aplicada**: **Greedy matching** - el `else` se asocia con el `if` más cercano (más interno).

**Resultado**: El parser siempre elige la Interpretación 1, que es el comportamiento estándar en C.

**Para forzar la Interpretación 2**, el programador debe usar llaves:
```c
if (a > 0) {
    if (b > 0)
        printf("ambos positivos");
}
else
    printf("a no es positivo");
```

---

### **P16: Demuestren el parsing completo de esta función recursiva:**

```c
int factorial(int n) {
    if (n <= 1)
        return 1;
    return n * factorial(n - 1);
}
```

**Respuesta:**

**Traza completa del parsing:**

**1. Entrada en parse_declaration():**
```
Token actual: KW_INT
↓
parse_type() → TypeSpec(base="int", ptr_depth=0)
Token actual: IDENT("factorial")
Token siguiente: LPAREN → Es una función
```

**2. Parsing de parámetros:**
```
match(LPAREN) ✅
parse_type() → TypeSpec(base="int", ptr_depth=0)  
Token: IDENT("n") → Parámetro: Param(type=int, name="n")
match(RPAREN) ✅
```

**3. Parsing del cuerpo (parse_compound()):**
```
match(LBRACE) ✅
Tokens en el bloque: KW_IF, KW_RETURN, KW_RETURN, RBRACE
```

**4. Primera sentencia (IfStmt):**
```
parse_stmt() → KW_IF detectado
├── parse_expr() para condición: "n <= 1"
│   └── parse_assign() → parse_bin_level(0)
│       └── Binary(op="<=", left=Var("n"), right=Number(1))
├── parse_stmt() para then: "return 1"
│   └── ReturnStmt(expr=Number(1))
└── else: None (no hay else)
```

**5. Segunda sentencia (ReturnStmt):**
```
parse_stmt() → KW_RETURN detectado
parse_expr(): "n * factorial(n - 1)"
├── parse_assign() → parse_bin_level(0)
├── Izquierda: parse_bin_level(1) → ... → Var("n")
├── Operador: STAR (precedencia 5)  
└── Derecha: parse_bin_level(6) → parse_postfix()
    └── Call(callee=Var("factorial"), args=[Binary("-", Var("n"), Number(1))])
```

**6. AST resultante:**
```
FuncDecl(
    ret_type=TypeSpec(base="int"),
    name="factorial", 
    params=[Param(type=TypeSpec(base="int"), name="n")],
    body=Block([
        IfStmt(
            cond=Binary(op="<=", left=Var("n"), right=Number(1)),
            then=ReturnStmt(expr=Number(1)),
            els=None
        ),
        ReturnStmt(
            expr=Binary(
                op="*",
                left=Var("n"),
                right=Call(
                    callee=Var("factorial"),
                    args=[Binary(op="-", left=Var("n"), right=Number(1))]
                )
            )
        )
    ])
)
```

**Puntos clave demostrados:**
- ✅ Recursión mutua entre `parse_stmt()` y `parse_compound()`
- ✅ Precedencia correcta: `*` antes que `-` en la expresión  
- ✅ Llamada recursiva parseada como `Call` node
- ✅ Estructura anidada del AST reflejando la gramática

---

## Preguntas trampa

### **PT1: "Su parser es LL(1), ¿verdad? Entonces debería poder parsear cualquier gramática libre de contexto..."**

**🚫 TRAMPA**: LL(1) NO puede parsear cualquier gramática libre de contexto.

**✅ RESPUESTA CORRECTA:**
"No, eso es incorrecto. LL(1) es un **subconjunto** de las gramáticas libres de contexto. Específicamente:

- **LL(1) ⊂ LR(1) ⊂ Gramáticas Libres de Contexto**
- LL(1) no puede manejar:
  - Recursión izquierda: `A → A α`
  - Ambigüedades: múltiples derivaciones para la misma entrada
  - Gramáticas que requieren más de 1 token lookahead
  
**Ejemplo de gramática libre de contexto que NO es LL(1):**
```
S → A a | B b
A → ε  
B → ε
```
Con entrada `a`, no sabemos si elegir la primera o segunda producción hasta ver el `a`."

---

### **PT2: "Como usan precedence climbing, su parser NO es realmente LL(1), ¿cierto?"**

**🚫 TRAMPA**: Confundir algoritmo de implementación con clasificación teórica.

**✅ RESPUESTA CORRECTA:**
"Eso es incorrecto. Precedence climbing es una **técnica de implementación** que sigue siendo LL(1):

1. **Sigue siendo LL(1) porque:**
   - Lee de izquierda a derecha ✓
   - Usa derivaciones por la izquierda ✓  
   - Necesita solo 1 token lookahead ✓
   - No hace backtracking ✓

2. **Precedence climbing es equivalente a:**
   ```
   // Gramática LL(1) equivalente (transformada):
   Expr → Term (('+' | '-') Term)*
   Term → Factor (('*' | '/') Factor)*
   Factor → Number | '(' Expr ')'
   ```

3. **Es solo una optimización** que evita crear múltiples funciones de parsing para cada nivel de precedencia."

---

### **PT3: "Si su lexer encuentra un identificador como 'if123', ¿lo tokeniza como IF seguido de 123?"**

**🚫 TRAMPA**: Confundir reglas de tokenización con reconocimiento de palabras clave.

**✅ RESPUESTA CORRECTA:**
"No, eso sería incorrecto. Nuestro lexer usa **maximal munch** (coincidencia máxima):

```python
# En lexer/lexer.py - así funciona realmente:
def tokenize_identifier_or_keyword(text, pos):
    start = pos
    while pos < len(text) and (text[pos].isalnum() or text[pos] == '_'):
        pos += 1  # Consume TODOS los caracteres válidos
    
    lexeme = text[start:pos]  # 'if123' completo
    
    # Verificar si es palabra clave DESPUÉS
    if lexeme in KEYWORDS:  # 'if123' NO está en KEYWORDS
        return Token(KEYWORDS[lexeme], lexeme, ...)
    else:
        return Token(TokenKind.IDENT, lexeme, ...)  # Es un identificador
```

**Resultado:** `'if123'` → `Token(IDENT, 'if123')`, no `Token(IF) + Token(NUMBER)`"

---

### **PT4: "Su análisis semántico detecta que 'x' no está declarada. ¿Por qué no simplemente la declaran automáticamente como 'auto'?"**

**🚫 TRAMPA**: Confundir lenguajes con diferentes reglas de declaración.

**✅ RESPUESTA CORRECTA:**
"Esa sería una decisión de diseño incorrecta para un compilador de C:

1. **C requiere declaraciones explícitas** - es parte de la especificación del lenguaje
2. **Declaración automática introduciría bugs silenciosos:**
   ```c
   int main() {
       int contador = 0;
       // ... 100 líneas después
       contadro = 5;  // Typo - crearía variable nueva en lugar de error
   }
   ```
3. **Nuestro rol es implementar C correctamente**, no inventar un nuevo lenguaje
4. **La detección de errores es una característica**, no un bug a arreglar"

---

### **PT5: "Veo que su parser puede recuperarse de errores. ¿Significa que pueden compilar código con errores sintácticos?"**

**🚫 TRAMPA**: Confundir recuperación de errores con compilación exitosa.

**✅ RESPUESTA CORRECTA:**
"No, la recuperación de errores NO significa compilación exitosa:

**Propósito de la recuperación:**
1. **Reportar múltiples errores** en una sola pasada
2. **Continuar el análisis** para encontrar más problemas  
3. **Mejor experiencia de desarrollo** - ver todos los errores juntos

**Lo que NO hacemos:**
- ❌ Generar código ejecutable con errores
- ❌ Ignorar errores sintácticos
- ❌ 'Adivinar' la intención del programador

**Nuestro comportamiento:**
```python
ast, parse_errs = parse(tokens)
sema_errs = check(ast)
errs = parse_errs + sema_errs
if errs:
    print("\\n".join(errs), file=sys.stderr)  # ← Reportar errores
    # NO generar código si hay errores
```"

---

### **PT6: "Su tabla de símbolos usa una pila. ¿No sería más eficiente usar un hash table plano?"**

**🚫 TRAMPA**: Confundir eficiencia con corrección semántica.

**✅ RESPUESTA CORRECTA:**
"No, un hash table plano sería **funcionalmente incorrecto** para manejar ámbitos:

**El problema con hash table plano:**
```c
int x = 10;        // x = 10 globalmente
void func() {
    int x = 5;     // ¿Cómo distinguir entre las dos 'x'?
    printf("%d", x); // Debe imprimir 5, no 10
}
```

**Por qué necesitamos pila de ámbitos:**
1. **Scoping correcto**: Variables locales ocultan globales
2. **Gestión de memoria**: Variables salen de ámbito automáticamente  
3. **Análisis de visibilidad**: `lookup()` busca desde el ámbito más interno

**Nuestra implementación:**
```python
_scope_stack = [
    {'x': Symbol(type=int, value=10)},  # Ámbito global
    {'x': Symbol(type=int, value=5)}    # Ámbito local (oculta global)
]
```

**Eficiencia real:** O(d) donde d = profundidad de anidamiento (típicamente < 10)"

---

### **PT7: "Su AST tiene nodos como 'Binary' y 'Unary'. ¿No deberían ser más específicos como 'Addition' y 'Multiplication'?"**

**🚫 TRAMPA**: Sobre-especialización innecesaria del AST.

**✅ RESPUESTA CORRECTA:**
"No, nuestro diseño es **intencionalmente genérico** y superior:

**Ventajas de nodos genéricos:**
```python
@dataclass
class Binary:
    op: str      # '+', '-', '*', '/', '<', '==', etc.
    left: Expr
    right: Expr
```

1. **Extensibilidad**: Agregar operadores no requiere nuevos nodos
2. **Consistencia**: Mismo patrón para todos los operadores binarios
3. **Simplicidad**: Menos tipos de nodos que mantener
4. **Polimorfismo**: Mismo código para procesar diferentes operadores

**Si fuéramos específicos necesitaríamos:**
```python
class Addition, class Subtraction, class Multiplication, 
class Division, class LessThan, class GreaterThan, class Equal...
# ¡15+ clases diferentes!
```

**Nuestro enfoque:**
- ✅ **Un nodo genérico** con campo discriminante (`op`)
- ✅ **Fácil extensión** para nuevos operadores  
- ✅ **Pattern matching** simple en el análisis semántico"

---

### **PT8: "He visto que llaman a 'parse_expr()' recursivamente. ¿No es esto recursión izquierda?"**

**🚫 TRAMPA**: Confundir recursión en implementación con recursión izquierda en gramática.

**✅ RESPUESTA CORRECTA:**
"No, hay una diferencia fundamental:

**Recursión izquierda (problemática):**
```
A → A α  // La regla empieza con el mismo no-terminal
```

**Recursión mutua (correcta):**
```python
def parse_primary():
    if match(LPAREN):
        expr = parse_expr()  # ← Recursión mutua, NO izquierda
        expect(RPAREN)
        return expr
```

**¿Por qué NO es recursión izquierda?**

1. **Progreso garantizado**: `match(LPAREN)` consume un token ANTES de la recursión
2. **Caso base claro**: `LPAREN` debe existir para recurrir
3. **Terminación**: Eventualmente se agotan los paréntesis

**Recursión izquierda sería:**
```python
def parse_expr():
    left = parse_expr()  # ← ¡BUCLE INFINITO! No consume tokens
    # ...
```

**La clave:** Siempre consumimos tokens o avanzamos el estado antes de recurrir."

---

### **PT9: "Si su parser es LL(1), ¿por qué necesitan una tabla de precedencia? ¿No debería estar en la gramática?"**

**🚫 TRAMPA**: Confundir implementación optimizada con teoría pura.

**✅ RESPUESTA CORRECTA:**
"Excelente pregunta. La precedencia **ESTÁ** en la gramática, pero implícitamente:

**Gramática teórica equivalente (que generaríamos):**
```
Expr → OrExpr
OrExpr → AndExpr ('||' AndExpr)*
AndExpr → EqExpr ('&&' EqExpr)*  
EqExpr → RelExpr (('==' | '!=') RelExpr)*
RelExpr → AddExpr (('<' | '<=' | '>' | '>=') AddExpr)*
AddExpr → MulExpr (('+' | '-') MulExpr)*
MulExpr → UnaryExpr (('*' | '/' | '%') UnaryExpr)*
```

**Nuestra tabla ES esta gramática compactada:**
```python
_PREC = [
    {TokenKind.OROR},     # OrExpr level
    {TokenKind.ANDAND},   # AndExpr level  
    {TokenKind.EQEQ, TokenKind.NEQ},  # EqExpr level
    # ... etc
]
```

**Ventajas de nuestra implementación:**
- ✅ **Misma semántica** que la gramática explícita
- ✅ **Más concisa**: 6 líneas vs 14 reglas
- ✅ **Más mantenible**: Cambiar precedencia = editar tabla
- ✅ **Mismo comportamiento LL(1)**: 1 token lookahead, no backtracking"

---

### **PT10: "Su lexer ignora comentarios. ¿No deberían preservarlos para herramientas como documentación automática?"**

**🚫 TRAMPA**: Confundir compilador con herramientas de análisis de código.

**✅ RESPUESTA CORRECTA:**
"Depende del **propósito** de la herramienta:

**Para un compilador (nuestro caso):**
- ✅ **Ignorar comentarios es correcto** - no afectan la semántica del programa
- ✅ **Simplifica el parser** - no necesita manejar comentarios en gramática
- ✅ **Estándar en compiladores** - GCC, Clang hacen lo mismo

**Para herramientas de análisis (diferente propósito):**
```python
# Se podría extender para preservar comentarios:
@dataclass  
class CommentToken:
    text: str
    line: int
    is_doc_comment: bool  # /** ... */ vs /* ... */

def tokenize_with_comments(source):
    # Preservar comentarios como tokens especiales
    pass
```

**Separación de responsabilidades:**
- **Compilador**: Generar código ejecutable (ignora comentarios)
- **Documentador**: Extraer documentación (preserva comentarios)  
- **Formatter**: Preservar estilo (mantiene comentarios y whitespace)

**Nuestro enfoque es correcto para el propósito declarado.**"

---
