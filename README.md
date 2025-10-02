# Proyecto: Analizador léxico y sintáctico (descendente recursivo/LL(1)) para un subset de C

> Se incluyen: (1) especificación de tokens y regex, (2) EBNF y su transformación a BNF/CFG, (3) código del lexer y parser con recuperación de errores, (4) AST con nodos tipados, (5) pruebas unitarias, (6) diagrama/flujo del pipeline, (7) instrucciones de ejecución.

---

## 1) Estructura del proyecto

```
c-subset-parser/
├─ README.md  (este documento)
├─ cli.py
├─ lexer/
│  ├─ __init__.py
│  ├─ tokens.py
│  └─ lexer.py
├─ parser/
│  ├─ __init__.py
│  ├─ errors.py
│  └─ parser.py
├─ ast/
│  ├─ __init__.py
│  ├─ nodes.py
│  └─ pretty.py
└─ tests/
   ├─ test_lexer.py
   ├─ test_parser_ok.py
   └─ test_parser_error.py
```

---

## 1) Especificación de **tokens** y **regex**

### Palabras clave

```
int | char | float | double | void | if | else | while | for | return
```

### Identificadores

Regex: `[A-Za-z_][A-Za-z0-9_]*`

### Literales numéricos (simplificados)

* Enteros (decimales): `(?:0|[1-9][0-9]*)`
* Flotantes (simplificados): `(?:[0-9]*\.[0-9]+|[0-9]+\.)` con opcional exponente `(?:[eE][+-]?[0-9]+)?`
* Tokenización: detectar **float** antes de **int** para evitar conflictos.

### Espacios y saltos

* `\s+` (incluye `\n`) → se ignoran pero se **cuenta** línea/columna.

### Comentarios

* Línea: `//.*?(?=\n|$)`
* Bloque: `/\*.*?\*/` con `re.DOTALL` (no anidados).

### Operadores y separadores

* Unarios: `+ - ! ~ & *` (también usados binariamente según contexto)
* Binarios: `* / % + - < <= > >= == != && ||`
* Asignación: `=`
* Paréntesis/brackets/braces: `(` `)` `[` `]` `{` `}`
* Otros: `,` `;`

**Regla práctica**: reconocer tokens multi-caracter primero (`<= >= == != && || /* */ //`) y luego los de un carácter.

### Conjunto de tipos básicos

```
int, char, float, double, void
```

---

## 2) Gramática en **EBNF** y transformación a **BNF/CFG** apta para parser

> Soporta: declaraciones de variables y funciones, llamadas, indexación, `if/else`, `while`, `for`, `return`, bloques `{...}`; sin typedef complejo, sin varargs, sin ternario, sin struct/union/enum avanzados.

### 2.1 EBNF (legible)

```
TranslationUnit   := { Declaration } ;

Declaration       := TypeSpec ( FunctionDecl | VarDecl ) ;
TypeSpec          := ("int"|"char"|"float"|"double"|"void") { "*" } ;   (* puntero simple por multiplicidad de * )

FunctionDecl      := Ident "(" [ ParamList ] ")" CompoundStmt ;
ParamList         := Param { "," Param } ;
Param             := TypeSpec Ident [ ArraySuffix ] ;
VarDecl           := InitDeclarator { "," InitDeclarator } ";" ;
InitDeclarator    := Ident [ ArraySuffix ] [ "=" Expr ] ;
ArraySuffix       := "[" [ ConstExpr ] "]" ;

CompoundStmt      := "{" { Declaration | Stmt } "}" ;
Stmt              := ExprStmt | IfStmt | WhileStmt | ForStmt | ReturnStmt | CompoundStmt ;
ExprStmt          := [ Expr ] ";" ;
IfStmt            := "if" "(" Expr ")" Stmt [ "else" Stmt ] ;
WhileStmt         := "while" "(" Expr ")" Stmt ;
ForStmt           := "for" "(" [ExprStmt] [Expr] ";" [Expr] ")" Stmt ;
ReturnStmt        := "return" [ Expr ] ";" ;

(* Expresiones - precedencia (baja→alta): ||, &&, == !=, < <= > >=, + -, * / %, unarios, primarios *)
Expr              := Assign ;
Assign            := LogicOr [ "=" Assign ] ;
LogicOr           := LogicAnd { "||" LogicAnd } ;
LogicAnd          := Equality { "&&" Equality } ;
Equality          := Relational { ("=="|"!=") Relational } ;
Relational        := Additive { ("<"|"<="|">"|">=") Additive } ;
Additive          := Multiplicative { ("+"|"-") Multiplicative } ;
Multiplicative    := Unary { ("*"|"/"|"%") Unary } ;
Unary             := ("+"|"-"|"!"|"~"|"&"|"*") Unary | Postfix ;
Postfix           := Primary { PostfixTail } ;
PostfixTail       := "(" [ ArgList ] ")" | "[" Expr "]" ;
ArgList           := Expr { "," Expr } ;
Primary           := Ident | Number | "(" Expr ")" ;
ConstExpr         := Number ; (* simplificación *)
```

### 2.2 Transformación a BNF/CFG (sin EBNF, sin recursión por la izquierda)

```
TranslationUnit → Declaration TranslationUnit | ε

Declaration → TypeSpec DeclTail
DeclTail    → FunctionDecl | VarDecl

TypeSpec    → BaseType PtrStars
BaseType    → int | char | float | double | void
PtrStars    → * PtrStars | ε

FunctionDecl → Ident ( OptParamList ) CompoundStmt
OptParamList → ParamList | ε
ParamList   → Param ParamListTail
ParamListTail → , Param ParamListTail | ε
Param       → TypeSpec Ident OptArraySuffix
OptArraySuffix → ArraySuffix | ε

VarDecl     → InitDeclarator VarDeclTail ;
VarDeclTail → , InitDeclarator VarDeclTail | ε
InitDeclarator → Ident OptArraySuffix OptInit
OptInit     → = Expr | ε
ArraySuffix → [ OptConstExpr ]
OptConstExpr → ConstExpr | ε
ConstExpr   → Number

CompoundStmt → { CompoundItems }
CompoundItems → CompoundItem CompoundItems | ε
CompoundItem → Declaration | Stmt

Stmt → ExprStmt | IfStmt | WhileStmt | ForStmt | ReturnStmt | CompoundStmt
ExprStmt → OptExpr ;
OptExpr  → Expr | ε
IfStmt   → if ( Expr ) Stmt OptElse
OptElse  → else Stmt | ε
WhileStmt → while ( Expr ) Stmt
ForStmt → for ( ForInit ForCond ; ForIter ) Stmt
ForInit → ExprStmt | ;
ForCond → OptExpr
ForIter → OptExpr
ReturnStmt → return OptExpr ;

Expr → Assign
Assign → LogicOr AssignTail
AssignTail → = Assign | ε
LogicOr → LogicAnd LogicOrTail
LogicOrTail → || LogicAnd LogicOrTail | ε
LogicAnd → Equality LogicAndTail
LogicAndTail → && Equality LogicAndTail | ε
Equality → Relational EqualityTail
EqualityTail → (== | !=) Relational EqualityTail | ε
Relational → Additive RelationalTail
RelationalTail → (< | <= | > | >=) Additive RelationalTail | ε
Additive → Multiplicative AdditiveTail
AdditiveTail → (+ | -) Multiplicative AdditiveTail | ε
Multiplicative → Unary MultiplicativeTail
MultiplicativeTail → (* | / | %) Unary MultiplicativeTail | ε
Unary → (+ | - | ! | ~ | & | *) Unary | Postfix
Postfix → Primary PostfixTailOpt
PostfixTailOpt → PostfixTail PostfixTailOpt | ε
PostfixTail → ( OptArgList ) | [ Expr ]
OptArgList → ArgList | ε
ArgList → Expr ArgListTail
ArgListTail → , Expr ArgListTail | ε
Primary → Ident | Number | ( Expr )
```

---

## 3) Código del **lexer** (funcional, con posiciones y comentarios)

### `lexer/tokens.py`

```python
# -*- coding: utf-8 -*-
from __future__ import annotations
from enum import Enum, auto
from typing import NamedTuple, Optional, Union

class TokenKind(Enum):
    # Palabras clave
    KW_INT = auto(); KW_CHAR = auto(); KW_FLOAT = auto(); KW_DOUBLE = auto(); KW_VOID = auto()
    KW_IF = auto(); KW_ELSE = auto(); KW_WHILE = auto(); KW_FOR = auto(); KW_RETURN = auto()

    # Identificadores y números
    IDENT = auto(); NUMBER_INT = auto(); NUMBER_FLOAT = auto()

    # Operadores
    PLUS = auto(); MINUS = auto(); STAR = auto(); SLASH = auto(); PERCENT = auto()
    LT = auto(); LE = auto(); GT = auto(); GE = auto(); EQEQ = auto(); NEQ = auto()
    ANDAND = auto(); OROR = auto(); ASSIGN = auto(); BANG = auto(); TILDE = auto(); AMP = auto()

    # Delimitadores
    LPAREN = auto(); RPAREN = auto(); LBRACE = auto(); RBRACE = auto(); LBRACKET = auto(); RBRACKET = auto()
    COMMA = auto(); SEMI = auto()

    # Fin de archivo y desconocido
    EOF = auto(); INVALID = auto()

KEYWORDS = {
    'int': TokenKind.KW_INT, 'char': TokenKind.KW_CHAR, 'float': TokenKind.KW_FLOAT,
    'double': TokenKind.KW_DOUBLE, 'void': TokenKind.KW_VOID,
    'if': TokenKind.KW_IF, 'else': TokenKind.KW_ELSE, 'while': TokenKind.KW_WHILE,
    'for': TokenKind.KW_FOR, 'return': TokenKind.KW_RETURN,
}

class Token(NamedTuple):
    kind: TokenKind
    lexeme: str
    line: int
    col: int
    value: Optional[Union[int, float, str]] = None
```

### `lexer/lexer.py`

```python
# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from typing import List, Iterable
from .tokens import Token, TokenKind, KEYWORDS

# Orden importa: patrones multi-caracter primero
_TOKEN_SPEC = [
    (TokenKind.LE, r"<="),
    (TokenKind.GE, r">="),
    (TokenKind.EQEQ, r"=="),
    (TokenKind.NEQ, r"!="),
    (TokenKind.ANDAND, r"&&"),
    (TokenKind.OROR, r"\|\|"),
    # comentarios
    (None, r"//[^\n]*"),
    (None, r"/\*.*?\*/"),
    # operadores y delimitadores de un char
    (TokenKind.LPAREN, r"\("), (TokenKind.RPAREN, r"\)"),
    (TokenKind.LBRACE, r"\{"), (TokenKind.RBRACE, r"\}"),
    (TokenKind.LBRACKET, r"\["), (TokenKind.RBRACKET, r"\]"),
    (TokenKind.COMMA, r","), (TokenKind.SEMI, r";"),
    (TokenKind.PLUS, r"\+"), (TokenKind.MINUS, r"-"), (TokenKind.STAR, r"\*"),
    (TokenKind.SLASH, r"/"), (TokenKind.PERCENT, r"%"),
    (TokenKind.LT, r"<"), (TokenKind.GT, r">"), (TokenKind.ASSIGN, r"="),
    (TokenKind.BANG, r"!"), (TokenKind.TILDE, r"~"), (TokenKind.AMP, r"&"),
]

_WS_RE = re.compile(r"\s+", re.MULTILINE)
_ID_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_FLOAT_RE = re.compile(r"(?:[0-9]*\.[0-9]+|[0-9]+\.)(?:[eE][+-]?[0-9]+)?")
_INT_RE = re.compile(r"(?:0|[1-9][0-9]*)")

def tokenize(src: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    line = 1
    col = 1
    n = len(src)

    def emit(kind: TokenKind, lexeme: str, value=None):
        nonlocal tokens, line, col
        tokens.append(Token(kind, lexeme, line, col, value))

    while i < n:
        # espacios
        m = _WS_RE.match(src, i)
        if m:
            txt = m.group(0)
            # actualiza linea/col
            lines = txt.split('\n')
            if len(lines) > 1:
                line += len(lines) - 1
                col = len(lines[-1]) + 1
            else:
                col += len(txt)
            i = m.end()
            continue

        # comentarios (manejo manual para contar columnas/lineas)
        if src.startswith('//', i):
            j = src.find('\n', i)
            if j == -1:
                # consume hasta EOF
                col += (n - i)
                i = n
            else:
                col = 1
                line += 1
                i = j + 1
            continue
        if src.startswith('/*', i):
            j = src.find('*/', i+2)
            if j == -1:
                # comentario no cerrado → error léxico suave: consumimos hasta EOF
                j = n - 2
            chunk = src[i:j+2]
            lines = chunk.split('\n')
            if len(lines) > 1:
                line += len(lines) - 1
                col = len(lines[-1]) + 1
            else:
                col += len(chunk)
            i = j + 2
            continue

        # identificador/keyword
        m = _ID_RE.match(src, i)
        if m:
            lex = m.group(0)
            kind = KEYWORDS.get(lex, TokenKind.IDENT)
            emit(kind, lex, lex)
            i = m.end()
            col += len(lex)
            continue

        # números: float antes que int
        m = _FLOAT_RE.match(src, i)
        if m:
            lex = m.group(0)
            emit(TokenKind.NUMBER_FLOAT, lex, float(lex))
            i = m.end(); col += len(lex); continue
        m = _INT_RE.match(src, i)
        if m:
            lex = m.group(0)
            emit(TokenKind.NUMBER_INT, lex, int(lex))
            i = m.end(); col += len(lex); continue

        # operadores/delimitadores
        matched = False
        for kind, pat in _TOKEN_SPEC:
            if kind is None:
                continue
            if re.match(pat, src[i:]):
                lex = re.match(pat, src[i:]).group(0)
                emit(kind, lex, lex)
                i += len(lex)
                col += len(lex)
                matched = True
                break
        if matched:
            continue

        # carácter inesperado → token INVALID y avanzar 1
        emit(TokenKind.INVALID, src[i], src[i])
        i += 1
        col += 1

    tokens.append(Token(TokenKind.EOF, "<eof>", line, col))
    return tokens
```

---

## 4) Código del **parser** (descendente recursivo + recuperación de errores) y **AST**

### Diseño

* **Expresiones**: algoritmo de precedencia (precedence climbing) para mantener el código simple y eficiente.
* **Recuperación**: modo **panic** con conjuntos de sincronización por producción (p. ej., `;`, `}`, `)`, `]`). Al error, se reporta con `(línea:columna)` y se avanza hasta un token “seguro”.
* **Estructurado**: todo como funciones; estados en variables y tuplas; sin clases.

### `ast/nodes.py`

```python
# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Union

# Tipos
@dataclass
class TypeSpec:
    base: str          # 'int' | 'char' | 'float' | 'double' | 'void'
    ptr_depth: int = 0 # número de '*'

@dataclass
class ArrayType:
    elem: TypeSpec
    size: Optional[int]  # None si [] sin tamaño (p.ej. en params)

# Nodos del AST
@dataclass
class Program:
    decls: List["Decl"]

Decl = Union["FuncDecl", "VarDecl"]

@dataclass
class Param:
    type: TypeSpec
    name: str
    array: Optional[ArrayType] = None

@dataclass
class FuncDecl:
    ret_type: TypeSpec
    name: str
    params: List[Param]
    body: "Block"

@dataclass
class VarInit:
    name: str
    array: Optional[ArrayType]
    init: Optional["Expr"]

@dataclass
class VarDecl:
    type: TypeSpec
    inits: List[VarInit]  # múltiples declaradores separados por comas

@dataclass
class Block:
    items: List[Union["Stmt", Decl]]

# Sentencias
@dataclass
class IfStmt:
    cond: "Expr"
    then: "Stmt"
    els: Optional["Stmt"]

@dataclass
class WhileStmt:
    cond: "Expr"
    body: "Stmt"

@dataclass
class ForStmt:
    init: Optional["Expr"]
    cond: Optional["Expr"]
    it: Optional["Expr"]
    body: "Stmt"

@dataclass
class ReturnStmt:
    expr: Optional["Expr"]

@dataclass
class ExprStmt:
    expr: Optional["Expr"]

Stmt = Union[Block, IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt]

# Expresiones
@dataclass
class Assign:
    left: "Expr"  # normalmente un LValue: Var/Index
    right: "Expr"

@dataclass
class Binary:
    op: str
    left: "Expr"
    right: "Expr"

@dataclass
class Unary:
    op: str
    expr: "Expr"

@dataclass
class Call:
    callee: "Expr"
    args: List["Expr"]

@dataclass
class Index:
    array: "Expr"
    index: "Expr"

@dataclass
class Var:
    name: str

@dataclass
class Number:
    value: Union[int, float]

Expr = Union[Assign, Binary, Unary, Call, Index, Var, Number]
```

### `parser/errors.py`

```python
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List

class ParseError(Exception):
    pass

def report(errors: List[str], line: int, col: int, msg: str) -> None:
    errors.append(f"[{line}:{col}] Error de sintaxis: {msg}")
```

### `parser/parser.py`

```python
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Tuple, Optional
from lexer.tokens import Token, TokenKind
from ast.nodes import *
from .errors import report, ParseError

# Utilidades del parser (funciones, no clases)

def _is_type_kw(k: TokenKind) -> bool:
    return k in {TokenKind.KW_INT, TokenKind.KW_CHAR, TokenKind.KW_FLOAT, TokenKind.KW_DOUBLE, TokenKind.KW_VOID}

# Precedencias (menor índice = menor precedencia)
_PREC = [
    {TokenKind.OROR},
    {TokenKind.ANDAND},
    {TokenKind.EQEQ, TokenKind.NEQ},
    {TokenKind.LT, TokenKind.LE, TokenKind.GT, TokenKind.GE},
    {TokenKind.PLUS, TokenKind.MINUS},
    {TokenKind.STAR, TokenKind.SLASH, TokenKind.PERCENT},
]

_BIN_OP_STR = {
    TokenKind.OROR: '||', TokenKind.ANDAND: '&&',
    TokenKind.EQEQ: '==', TokenKind.NEQ: '!=',
    TokenKind.LT: '<', TokenKind.LE: '<=', TokenKind.GT: '>', TokenKind.GE: '>=',
    TokenKind.PLUS: '+', TokenKind.MINUS: '-',
    TokenKind.STAR: '*', TokenKind.SLASH: '/', TokenKind.PERCENT: '%',
}

_UNARY_SET = {TokenKind.PLUS, TokenKind.MINUS, TokenKind.BANG, TokenKind.TILDE, TokenKind.AMP, TokenKind.STAR}

# ------------- Núcleo del parser -------------

def parse(tokens: List[Token]) -> Tuple[Program, List[str]]:
    i = 0
    errors: List[str] = []

    def peek() -> Token:
        return tokens[min(len(tokens)-1, i)]

    def match(kind: TokenKind) -> bool:
        nonlocal i
        if tokens[i].kind == kind:
            i += 1
            return True
        return False

    def expect(kind: TokenKind, msg: str):
        nonlocal i
        if tokens[i].kind == kind:
            i += 1
            return tokens[i-1]
        t = tokens[i]
        report(errors, t.line, t.col, msg + f"; se encontró '{t.lexeme}'")
        raise ParseError()

    def synchronize(sync_kinds: set[TokenKind]):
        nonlocal i
        # avanzar hasta un token seguro o fin
        while tokens[i].kind not in sync_kinds and tokens[i].kind != TokenKind.EOF:
            i += 1

    # ---------- Parsing de tipos ----------
    def parse_type() -> TypeSpec:
        t = peek()
        if not _is_type_kw(t.kind):
            report(errors, t.line, t.col, "Se esperaba especificador de tipo")
            raise ParseError()
        base = t.lexeme
        match(t.kind)
        ptr_depth = 0
        while match(TokenKind.STAR):
            ptr_depth += 1
        return TypeSpec(base=base, ptr_depth=ptr_depth)

    def opt_array_suffix() -> Optional[ArrayType]:
        if match(TokenKind.LBRACKET):
            if tokens[i].kind in (TokenKind.NUMBER_INT,):
                size = tokens[i].value
                i_plus = i
                match(TokenKind.NUMBER_INT)
            else:
                size = None
            try:
                expect(TokenKind.RBRACKET, "] esperado")
            except ParseError:
                synchronize({TokenKind.SEMI, TokenKind.COMMA, TokenKind.RPAREN, TokenKind.RBRACKET})
            elem = None  # se completará arriba con el TypeSpec
            return ArrayType(elem=None, size=size)
        return None

    # ---------- Declarations ----------
    def parse_declaration() -> Optional[Decl]:
        t0 = peek()
        try:
            ts = parse_type()
        except ParseError:
            synchronize({TokenKind.SEMI, TokenKind.RBRACE})
            if match(TokenKind.SEMI):
                return None
            return None

        # Mirar siguiente: Ident obligatorio
        if tokens[i].kind != TokenKind.IDENT:
            report(errors, tokens[i].line, tokens[i].col, "Se esperaba identificador tras el tipo")
            synchronize({TokenKind.SEMI, TokenKind.RBRACE})
            if match(TokenKind.SEMI):
                return VarDecl(type=ts, inits=[])
            return None
        name_tok = tokens[i]; match(TokenKind.IDENT)

        # ¿función o variable?
        if match(TokenKind.LPAREN):
            # función
            params: List[Param] = []
            if not match(TokenKind.RPAREN):
                while True:
                    ptype = parse_type()
                    if tokens[i].kind != TokenKind.IDENT:
                        report(errors, tokens[i].line, tokens[i].col, "Se esperaba nombre de parámetro")
                        raise ParseError()
                    pname = tokens[i].lexeme; match(TokenKind.IDENT)
                    arr = None
                    if tokens[i].kind == TokenKind.LBRACKET:
                        arr = opt_array_suffix()
                    params.append(Param(ptype, pname, arr))
                    if match(TokenKind.COMMA):
                        continue
                    expect(TokenKind.RPAREN, ") esperado en parámetros")
                    break
            body = parse_compound()
            return FuncDecl(ret_type=ts, name=name_tok.lexeme, params=params, body=body)
        else:
            # variable / lista de inicializadores
            inits: List[VarInit] = []
            # primer declarador ya tiene name_tok
            arr = None
            if tokens[i].kind == TokenKind.LBRACKET:
                arr = opt_array_suffix()
            init_expr = None
            if match(TokenKind.ASSIGN):
                init_expr = parse_expr()
            inits.append(VarInit(name=name_tok.lexeme, array=arr, init=init_expr))
            while match(TokenKind.COMMA):
                if tokens[i].kind != TokenKind.IDENT:
                    report(errors, tokens[i].line, tokens[i].col, "Se esperaba identificador en declarador")
                    break
                nm = tokens[i].lexeme; match(TokenKind.IDENT)
                arr2 = None
                if tokens[i].kind == TokenKind.LBRACKET:
                    arr2 = opt_array_suffix()
                init2 = None
                if match(TokenKind.ASSIGN):
                    init2 = parse_expr()
                inits.append(VarInit(name=nm, array=arr2, init=init2))
            try:
                expect(TokenKind.SEMI, "; esperado tras declaración de variable")
            except ParseError:
                synchronize({TokenKind.SEMI, TokenKind.RBRACE})
                match(TokenKind.SEMI)
            # completa elem de arrays al final
            for vi in inits:
                if vi.array is not None and vi.array.elem is None:
                    vi.array.elem = ts
            return VarDecl(type=ts, inits=inits)

    # ---------- Compound y statements ----------
    def parse_compound() -> Block:
        try:
            expect(TokenKind.LBRACE, "{ esperado")
        except ParseError:
            synchronize({TokenKind.LBRACE})
            match(TokenKind.LBRACE)
        items: List[Union[Stmt, Decl]] = []
        while tokens[i].kind not in {TokenKind.RBRACE, TokenKind.EOF}:
            if _is_type_kw(tokens[i].kind):
                d = parse_declaration()
                if d is not None:
                    items.append(d)
            else:
                s = parse_stmt()
                if s is not None:
                    items.append(s)
        try:
            expect(TokenKind.RBRACE, "} esperado")
        except ParseError:
            pass
        return Block(items)

    def parse_stmt() -> Optional[Stmt]:
        k = tokens[i].kind
        if k == TokenKind.KW_IF:
            match(TokenKind.KW_IF)
            expect(TokenKind.LPAREN, "( esperado tras if")
            cond = parse_expr()
            expect(TokenKind.RPAREN, ") esperado tras condición")
            then = parse_stmt()
            els = None
            if match(TokenKind.KW_ELSE):
                els = parse_stmt()
            return IfStmt(cond, then, els)
        elif k == TokenKind.KW_WHILE:
            match(TokenKind.KW_WHILE)
            expect(TokenKind.LPAREN, "( esperado tras while")
            cond = parse_expr()
            expect(TokenKind.RPAREN, ") esperado")
            body = parse_stmt()
            return WhileStmt(cond, body)
        elif k == TokenKind.KW_FOR:
            match(TokenKind.KW_FOR)
            expect(TokenKind.LPAREN, "( esperado tras for")
            # init (ExprStmt o ;)
            if tokens[i].kind == TokenKind.SEMI:
                match(TokenKind.SEMI)
                init = None
            else:
                init = parse_expr()
                expect(TokenKind.SEMI, "; en for-init")
            # cond
            cond = None if tokens[i].kind == TokenKind.SEMI else parse_expr()
            expect(TokenKind.SEMI, "; en for-cond")
            # iter
            it = None if tokens[i].kind == TokenKind.RPAREN else parse_expr()
            expect(TokenKind.RPAREN, ") en for")
            body = parse_stmt()
            return ForStmt(init, cond, it, body)
        elif k == TokenKind.KW_RETURN:
            match(TokenKind.KW_RETURN)
            expr = None if tokens[i].kind == TokenKind.SEMI else parse_expr()
            expect(TokenKind.SEMI, "; tras return")
            return ReturnStmt(expr)
        elif k == TokenKind.LBRACE:
            return parse_compound()
        else:
            # ExprStmt
            if tokens[i].kind == TokenKind.SEMI:
                match(TokenKind.SEMI)
                return ExprStmt(None)
            e = parse_expr()
            try:
                expect(TokenKind.SEMI, "; esperado tras expresión")
            except ParseError:
                synchronize({TokenKind.SEMI, TokenKind.RBRACE})
                match(TokenKind.SEMI)
            return ExprStmt(e)

    # ---------- Expresiones (precedence climbing) ----------
    def parse_expr() -> Expr:
        return parse_assign()

    def parse_assign() -> Expr:
        left = parse_bin_level(0)
        if match(TokenKind.ASSIGN):
            right = parse_assign()
            return Assign(left, right)
        return left

    def parse_bin_level(level: int) -> Expr:
        if level >= len(_PREC):
            return parse_unary()
        left = parse_bin_level(level + 1)
        while tokens[i].kind in _PREC[level]:
            op_tok = tokens[i]; i_inc()
            right = parse_bin_level(level + 1)
            left = Binary(_BIN_OP_STR[op_tok.kind], left, right)
        return left

    def i_inc():
        nonlocal i
        i += 1

    def parse_unary() -> Expr:
        if tokens[i].kind in _UNARY_SET:
            op = tokens[i].lexeme; i_inc()
            expr = parse_unary()
            return Unary(op, expr)
        return parse_postfix()

    def parse_postfix() -> Expr:
        expr = parse_primary()
        while True:
            if match(TokenKind.LPAREN):
                args: List[Expr] = []
                if not match(TokenKind.RPAREN):
                    while True:
                        args.append(parse_expr())
                        if match(TokenKind.COMMA):
                            continue
                        expect(TokenKind.RPAREN, ") esperado en llamada")
                        break
                expr = Call(expr, args)
            elif match(TokenKind.LBRACKET):
                idx = parse_expr()
                expect(TokenKind.RBRACKET, "] esperado")
                expr = Index(expr, idx)
            else:
                break
        return expr

    def parse_primary() -> Expr:
        t = tokens[i]
        if t.kind == TokenKind.IDENT:
            i_inc(); return Var(t.lexeme)
        if t.kind in (TokenKind.NUMBER_INT, TokenKind.NUMBER_FLOAT):
            i_inc(); return Number(t.value)
        if match(TokenKind.LPAREN):
            e = parse_expr(); expect(TokenKind.RPAREN, ") esperado")
            return e
        report(errors, t.line, t.col, f"Expresión primaria inesperada '{t.lexeme}'")
        i_inc()  # avanzar para no quedar en bucle
        return Number(0)

    # ---------- Translation unit ----------
    decls: List[Decl] = []
    while tokens[i].kind not in (TokenKind.EOF,):
        if _is_type_kw(tokens[i].kind):
            d = parse_declaration()
            if d is not None:
                decls.append(d)
        else:
            # basura/decl perdida → intento de sincronización
            report(errors, tokens[i].line, tokens[i].col, "Se esperaba declaración o fin de archivo")
            synchronize({TokenKind.SEMI, TokenKind.RBRACE})
            if tokens[i].kind == TokenKind.SEMI:
                match(TokenKind.SEMI)
            if tokens[i].kind == TokenKind.RBRACE:
                match(TokenKind.RBRACE)
    return Program(decls), errors
```

---

## 5) Pretty printer y CLI

### `ast/pretty.py`

```python
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Union
from .nodes import *

IND = "  "

def _p(node, lvl=0) -> str:
    sp = IND * lvl
    if isinstance(node, Program):
        return "\n".join(_p(d, lvl) for d in node.decls)
    if isinstance(node, FuncDecl):
        ps = ", ".join(f"{p.type.base}{'*'*p.type.ptr_depth} {p.name}" + ("[]" if p.array else "") for p in node.params)
        return f"{sp}Func {node.ret_type.base}{'*'*node.ret_type.ptr_depth} {node.name}({ps})\n" + _p(node.body, lvl)
    if isinstance(node, VarDecl):
        parts = []
        for init in node.inits:
            arr = f"[{init.array.size}]" if init.array and init.array.size is not None else ("[]" if init.array else "")
            rhs = f" = {expr_to_str(init.init)}" if init.init else ""
            parts.append(f"{init.name}{arr}{rhs}")
        return f"{sp}Var {node.type.base}{'*'*node.type.ptr_depth} " + ", ".join(parts)
    if isinstance(node, Block):
        inner = "\n".join(_p(it, lvl+1) for it in node.items)
        return f"{sp}{{\n{inner}\n{sp}}}"
    if isinstance(node, IfStmt):
        s = f"{sp}If ({expr_to_str(node.cond)})\n" + _p(node.then, lvl+1)
        if node.els:
            s += f"\n{sp}else\n" + _p(node.els, lvl+1)
        return s
    if isinstance(node, WhileStmt):
        return f"{sp}While ({expr_to_str(node.cond)})\n" + _p(node.body, lvl+1)
    if isinstance(node, ForStmt):
        return f"{sp}For (init={expr_to_str(node.init)}, cond={expr_to_str(node.cond)}, it={expr_to_str(node.it)})\n" + _p(node.body, lvl+1)
    if isinstance(node, ReturnStmt):
        return f"{sp}Return {expr_to_str(node.expr)}"
    if isinstance(node, ExprStmt):
        return f"{sp}Expr {expr_to_str(node.expr)}"
    return f"{sp}<node {type(node).__name__}>"


def expr_to_str(e: Expr | None) -> str:
    if e is None:
        return "<empty>"
    if isinstance(e, Number):
        return str(e.value)
    if isinstance(e, Var):
        return e.name
    if isinstance(e, Assign):
        return f"({expr_to_str(e.left)} = {expr_to_str(e.right)})"
    if isinstance(e, Unary):
        return f"({e.op}{expr_to_str(e.expr)})"
    if isinstance(e, Binary):
        return f"({expr_to_str(e.left)} {e.op} {expr_to_str(e.right)})"
    if isinstance(e, Call):
        return f"{expr_to_str(e.callee)}(" + ", ".join(expr_to_str(a) for a in e.args) + ")"
    if isinstance(e, Index):
        return f"{expr_to_str(e.array)}[{expr_to_str(e.index)}]"
    return f"<{type(e).__name__}>"
```

### `cli.py`

```python
# -*- coding: utf-8 -*-
from __future__ import annotations
import sys
from lexer.lexer import tokenize
from parser.parser import parse
from ast.pretty import _p

EXAMPLE = r"""
int sum(int n){
  int i = 0, acc = 0;
  for(i = 0; i < n; i = i + 1){
    acc = acc + i;
  }
  return acc;
}
"""

def main(argv):
    if len(argv) > 1:
        with open(argv[1], 'r', encoding='utf-8') as f:
            src = f.read()
    else:
        src = EXAMPLE
    toks = tokenize(src)
    ast, errs = parse(toks)
    if errs:
        print("\n".join(errs), file=sys.stderr)
    print(_p(ast))

if __name__ == "__main__":
    main(sys.argv)
```

---

## 6) Pruebas unitarias (pytest)

### `tests/test_lexer.py`

```python
# -*- coding: utf-8 -*-
from lexer.lexer import tokenize
from lexer.tokens import TokenKind

def test_keywords_and_ops():
    code = "int x = a + b * 3; // comment\n"
    toks = tokenize(code)
    kinds = [t.kind for t in toks[:8]]
    assert kinds[:5] == [TokenKind.KW_INT, TokenKind.IDENT, TokenKind.ASSIGN, TokenKind.IDENT, TokenKind.PLUS]
    assert any(t.kind == TokenKind.SEMI for t in toks)
```

### `tests/test_parser_ok.py`

```python
# -*- coding: utf-8 -*-
from lexer.lexer import tokenize
from parser.parser import parse
from ast.nodes import Program, FuncDecl

def test_parse_function_sum():
    src = """
    int sum(int n){
      int i = 0, acc = 0;
      for(i = 0; i < n; i = i + 1){
        acc = acc + i;
      }
      return acc;
    }
    """
    ast, errs = parse(tokenize(src))
    assert isinstance(ast, Program)
    assert not errs
    assert isinstance(ast.decls[0], FuncDecl)
```

### `tests/test_parser_error.py`

```python
# -*- coding: utf-8 -*-
from lexer.lexer import tokenize
from parser.parser import parse

def test_error_recovery_missing_semi():
    src = """
    int x = 5
    int y = 6; // falta ; en la anterior línea
    """
    ast, errs = parse(tokenize(src))
    assert errs  # debe haber al menos un error
    # El parser debería continuar y reconocer la segunda declaración
    assert len(ast.decls) >= 1
```

---

## 7) Diagrama simple del **pipeline**

```
   +---------+        +-----------+        +-----------+        +-----------+
   |  Código | -----> |   Lexer   | -----> |   Parser  | -----> |   AST     |
   | fuente  | tokens | (tokeniza)| errores| (rec. desc) errores| (árbol)   |
   +---------+        +-----------+        +-----------+        +-----------+
                                           |  recuperación |                
                                           |   pánico      |                
```

---

## 8) Instrucciones para ejecutar **sin make**

**Requisitos**: Python 3.11+

1. Crear estructura de carpetas y archivos según el árbol.
2. Instalar pytest (opcional para pruebas):

   ```bash
   python -m pip install pytest
   ```
3. Ejecutar el ejemplo con la CLI (sin argumentos usa el `EXAMPLE` embebido):

   ```bash
   python cli.py
   ```
4. Ejecutar contra un archivo propio:

   ```bash
   python cli.py ruta/a/mi.c
   ```
5. Correr pruebas:

   ```bash
   pytest -q
   ```

---

## 9) Notas de diseño y ampliación

* **Expresiones**: el algoritmo de precedencia hace el parser compacto y compatible con el enfoque descendente.
* **LValues**: en un proyecto real, conviene validar que el lado izquierdo de `Assign` es un lvalue (`Var`/`Index`).
* **Tipos**: se modela `TypeSpec` + `ArrayType` para punteros/arreglos simples. Extender a más tipos es directo.
* **Errores**: el modo pánico sincroniza con `;`, `}`, `)`, `]`. Puedes afinar conjuntos por producción.
* **Siguiente paso**: agregar verificación semántica (tabla de símbolos) y generación de código/IR.

---

## 10) Caso de ejemplo adicional (con errores de sintaxis)

```c
int f(int n) {
  int a[10];
  a[0] = 1
  if (n > 0) {
    return a[0];
  else // falta ) y }
    return 0;
}
```

* El parser debe reportar al menos:

  * falta `;` tras asignación
  * `)` esperado tras condición de `if`
  * `}` esperado antes de `else`

---

> Con esto tienes un esqueleto completo, funcional y extensible para tu subset de C, escrito con **programación estructurada** y listo para ejecutar y probar. Ajusta los conjuntos de sincronización y la gramática según tus necesidades específicas.

---

## 11) **Análisis semántico**: tabla de símbolos + checker (estructurado)

### Nueva estructura

```
sema/
├─ __init__.py
├─ symtab.py
└─ checker.py
```

### `sema/symtab.py`

```python
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, List, Optional, TypedDict, Literal

SymbolKind = Literal["var", "func", "param"]

class Symbol(TypedDict, total=False):
    name: str
    kind: SymbolKind
    type: object         # ast.nodes.TypeSpec o ArrayType
    params: list         # para funciones: lista de (TypeSpec/ArrayType)
    storage: str         # "global" | "local"
    offset: int          # para futuras etapas (frame offset)

# Pila de ámbitos (cada ámbito es un dict nombre -> Symbol)
_scopes: List[Dict[str, Symbol]] = []

def enter_scope() -> None:
    _scopes.append({})

def leave_scope() -> None:
    _scopes.pop()

def current_scope() -> Dict[str, Symbol]:
    return _scopes[-1]

def declare(sym: Symbol, errors: List[str], line: int, col: int) -> None:
    top = current_scope()
    name = sym["name"]
    if name in top:
        errors.append(f"[{line}:{col}] Redeclaración de '{name}' en este ámbito")
    else:
        top[name] = sym

def lookup(name: str) -> Optional[Symbol]:
    for scope in reversed(_scopes):
        if name in scope:
            return scope[name]
    return None
```

### `sema/checker.py`

```python
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Optional, Tuple
from ast.nodes import *
from .symtab import enter_scope, leave_scope, declare, lookup, Symbol

# ---- utilidades de tipos (mínimas) ----

def is_integer(t: TypeSpec | ArrayType | None) -> bool:
    if isinstance(t, ArrayType):
        return False
    if not isinstance(t, TypeSpec):
        return False
    return t.base in {"int", "char"} and t.ptr_depth == 0

def is_arith(t: TypeSpec | ArrayType | None) -> bool:
    if isinstance(t, ArrayType):
        return False
    if not isinstance(t, TypeSpec):
        return False
    return t.base in {"int", "char", "float", "double"} and t.ptr_depth == 0

def is_pointer(t: TypeSpec | ArrayType | None) -> bool:
    return isinstance(t, TypeSpec) and t.ptr_depth > 0

def array_to_pointer(t: ArrayType | None) -> Optional[TypeSpec]:
    if t is None:
        return None
    # decae a puntero a elemento
    elem = t.elem
    if elem is None:
        return None
    return TypeSpec(base=elem.base, ptr_depth=elem.ptr_depth + 1)

# compatibilidad simple para asignación (se puede extender)

def assignable(dst: TypeSpec | ArrayType, src: TypeSpec | ArrayType) -> bool:
    # arrays: no asignables directamente en este subset
    if isinstance(dst, ArrayType) or isinstance(src, ArrayType):
        return False
    if dst.base == src.base and dst.ptr_depth == src.ptr_depth:
        return True
    # promociones numéricas simples (int/char <- int/char)
    if dst.ptr_depth == 0 and src.ptr_depth == 0:
        num = {"char", "int", "float", "double"}
        if dst.base in num and src.base in num:
            return True
    # punteros: permiten asignar void* <-> T* (muy simplificado)
    if dst.ptr_depth > 0 and src.ptr_depth > 0:
        return True
    return False

# ---- checker principal ----

def check(program: Program) -> List[str]:
    errors: List[str] = []

    # ámbito global
    enter_scope()

    # 1) Primero, declara firmas de funciones y variables globales
    for d in program.decls:
        if isinstance(d, FuncDecl):
            sig_types = []
            for p in d.params:
                t = p.array.elem if p.array else p.type
                sig_types.append(t)
            sym: Symbol = {
                "name": d.name,
                "kind": "func",
                "type": d.ret_type,
                "params": sig_types,
                "storage": "global",
            }
            declare(sym, errors, 1, 1)
        elif isinstance(d, VarDecl):
            for vi in d.inits:
                t = vi.array.elem if vi.array else d.type
                sym: Symbol = {
                    "name": vi.name,
                    "kind": "var",
                    "type": t,
                    "storage": "global",
                }
                declare(sym, errors, 1, 1)

    # 2) Segundo, valida cuerpos
    for d in program.decls:
        if isinstance(d, FuncDecl):
            check_func(d, errors)
        elif isinstance(d, VarDecl):
            # valida inicializadores
            for vi in d.inits:
                if vi.init is not None:
                    t_rhs = type_of_expr(vi.init, errors)
                    t_lhs = vi.array.elem if vi.array else d.type
                    if t_rhs is not None and t_lhs is not None and not assignable(t_lhs, t_rhs):
                        errors.append(f"Asignación incompatible en inicialización de '{vi.name}'")

    leave_scope()
    return errors

# ---- helpers por nodo ----

def check_func(fn: FuncDecl, errors: List[str]) -> None:
    enter_scope()
    # declara parámetros como variables locales
    for p in fn.params:
        t = p.array.elem if p.array else p.type
        declare({"name": p.name, "kind": "param", "type": t, "storage": "local"}, errors, 1, 1)
    check_block(fn.body, errors)
    leave_scope()


def check_block(block: Block, errors: List[str]) -> None:
    enter_scope()
    for it in block.items:
        if isinstance(it, VarDecl):
            for vi in it.inits:
                t = vi.array.elem if vi.array else it.type
                declare({"name": vi.name, "kind": "var", "type": t, "storage": "local"}, errors, 1, 1)
                if vi.init is not None:
                    t_rhs = type_of_expr(vi.init, errors)
                    if t_rhs is not None and t is not None and not assignable(t, t_rhs):
                        errors.append(f"Asignación incompatible a '{vi.name}'")
        elif isinstance(it, Block):
            check_block(it, errors)
        else:
            check_stmt(it, errors)
    leave_scope()


def check_stmt(s: Stmt, errors: List[str]) -> None:
    if isinstance(s, IfStmt):
        t = type_of_expr(s.cond, errors)
        # condición: aceptamos aritmético o puntero (estilo C), aquí solo aritmético
        if t is not None and not (is_arith(t) or is_pointer(t)):
            errors.append("Condición de if no escalar")
        check_stmt(s.then, errors)
        if s.els:
            check_stmt(s.els, errors)
    elif isinstance(s, WhileStmt):
        t = type_of_expr(s.cond, errors)
        if t is not None and not (is_arith(t) or is_pointer(t)):
            errors.append("Condición de while no escalar")
        check_stmt(s.body, errors)
    elif isinstance(s, ForStmt):
        if s.init: type_of_expr(s.init, errors)
        if s.cond:
            t = type_of_expr(s.cond, errors)
            if t is not None and not (is_arith(t) or is_pointer(t)):
                errors.append("Condición de for no escalar")
        if s.it: type_of_expr(s.it, errors)
        check_stmt(s.body, errors)
    elif isinstance(s, ReturnStmt):
        if s.expr: type_of_expr(s.expr, errors)
    elif isinstance(s, ExprStmt):
        if s.expr: type_of_expr(s.expr, errors)
    elif isinstance(s, Block):
        check_block(s, errors)

# ---- Tipado de expresiones ----

def type_of_expr(e: Expr, errors: List[str]) -> Optional[TypeSpec | ArrayType]:
    if isinstance(e, Number):
        # heurística: si tiene punto -> double, si no -> int
        if isinstance(e.value, float):
            return TypeSpec("double", 0)
        return TypeSpec("int", 0)
    if isinstance(e, Var):
        sym = lookup(e.name)
        if sym is None:
            errors.append(f"Identificador no declarado: '{e.name}'")
            return None
        return sym.get("type")
    if isinstance(e, Assign):
        t_l = type_of_expr(e.left, errors)
        t_r = type_of_expr(e.right, errors)
        # comprobar lvalue
        if not isinstance(e.left, (Var, Index)):
            errors.append("El lado izquierdo de una asignación debe ser un lvalue")
        if t_l is not None and t_r is not None and not assignable(t_l, t_r):
            errors.append("Tipos incompatibles en la asignación")
        return t_l
    if isinstance(e, Unary):
        t_e = type_of_expr(e.expr, errors)
        # casos mínimos
        if e.op in ('+', '-', '!','~'):
            if t_e and not (is_arith(t_e) or is_integer(t_e)):
                errors.append(f"Operador unario '{e.op}' sobre tipo no aritmético")
            return t_e
        if e.op == '&':
            # &x -> puntero a tipo de x (si Var o Index)
            if isinstance(e.expr, Var):
                t = type_of_expr(e.expr, errors)
                if isinstance(t, TypeSpec):
                    return TypeSpec(t.base, t.ptr_depth + 1)
                if isinstance(t, ArrayType):
                    return array_to_pointer(t)
            return TypeSpec("void", 1)  # simplificado
        if e.op == '*':
            # *p -> desreferencia
            if isinstance(t_e, TypeSpec) and t_e.ptr_depth > 0:
                return TypeSpec(t_e.base, t_e.ptr_depth - 1)
            errors.append("Desreferencia de un no-puntero")
            return None
        return t_e
    if isinstance(e, Binary):
        t_l = type_of_expr(e.left, errors)
        t_r = type_of_expr(e.right, errors)
        op = e.op
        if op in {"+","-","*","/","%"}:
            if (t_l and not is_arith(t_l)) or (t_r and not is_arith(t_r)):
                errors.append(f"Operador '{op}' requiere tipos aritméticos")
            # resultado: promoción sencilla
            return TypeSpec("double", 0) if (t_l and t_r) and (not is_integer(t_l) or not is_integer(t_r)) else TypeSpec("int", 0)
        if op in {"<","<=",">",">=","==","!="}:
            return TypeSpec("int", 0)
        if op in {"&&","||"}:
            return TypeSpec("int", 0)
        return t_l
    if isinstance(e, Call):
        # callee debe ser Var con símbolo de función
        if isinstance(e.callee, Var):
            sym = lookup(e.callee.name)
            if sym is None or sym.get("kind") != "func":
                errors.append(f"Llamada a identificador no-función: '{e.callee.name}'")
                return None
            params = sym.get("params", [])
            if len(params) != len(e.args):
                errors.append(f"Aridad incompatible en llamada a '{e.callee.name}'")
            # chequear tipos compatibles
            for (pt, arg) in zip(params, e.args):
                at = type_of_expr(arg, errors)
                if at is not None and pt is not None and not assignable(pt, at):
                    errors.append(f"Argumento incompatible en llamada a '{e.callee.name}'")
            return sym.get("type")  # tipo de retorno
        else:
            errors.append("Callee no es un identificador de función")
            return None
    if isinstance(e, Index):
        t_arr = type_of_expr(e.array, errors)
        t_idx = type_of_expr(e.index, errors)
        if t_idx is not None and not is_integer(t_idx):
            errors.append("Índice no entero en acceso de arreglo")
        # arreglo o puntero -> elemento
        if isinstance(t_arr, ArrayType):
            return t_arr.elem
        if isinstance(t_arr, TypeSpec) and t_arr.ptr_depth > 0:
            return TypeSpec(t_arr.base, t_arr.ptr_depth - 1)
        errors.append("Indexación de un no-arreglo")
        return None
    return None
```

### CLI actualizada para incluir el chequeo semántico

```python
# cli.py (reemplazo del contenido anterior)
# -*- coding: utf-8 -*-
from __future__ import annotations
import sys
from lexer.lexer import tokenize
from parser.parser import parse
from ast.pretty import _p
from sema.checker import check

EXAMPLE = r"""
int sum(int n){
  int i = 0, acc = 0;
  for(i = 0; i < n; i = i + 1){
    acc = acc + i;
  }
  return acc;
}
"""

def main(argv):
    if len(argv) > 1:
        with open(argv[1], 'r', encoding='utf-8') as f:
            src = f.read()
    else:
        src = EXAMPLE
    toks = tokenize(src)
    ast, parse_errs = parse(toks)
    sema_errs = check(ast)
    errs = parse_errs + sema_errs
    if errs:
        print("
".join(errs), file=sys.stderr)
    print(_p(ast))

if __name__ == "__main__":
    main(sys.argv)
```

### Pruebas semánticas (pytest)

`tests/test_sema_ok.py`

```python
# -*- coding: utf-8 -*-
from lexer.lexer import tokenize
from parser.parser import parse
from sema.checker import check

def test_sema_ok_sum():
    src = """
    int sum(int n){
      int acc = 0;
      for(acc = 0; acc < n; acc = acc + 1){}
      return acc;
    }
    """
    ast, perrs = parse(tokenize(src))
    assert not perrs
    serrs = check(ast)
    assert not serrs
```

`tests/test_sema_errors.py`

```python
# -*- coding: utf-8 -*-
from lexer.lexer import tokenize
from parser.parser import parse
from sema.checker import check

def test_undeclared_and_bad_call():
    src = """
    int f(int n){
      int acc = 0;
      acc = acc + x;   // x no declarada
      g(1,2,3);        // g no declarada
      return acc;
    }
    """
    ast, perrs = parse(tokenize(src))
    serrs = check(ast)
    assert any("no declarada" in e or "no-función" in e for e in serrs)


def test_array_index_type_and_assign():
    src = """
    int f(int n){
      int a[10];
      double d;
      a[1.5] = 2;   // índice no entero
      a = 3;        // array no asignable
      d = a;        // incompatible
      return n;
    }
    """
    ast, perrs = parse(tokenize(src))
    serrs = check(ast)
    joined = "
".join(serrs)
    assert "Índice no entero" in joined
    assert "no asignable" in joined or "Tipos incompatibles" in joined
```

### Instrucciones actualizadas

1. Crear los nuevos archivos en `sema/`.
2. Reemplazar el contenido de `cli.py` por la versión “CLI actualizada”.
3. Ejecutar:

   ```bash
   python cli.py              # corre lexer+parser+sema sobre el ejemplo
   pytest -q                  # incluye pruebas semánticas
   ```

> El checker es intencionalmente conservador y simple; puedes endurecer o flexibilizar reglas (p.ej., permitir más promociones, punteros aritméticos, arrays como parámetros —decay a puntero—, etc.).
