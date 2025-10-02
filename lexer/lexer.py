from __future__ import annotations
import re
from typing import List
from .tokens import Token, TokenKind, KEYWORDS

# Orden importa: patrones multi-caracter primero
_TOKEN_SPEC = [
    (TokenKind.LE, r"<="),
    (TokenKind.GE, r">="),
    (TokenKind.EQEQ, r"=="),
    (TokenKind.NEQ, r"!="),
    (TokenKind.ANDAND, r"&&"),
    (TokenKind.OROR, r"\|\|"),
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
            lines = txt.split('\n')
            if len(lines) > 1:
                line += len(lines) - 1
                col = len(lines[-1]) + 1
            else:
                col += len(txt)
            i = m.end()
            continue

        # comentarios //
        if src.startswith('//', i):
            j = src.find('\n', i)
            if j == -1:
                col += (n - i)
                i = n
            else:
                line += 1
                col = 1
                i = j + 1
            continue

        # comentarios /* ... */
        if src.startswith('/*', i):
            j = src.find('*/', i+2)
            if j == -1:
                j = n - 2  # consume hasta EOF si no cierra
            chunk = src[i:j+2]
            lines = chunk.split('\n')
            if len(lines) > 1:
                line += len(lines) - 1
                col = len(lines[-1]) + 1
            else:
                col += len(chunk)
            i = j + 2
            continue

        # identificador / palabra clave
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
            if re.match(pat, src[i:]):
                lex = re.match(pat, src[i:]).group(0)
                emit(kind, lex, lex)
                i += len(lex)
                col += len(lex)
                matched = True
                break
        if matched:
            continue

        # carácter inesperado
        emit(TokenKind.INVALID, src[i], src[i])
        i += 1
        col += 1

    tokens.append(Token(TokenKind.EOF, "<eof>", line, col))
    return tokens
