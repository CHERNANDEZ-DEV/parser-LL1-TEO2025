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
