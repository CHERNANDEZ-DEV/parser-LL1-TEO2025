from __future__ import annotations
from typing import List, Tuple, Optional, Union
from lexer.tokens import Token, TokenKind
from ast.nodes import *
from .errors import report, ParseError

# ---------- helpers ----------
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

# ------------- parser principal -------------

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
        while tokens[i].kind not in sync_kinds and tokens[i].kind != TokenKind.EOF:
            i += 1

    # ---------- tipos ----------
    def parse_type() -> TypeSpec:
        t = peek()
        if not _is_type_kw(t.kind):
            report(errors, t.line, t.col, "Se esperaba especificador de tipo"); raise ParseError()
        base = t.lexeme; match(t.kind)
        ptr_depth = 0
        while match(TokenKind.STAR):
            ptr_depth += 1
        return TypeSpec(base=base, ptr_depth=ptr_depth)

    def opt_array_suffix() -> Optional[ArrayType]:
        if match(TokenKind.LBRACKET):
            size = None
            if tokens[i].kind == TokenKind.NUMBER_INT:
                size = tokens[i].value; match(TokenKind.NUMBER_INT)
            try:
                expect(TokenKind.RBRACKET, "] esperado")
            except ParseError:
                synchronize({TokenKind.SEMI, TokenKind.COMMA, TokenKind.RPAREN, TokenKind.RBRACKET})
            return ArrayType(elem=None, size=size)
        return None

    # ---------- declaraciones ----------
    def parse_declaration() -> Optional[Decl]:
        try:
            ts = parse_type()
        except ParseError:
            synchronize({TokenKind.SEMI, TokenKind.RBRACE}); match(TokenKind.SEMI)
            return None

        if tokens[i].kind != TokenKind.IDENT:
            report(errors, tokens[i].line, tokens[i].col, "Se esperaba identificador tras el tipo")
            synchronize({TokenKind.SEMI, TokenKind.RBRACE}); match(TokenKind.SEMI)
            return None
        name_tok = tokens[i]; match(TokenKind.IDENT)

        # función
        if match(TokenKind.LPAREN):
            params: List[Param] = []
            if not match(TokenKind.RPAREN):
                while True:
                    ptype = parse_type()
                    if tokens[i].kind != TokenKind.IDENT:
                        report(errors, tokens[i].line, tokens[i].col, "Se esperaba nombre de parámetro"); raise ParseError()
                    pname = tokens[i].lexeme; match(TokenKind.IDENT)
                    arr = opt_array_suffix()
                    params.append(Param(ptype, pname, arr))
                    if match(TokenKind.COMMA): continue
                    expect(TokenKind.RPAREN, ") esperado en parámetros"); break
            body = parse_compound()
            return FuncDecl(ret_type=ts, name=name_tok.lexeme, params=params, body=body)

        # variables (lista de declaradores)
        inits: List[VarInit] = []
        arr = opt_array_suffix()
        init_expr = None
        if match(TokenKind.ASSIGN):
            init_expr = parse_expr()
        inits.append(VarInit(name=name_tok.lexeme, array=arr, init=init_expr))
        while match(TokenKind.COMMA):
            if tokens[i].kind != TokenKind.IDENT:
                report(errors, tokens[i].line, tokens[i].col, "Se esperaba identificador en declarador"); break
            nm = tokens[i].lexeme; match(TokenKind.IDENT)
            arr2 = opt_array_suffix()
            init2 = None
            if match(TokenKind.ASSIGN):
                init2 = parse_expr()
            inits.append(VarInit(name=nm, array=arr2, init=init2))
        try:
            expect(TokenKind.SEMI, "; esperado tras declaración de variable")
        except ParseError:
            synchronize({TokenKind.SEMI, TokenKind.RBRACE}); match(TokenKind.SEMI)

        # completa elem de arrays con el tipo base
        for vi in inits:
            if vi.array and vi.array.elem is None:
                vi.array.elem = ts
        return VarDecl(type=ts, inits=inits)

    # ---------- compuestos y sentencias ----------
    def parse_compound() -> Block:
        try:
            expect(TokenKind.LBRACE, "{ esperado")
        except ParseError:
            synchronize({TokenKind.LBRACE}); match(TokenKind.LBRACE)
        items: List[Union[Stmt, Decl]] = []
        while tokens[i].kind not in {TokenKind.RBRACE, TokenKind.EOF}:
            if _is_type_kw(tokens[i].kind):
                d = parse_declaration()
                if d is not None: items.append(d)
            else:
                s = parse_stmt()
                if s is not None: items.append(s)
        try:
            expect(TokenKind.RBRACE, "} esperado")
        except ParseError:
            pass
        return Block(items)

    def parse_stmt() -> Optional[Stmt]:
        k = tokens[i].kind
        if k == TokenKind.KW_IF:
            match(TokenKind.KW_IF); expect(TokenKind.LPAREN, "( tras if")
            cond = parse_expr(); expect(TokenKind.RPAREN, ") tras condición")
            then = parse_stmt(); els = None
            if match(TokenKind.KW_ELSE): els = parse_stmt()
            return IfStmt(cond, then, els)
        if k == TokenKind.KW_WHILE:
            match(TokenKind.KW_WHILE); expect(TokenKind.LPAREN, "( tras while")
            cond = parse_expr(); expect(TokenKind.RPAREN, ") esperado")
            body = parse_stmt(); return WhileStmt(cond, body)
        if k == TokenKind.KW_FOR:
            match(TokenKind.KW_FOR); expect(TokenKind.LPAREN, "( tras for")
            if tokens[i].kind == TokenKind.SEMI:
                match(TokenKind.SEMI); init = None
            else:
                init = parse_expr(); expect(TokenKind.SEMI, "; en for-init")
            cond = None if tokens[i].kind == TokenKind.SEMI else parse_expr()
            expect(TokenKind.SEMI, "; en for-cond")
            it = None if tokens[i].kind == TokenKind.RPAREN else parse_expr()
            expect(TokenKind.RPAREN, ") en for")
            body = parse_stmt(); return ForStmt(init, cond, it, body)
        if k == TokenKind.KW_RETURN:
            match(TokenKind.KW_RETURN); e = None if tokens[i].kind == TokenKind.SEMI else parse_expr()
            expect(TokenKind.SEMI, "; tras return"); return ReturnStmt(e)
        if k == TokenKind.LBRACE:
            return parse_compound()
        # ExprStmt
        if k == TokenKind.SEMI:
            match(TokenKind.SEMI); return ExprStmt(None)
        e = parse_expr()
        try:
            expect(TokenKind.SEMI, "; esperado tras expresión")
        except ParseError:
            synchronize({TokenKind.SEMI, TokenKind.RBRACE}); match(TokenKind.SEMI)
        return ExprStmt(e)

    # ---------- expresiones (precedence climbing) ----------
    def parse_expr() -> Expr:
        return parse_assign()

    def parse_assign() -> Expr:
        left = parse_bin_level(0)
        if match(TokenKind.ASSIGN):
            right = parse_assign()
            return Assign(left, right)  # '=' es asociativo a derecha
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
            return Unary(op, parse_unary())
        return parse_postfix()

    def parse_postfix() -> Expr:
        node = parse_primary()
        while True:
            if match(TokenKind.LPAREN):
                args: List[Expr] = []
                if not match(TokenKind.RPAREN):
                    while True:
                        args.append(parse_expr())
                        if match(TokenKind.COMMA):
                            continue
                        expect(TokenKind.RPAREN, ") esperado en llamada"); break
                node = Call(node, args); continue
            if match(TokenKind.LBRACKET):
                idx = parse_expr(); expect(TokenKind.RBRACKET, "] esperado")
                node = Index(node, idx); continue
            break
        return node

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
        i_inc()
        return Number(0)

    # ---------- translation unit ----------
    decls: List[Decl] = []
    while tokens[i].kind != TokenKind.EOF:
        if _is_type_kw(tokens[i].kind):
            d = parse_declaration()
            if d is not None:
                decls.append(d)
        else:
            report(errors, tokens[i].line, tokens[i].col, "Se esperaba declaración o fin de archivo")
            synchronize({TokenKind.SEMI, TokenKind.RBRACE})
            if tokens[i].kind == TokenKind.SEMI: match(TokenKind.SEMI)
            if tokens[i].kind == TokenKind.RBRACE: match(TokenKind.RBRACE)
    return Program(decls), errors
