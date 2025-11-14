import ply.lex as lex

tokens = (
    # literales / operadores / delimitadores
    'NUMBER',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    'LPAREN', 'RPAREN',
    'inicioBloque', 'finBloque',
    'finInstruccion', 'asignacion',
    'coma', 'cadena',
    'comentario', 'comentario_bloque',
    'identificador',
    'eof',

    # Palabras reservadas (sin 'return')
    'int', 'float', 'double', 'char', 'void',
    'if', 'else', 'while', 'for',

    # Comparación
    'EQ', 'NE', 'LE', 'GE', 'LT', 'GT',

    # Lógicos
    'LOGICAL_AND', 'LOGICAL_OR', 'LOGICAL_NOT',
)

# ===== Palabras reservadas =====
def t_int(t):     r'int';     return t
def t_float(t):   r'float';   return t
def t_double(t):  r'double';  return t
def t_char(t):    r'char';    return t
def t_void(t):    r'void';    return t  # reservada; la gramática no la usa como TYPE
def t_if(t):      r'if';      return t
def t_else(t):    r'else';    return t
def t_while(t):   r'while';   return t
def t_for(t):     r'for';     return t

# ===== Operadores multi-caracter (antes que 1-char) =====
t_EQ          = r'=='
t_NE          = r'!='
t_LE          = r'<='
t_GE          = r'>='
t_LOGICAL_AND = r'&&'
t_LOGICAL_OR  = r'\|\|'

# ===== Comentarios =====
def t_comentario_bloque(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')
    pass  # no retornamos token

def t_comentario(t):
    r'//.*'
    pass

# ===== Operadores 1 char y delimitadores =====
t_PLUS           = r'\+'
t_MINUS          = r'-'
t_TIMES          = r'\*'
t_DIVIDE         = r'/'
t_LPAREN         = r'\('
t_RPAREN         = r'\)'
t_inicioBloque   = r'\{'
t_finBloque      = r'\}'
t_finInstruccion = r';'
t_asignacion     = r'='      # después de '=='
t_LT             = r'<'      # después de '<='
t_GT             = r'>'      # después de '>='
t_LOGICAL_NOT    = r'!'      # después de '!='
t_coma           = r','
t_eof            = r'\$'

# ===== Literales y otros =====
def t_NUMBER(t):
    r'\d+'
    try: t.value = int(t.value)
    except ValueError: t.value = 0
    return t

def t_cadena(t):
    r'\"([^\\\"]|\\.)*\"'
    return t

def t_identificador(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    return t

# ===== Control de líneas / espacios / errores =====
t_ignore = ' \t\r'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"[LEX] Illegal character '{t.value[0]}' at pos {t.lexpos}")
    t.lexer.skip(1)

lexer = lex.lex()



