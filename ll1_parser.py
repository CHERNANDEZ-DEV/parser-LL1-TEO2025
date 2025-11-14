from shutil import get_terminal_size
from c_lexer import tokens, lexer 

def _clip(s: str, w: int) -> str:
    """Recorta s a w columnas, agregando '…' si excede."""
    if s is None:
        s = ""
    if len(s) <= w:
        return s
    if w <= 1:
        return s[:w]
    return s[:max(0, w - 1)] + "…"

def _format_row(buf: str, stack: str, action: str, W):
    """Devuelve una fila alineada con anchos W=(wBuf,wStack,wAction)."""
    b = _clip(buf, W[0]).ljust(W[0])
    s = _clip(stack, W[1]).ljust(W[1])
    a = _clip(action, W[2]).ljust(W[2])
    return f"{b}  {s}  {a}"

# ============================================================
# Tabla LL(1) completa (producciones)
#   Nota: 'vacia' representa ε (epsilon)
# ============================================================

tabla_ll1 = [

# =========================
# 1) S y lista de sentencias
# =========================

# S
['S', 'int',            ['STMT_LIST']],
['S', 'float',          ['STMT_LIST']],
['S', 'double',         ['STMT_LIST']],
['S', 'char',           ['STMT_LIST']],
['S', 'identificador',  ['STMT_LIST']],
['S', 'if',             ['STMT_LIST']],
['S', 'while',          ['STMT_LIST']],
['S', 'for',            ['STMT_LIST']],
['S', 'inicioBloque',   ['STMT_LIST']],
['S', 'finInstruccion', ['STMT_LIST']],
['S', 'finBloque',      ['STMT_LIST']],
['S', 'eof',            ['STMT_LIST']],

# STMT_LIST -> STMT STMT_LIST | ε
['STMT_LIST', 'int',            ['STMT','STMT_LIST']],
['STMT_LIST', 'float',          ['STMT','STMT_LIST']],
['STMT_LIST', 'double',         ['STMT','STMT_LIST']],
['STMT_LIST', 'char',           ['STMT','STMT_LIST']],
['STMT_LIST', 'identificador',  ['STMT','STMT_LIST']],
['STMT_LIST', 'if',             ['STMT','STMT_LIST']],
['STMT_LIST', 'while',          ['STMT','STMT_LIST']],
['STMT_LIST', 'for',            ['STMT','STMT_LIST']],
['STMT_LIST', 'inicioBloque',   ['STMT','STMT_LIST']],
['STMT_LIST', 'finInstruccion', ['STMT','STMT_LIST']],
['STMT_LIST', 'finBloque',      ['vacia']],
['STMT_LIST', 'eof',            ['vacia']],

# =========================
# 2) Sentencias
# =========================

# STMT -> DECL | ASSIGN | IF | WHILE | FOR | BLOCK | EMPTY
['STMT', 'int',            ['DECL']],
['STMT', 'float',          ['DECL']],
['STMT', 'double',         ['DECL']],
['STMT', 'char',           ['DECL']],
['STMT', 'identificador',  ['ASSIGN']],
['STMT', 'if',             ['IF_STMT']],
['STMT', 'while',          ['WHILE_STMT']],
['STMT', 'for',            ['FOR_STMT']],
['STMT', 'inicioBloque',   ['BLOCK']],
['STMT', 'finInstruccion', ['EMPTY']],

# EMPTY -> ;
['EMPTY', 'finInstruccion', ['finInstruccion']],

# =========================
# 3) Declaraciones con inicialización
# =========================

# DECL -> TYPE INIT_LIST ;
['DECL', 'int',    ['TYPE','INIT_LIST','finInstruccion']],
['DECL', 'float',  ['TYPE','INIT_LIST','finInstruccion']],
['DECL', 'double', ['TYPE','INIT_LIST','finInstruccion']],
['DECL', 'char',   ['TYPE','INIT_LIST','finInstruccion']],

# TYPE -> int | float | double | char
['TYPE', 'int',    ['int']],
['TYPE', 'float',  ['float']],
['TYPE', 'double', ['double']],
['TYPE', 'char',   ['char']],

# INIT_LIST -> INIT INIT_TAIL
['INIT_LIST', 'identificador', ['INIT','INIT_TAIL']],

# INIT_TAIL -> , INIT INIT_TAIL | ε
['INIT_TAIL', 'coma',           ['coma','INIT','INIT_TAIL']],
['INIT_TAIL', 'finInstruccion', ['vacia']],

# INIT -> id INIT_OPT
['INIT', 'identificador', ['identificador','INIT_OPT']],

# INIT_OPT -> = EXPR | ε
['INIT_OPT', 'asignacion',     ['asignacion','EXPR']],
['INIT_OPT', 'coma',           ['vacia']],
['INIT_OPT', 'finInstruccion', ['vacia']],

# =========================
# 4) Asignación y bloque
# =========================

# ASSIGN -> ASSIGN_CORE ;
['ASSIGN', 'identificador', ['ASSIGN_CORE','finInstruccion']],

# ASSIGN_CORE -> id = EXPR
['ASSIGN_CORE', 'identificador', ['identificador','asignacion','EXPR']],

# BLOCK -> { STMT_LIST }
['BLOCK', 'inicioBloque', ['inicioBloque','STMT_LIST','finBloque']],

# =========================
# 5) if / while / for
# =========================

# IF_STMT -> if ( EXPR ) STMT IF_TAIL
['IF_STMT', 'if', ['if','LPAREN','EXPR','RPAREN','STMT','IF_TAIL']],

# IF_TAIL -> else STMT | ε
['IF_TAIL', 'else',          ['else','STMT']],
['IF_TAIL', 'int',           ['vacia']],
['IF_TAIL', 'float',         ['vacia']],
['IF_TAIL', 'double',        ['vacia']],
['IF_TAIL', 'char',          ['vacia']],
['IF_TAIL', 'identificador', ['vacia']],
['IF_TAIL', 'if',            ['vacia']],
['IF_TAIL', 'while',         ['vacia']],
['IF_TAIL', 'for',           ['vacia']],
['IF_TAIL', 'inicioBloque',  ['vacia']],
['IF_TAIL', 'finInstruccion',['vacia']],
['IF_TAIL', 'finBloque',     ['vacia']],
['IF_TAIL', 'eof',           ['vacia']],

# WHILE_STMT -> while ( EXPR ) STMT
['WHILE_STMT', 'while', ['while','LPAREN','EXPR','RPAREN','STMT']],

# FOR_STMT -> for ( FOR_INIT ; EXPR_OPT ; POST_OPT ) STMT
['FOR_STMT', 'for', ['for','LPAREN','FOR_INIT','finInstruccion',
                     'EXPR_OPT','finInstruccion','POST_OPT','RPAREN','STMT']],

# FOR_INIT -> DECL_NO_SEMI | ASSIGN_CORE | ε
['FOR_INIT', 'int',          ['DECL_NO_SEMI']],
['FOR_INIT', 'float',        ['DECL_NO_SEMI']],
['FOR_INIT', 'double',       ['DECL_NO_SEMI']],
['FOR_INIT', 'char',         ['DECL_NO_SEMI']],
['FOR_INIT', 'identificador',['ASSIGN_CORE']],
['FOR_INIT', 'finInstruccion',['vacia']],

# DECL_NO_SEMI -> TYPE INIT_LIST
['DECL_NO_SEMI', 'int',    ['TYPE','INIT_LIST']],
['DECL_NO_SEMI', 'float',  ['TYPE','INIT_LIST']],
['DECL_NO_SEMI', 'double', ['TYPE','INIT_LIST']],
['DECL_NO_SEMI', 'char',   ['TYPE','INIT_LIST']],

# EXPR_OPT -> EXPR | ε
['EXPR_OPT', 'LPAREN',        ['EXPR']],
['EXPR_OPT', 'identificador', ['EXPR']],
['EXPR_OPT', 'NUMBER',        ['EXPR']],
['EXPR_OPT', 'cadena',        ['EXPR']],
['EXPR_OPT', 'LOGICAL_NOT',   ['EXPR']],
['EXPR_OPT', 'MINUS',         ['EXPR']],
['EXPR_OPT', 'finInstruccion',['vacia']],

# POST_OPT -> ASSIGN_CORE | ε
['POST_OPT', 'identificador', ['ASSIGN_CORE']],
['POST_OPT', 'RPAREN',        ['vacia']],

# =========================
# 6) Expresiones (precedencia y colas)
# =========================

# EXPR -> OR_EXPR
['EXPR', 'LPAREN',        ['OR_EXPR']],
['EXPR', 'identificador', ['OR_EXPR']],
['EXPR', 'NUMBER',        ['OR_EXPR']],
['EXPR', 'cadena',        ['OR_EXPR']],
['EXPR', 'LOGICAL_NOT',   ['OR_EXPR']],
['EXPR', 'MINUS',         ['OR_EXPR']],

# OR_EXPR -> AND_EXPR OR_EXPR_P
['OR_EXPR', 'LPAREN',        ['AND_EXPR','OR_EXPR_P']],
['OR_EXPR', 'identificador', ['AND_EXPR','OR_EXPR_P']],
['OR_EXPR', 'NUMBER',        ['AND_EXPR','OR_EXPR_P']],
['OR_EXPR', 'cadena',        ['AND_EXPR','OR_EXPR_P']],
['OR_EXPR', 'LOGICAL_NOT',   ['AND_EXPR','OR_EXPR_P']],
['OR_EXPR', 'MINUS',         ['AND_EXPR','OR_EXPR_P']],

# OR_EXPR_P -> LOGICAL_OR AND_EXPR OR_EXPR_P | ε
['OR_EXPR_P', 'LOGICAL_OR',    ['LOGICAL_OR','AND_EXPR','OR_EXPR_P']],
['OR_EXPR_P', 'RPAREN',        ['vacia']],
['OR_EXPR_P', 'finInstruccion',['vacia']],
['OR_EXPR_P', 'coma',          ['vacia']],   # permite coma tras expr (p.ej. int a=1, b)

# AND_EXPR -> REL_EXPR AND_EXPR_P
['AND_EXPR', 'LPAREN',        ['REL_EXPR','AND_EXPR_P']],
['AND_EXPR', 'identificador', ['REL_EXPR','AND_EXPR_P']],
['AND_EXPR', 'NUMBER',        ['REL_EXPR','AND_EXPR_P']],
['AND_EXPR', 'cadena',        ['REL_EXPR','AND_EXPR_P']],
['AND_EXPR', 'LOGICAL_NOT',   ['REL_EXPR','AND_EXPR_P']],
['AND_EXPR', 'MINUS',         ['REL_EXPR','AND_EXPR_P']],

# AND_EXPR_P -> LOGICAL_AND REL_EXPR AND_EXPR_P | ε
['AND_EXPR_P', 'LOGICAL_AND',   ['LOGICAL_AND','REL_EXPR','AND_EXPR_P']],
['AND_EXPR_P', 'LOGICAL_OR',    ['vacia']],
['AND_EXPR_P', 'RPAREN',        ['vacia']],
['AND_EXPR_P', 'finInstruccion',['vacia']],
['AND_EXPR_P', 'coma',          ['vacia']],

# REL_EXPR -> ADD_EXPR REL_TAIL
['REL_EXPR', 'LPAREN',        ['ADD_EXPR','REL_TAIL']],
['REL_EXPR', 'identificador', ['ADD_EXPR','REL_TAIL']],
['REL_EXPR', 'NUMBER',        ['ADD_EXPR','REL_TAIL']],
['REL_EXPR', 'cadena',        ['ADD_EXPR','REL_TAIL']],
['REL_EXPR', 'LOGICAL_NOT',   ['ADD_EXPR','REL_TAIL']],
['REL_EXPR', 'MINUS',         ['ADD_EXPR','REL_TAIL']],

# REL_TAIL -> (==|!=|<|<=|>|>=) ADD_EXPR REL_TAIL | ε
['REL_TAIL', 'EQ',             ['EQ','ADD_EXPR','REL_TAIL']],
['REL_TAIL', 'NE',             ['NE','ADD_EXPR','REL_TAIL']],
['REL_TAIL', 'LT',             ['LT','ADD_EXPR','REL_TAIL']],
['REL_TAIL', 'LE',             ['LE','ADD_EXPR','REL_TAIL']],
['REL_TAIL', 'GT',             ['GT','ADD_EXPR','REL_TAIL']],
['REL_TAIL', 'GE',             ['GE','ADD_EXPR','REL_TAIL']],
['REL_TAIL', 'LOGICAL_AND',    ['vacia']],
['REL_TAIL', 'LOGICAL_OR',     ['vacia']],
['REL_TAIL', 'RPAREN',         ['vacia']],
['REL_TAIL', 'finInstruccion', ['vacia']],
['REL_TAIL', 'coma',           ['vacia']],

# ADD_EXPR -> MUL_EXPR ADD_TAIL
['ADD_EXPR', 'LPAREN',        ['MUL_EXPR','ADD_TAIL']],
['ADD_EXPR', 'identificador', ['MUL_EXPR','ADD_TAIL']],
['ADD_EXPR', 'NUMBER',        ['MUL_EXPR','ADD_TAIL']],
['ADD_EXPR', 'cadena',        ['MUL_EXPR','ADD_TAIL']],
['ADD_EXPR', 'LOGICAL_NOT',   ['MUL_EXPR','ADD_TAIL']],
['ADD_EXPR', 'MINUS',         ['MUL_EXPR','ADD_TAIL']],

# ADD_TAIL -> (+|-) MUL_EXPR ADD_TAIL | ε
['ADD_TAIL', 'PLUS',           ['PLUS','MUL_EXPR','ADD_TAIL']],
['ADD_TAIL', 'MINUS',          ['MINUS','MUL_EXPR','ADD_TAIL']],
['ADD_TAIL', 'EQ',             ['vacia']],
['ADD_TAIL', 'NE',             ['vacia']],
['ADD_TAIL', 'LT',             ['vacia']],
['ADD_TAIL', 'LE',             ['vacia']],
['ADD_TAIL', 'GT',             ['vacia']],
['ADD_TAIL', 'GE',             ['vacia']],
['ADD_TAIL', 'LOGICAL_AND',    ['vacia']],
['ADD_TAIL', 'LOGICAL_OR',     ['vacia']],
['ADD_TAIL', 'RPAREN',         ['vacia']],
['ADD_TAIL', 'finInstruccion', ['vacia']],
['ADD_TAIL', 'coma',           ['vacia']],

# MUL_EXPR -> UNARY MUL_TAIL
['MUL_EXPR', 'LPAREN',        ['UNARY','MUL_TAIL']],
['MUL_EXPR', 'identificador', ['UNARY','MUL_TAIL']],
['MUL_EXPR', 'NUMBER',        ['UNARY','MUL_TAIL']],
['MUL_EXPR', 'cadena',        ['UNARY','MUL_TAIL']],
['MUL_EXPR', 'LOGICAL_NOT',   ['UNARY','MUL_TAIL']],
['MUL_EXPR', 'MINUS',         ['UNARY','MUL_TAIL']],

# MUL_TAIL -> (*|/) UNARY MUL_TAIL | ε
['MUL_TAIL', 'TIMES',          ['TIMES','UNARY','MUL_TAIL']],
['MUL_TAIL', 'DIVIDE',         ['DIVIDE','UNARY','MUL_TAIL']],
['MUL_TAIL', 'PLUS',           ['vacia']],
['MUL_TAIL', 'MINUS',          ['vacia']],
['MUL_TAIL', 'EQ',             ['vacia']],
['MUL_TAIL', 'NE',             ['vacia']],
['MUL_TAIL', 'LT',             ['vacia']],
['MUL_TAIL', 'LE',             ['vacia']],
['MUL_TAIL', 'GT',             ['vacia']],
['MUL_TAIL', 'GE',             ['vacia']],
['MUL_TAIL', 'LOGICAL_AND',    ['vacia']],
['MUL_TAIL', 'LOGICAL_OR',     ['vacia']],
['MUL_TAIL', 'RPAREN',         ['vacia']],
['MUL_TAIL', 'finInstruccion', ['vacia']],
['MUL_TAIL', 'coma',           ['vacia']],

# UNARY -> ! UNARY | - UNARY | PRIMARY
['UNARY', 'LOGICAL_NOT',   ['LOGICAL_NOT','UNARY']],
['UNARY', 'MINUS',         ['MINUS','UNARY']],
['UNARY', 'LPAREN',        ['PRIMARY']],
['UNARY', 'identificador', ['PRIMARY']],
['UNARY', 'NUMBER',        ['PRIMARY']],
['UNARY', 'cadena',        ['PRIMARY']],

# PRIMARY -> ( EXPR ) | id | NUMBER | cadena
['PRIMARY', 'LPAREN',        ['LPAREN','EXPR','RPAREN']],
['PRIMARY', 'identificador', ['identificador']],
['PRIMARY', 'NUMBER',        ['NUMBER']],
['PRIMARY', 'cadena',        ['cadena']],
]

# ============================================================
# Índice de acceso rápido a la tabla (A,a) -> producción
# ============================================================

_indice = {(A, a): prod for (A, a, prod) in tabla_ll1}

def _buscar_en_tabla(no_terminal, terminal):
    return _indice.get((no_terminal, terminal))

def _agregar_pila(stack, produccion):
    for simbolo in reversed(produccion):
        if simbolo != 'vacia':
            stack.append(simbolo)

def _tokenizar(codigo: str):
    """Tokeniza con el lexer PLY; asegura 'eof' al final."""
    lexer.lineno = 1
    lexer.input(codigo)
    out = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        out.append(tok)
    if not out or out[-1].type != 'eof':
        class _E: pass
        e = _E(); e.type = 'eof'; e.value = None; e.lexpos = -1
        out.append(e)
    return out

def parse(codigo: str, trazar: bool = True, widths: tuple[int,int,int] | None = None) -> bool:
    tokens_stream = _tokenizar(codigo)
    stack = ['eof', 'S']        # tope = último elemento
    i = 0

    if widths is None:
        total = max(get_terminal_size((140, 40)).columns - 4, 100)
        W = (int(total * 0.30), int(total * 0.50), total - int(total * 0.30) - int(total * 0.50))
        W = (max(W[0], 28), max(W[1], 50), max(W[2], 22))
    else:
        W = widths

    def show_stack() -> str:
        return ' '.join(stack)

    def look() -> str:
        return tokens_stream[i].type

    if trazar:
        print(_format_row("Buffer", "Stack", "Acción", W))
        print(_format_row("-" * 6, "-" * 5, "-" * 6, W))

    while True:
        a = look()
        X = stack[-1]

        # Aceptación
        if X == a == 'eof':
            if trazar:
                print(_format_row(a, show_stack(), "Aceptar", W))
            return True

        # Caso: X es terminal
        if X in tokens:
            if X == a:
                if trazar:
                    print(_format_row(a, show_stack(), f"match {X}", W))
                stack.pop()
                i += 1
            else:
                if trazar:
                    print(_format_row(a, show_stack(), f"[ERR] esperado {X}", W))
                return False
            continue

        # Caso: X es No Terminal
        produccion = _buscar_en_tabla(X, a)
        if produccion is None:
            if trazar:
                print(_format_row(a, show_stack(), f"[ERR] M[{X}][{a}] vacío", W))
            return False

        rhs = 'ε' if produccion == ['vacia'] else ' '.join(produccion)
        if trazar:
            print(_format_row(a, show_stack(), f"{X} -> {rhs}", W))

        stack.pop()
        _agregar_pila(stack, produccion)
