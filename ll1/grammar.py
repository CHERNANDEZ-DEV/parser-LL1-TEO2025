from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple

EPS = "ε"  # Epsilon (cadena vacía) en la gramática

# ----------------------------
# 1) LÉXICO: especificación y tokenizador
# ----------------------------

_TOKEN_SPEC = [
    # Flecha de producción: -> o → (Unicode)
    ("ARROW",    r"->|→"),
    # Alternativa
    ("OR",       r"\|"),
    # Agrupación
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    # Operadores EBNF postfijo
    ("STAR",     r"\*"),
    ("PLUS",     r"\+"),
    ("QMARK",    r"\?"),
    # Terminales entre comillas simples con soporte de escapes
    ("TERMINAL", r"'([^'\\]|\\.)*'"),
    # Identificadores (no terminales o nombres)
    ("ID",       r"[A-Za-z_][A-Za-z0-9_]*"),
    # Epsilon literal
    ("EPS",      r"ε"),
    # Espacios y comentarios (ignorados)
    ("SKIP",     r"[ \t\r\n]+"),
    ("COMMENT",  r"#.*"),
]
_MASTER = re.compile("|".join(f"(?P<{n}>{p})" for n, p in _TOKEN_SPEC))


# ----------------------------
# 2) MODELO DE GRAMÁTICA
# ----------------------------

Symbol = str
Span = Tuple[int, int, int, int]  # (opcional si tú luego agregas spans de tokens)

@dataclass
class Production:
    """
    Producción de gramática CFG: head -> body
    body es una lista de símbolos (no terminales y terminales).
    """
    head: Symbol
    body: List[Symbol]

@dataclass
class Grammar:
    """
    Gramática en BNF/CFG resultante de expandir una entrada en EBNF.
    - 'start' es el símbolo inicial.
    - 'nonterminals' y 'terminals' se rellenan heurísticamente en add_prod.
    """
    start: Symbol
    nonterminals: Set[Symbol] = field(default_factory=set)
    terminals: Set[Symbol] = field(default_factory=set)
    prods: List[Production] = field(default_factory=list)

    def by_head(self) -> Dict[Symbol, List[Production]]:
        """Agrupa producciones por cabeza (no terminal)."""
        grouped: Dict[Symbol, List[Production]] = {}
        for p in self.prods:
            grouped.setdefault(p.head, []).append(p)
        return grouped

    def add_prod(self, head: Symbol, body: List[Symbol]) -> None:
        """
        Inserta una producción y clasifica símbolos:
        - Si un símbolo es EPS: se considera 'vacío' (no se añade a terminals/nonterminals).
        - Si va entre comillas simples: es un terminal (se guarda sin comillas).
        - Si es 'identifier' Python: se considera no terminal.
        """
        self.nonterminals.add(head)
        for sym in body:
            if sym == EPS:
                continue
            if sym.startswith("'") and sym.endswith("'"):
                # Guardamos el terminal real sin comillas
                self.terminals.add(sym[1:-1])
            elif sym.isidentifier():
                self.nonterminals.add(sym)
        self.prods.append(Production(head, body))


# ----------------------------
# 3) ERRORES Y TOKENS
# ----------------------------

class GrammarError(Exception):
    """Errores de análisis de gramática (léxico o sintaxis)."""
    pass

class _Tok:
    """Token léxico simple con tipo y lexema."""
    def __init__(self, typ: str, val: str):
        self.type = typ
        self.value = val
    def __repr__(self) -> str:
        return f"{self.type}:{self.value}"

def _lex(src: str) -> List[_Tok]:
    """Convierte el texto de gramática en lista de tokens, omitiendo espacios y comentarios."""
    out: List[_Tok] = []
    for m in _MASTER.finditer(src):
        typ = m.lastgroup
        val = m.group()
        if typ in ("SKIP", "COMMENT"):
            continue
        out.append(_Tok(typ, val))
    return out


# ----------------------------
# 4) PARSER EBNF (descendente recursivo)
# ----------------------------

def parse_ebnf(src: str, start: Optional[str] = None) -> Grammar:
    """
    Parsea una gramática en EBNF y devuelve una Grammar en BNF (sin multiplicadores).
    Soporta:
      - A → B | C
      - Agrupación con ( ... )
      - Epsilon 'ε'
      - Terminales entre 'comillas simples' (con escapes)
      - Operadores postfijo: ?, *, +
      - Comentarios con '#'
    """
    toks = _lex(src)
    i = 0  # índice de lectura

    def peek() -> _Tok:
        return toks[i] if i < len(toks) else _Tok("EOF", "")

    def eat(expected: str) -> _Tok:
        nonlocal i
        if peek().type != expected:
            raise GrammarError(f"Expected {expected}, got {peek()}")
        i += 1
        return toks[i - 1]

    rules: List[Tuple[str, List[List[str]]]] = []  # [(head, alts)]
    nts: List[str] = []  # orden de aparición de no terminales

    # ---- sub-parsers ----

    def parse_atom() -> List[List[str]]:
        """
        Devuelve una lista de alternativas, cada una una secuencia (lista de símbolos).
        """
        if peek().type == "ID":
            return [[eat("ID").value]]
        if peek().type == "TERMINAL":
            return [[eat("TERMINAL").value]]
        if peek().type == "EPS":
            eat("EPS")
            return [[EPS]]
        if peek().type == "LPAREN":
            eat("LPAREN")
            alts = parse_expr()
            eat("RPAREN")
            return alts
        raise GrammarError(f"Atom expected, got {peek()}")

    def parse_item() -> List[List[str]]:
        """
        Un atom con multiplicador opcional:
          - sin multiplicador → mismas alternativas del atom
          - con multiplicador → cada alternativa se marca como ["__MULT__", op, ...atom...]
        """
        atoms = parse_atom()
        if peek().type in ("STAR", "PLUS", "QMARK"):
            op = eat(peek().type).type
            return [["__MULT__", op] + a for a in atoms]
        return atoms

    def parse_seq() -> List[List[str]]:
        """
        Secuencia (concatenación) de items: realiza el producto cartesiano de alternativas.
        Si la secuencia está vacía, devuelve [[EPS]].
        """
        seqs: List[List[str]] = [[]]
        first = True
        while peek().type in ("ID", "TERMINAL", "LPAREN", "EPS"):
            itm = parse_item()              # lista de alternativas
            new: List[List[str]] = []
            for pref in seqs:               # para cada prefijo acumulado
                for alt in itm:             # concatenar cada alternativa del item
                    new.append(pref + alt)
            seqs = new
            first = False
        return [[EPS]] if first else seqs

    def parse_expr() -> List[List[str]]:
        """
        Expresión con alternativas separadas por '|'.
        """
        alts = parse_seq()
        while peek().type == "OR":
            eat("OR")
            alts += parse_seq()
        return alts

    # ---- reglas: ID ARROW expr (sin separadores obligatorios de fin de regla) ----
    while peek().type != "EOF":
        if peek().type != "ID":
            raise GrammarError(f"Rule must start with ID; got {peek()}")
        head = eat("ID").value
        nts.append(head)
        eat("ARROW")
        alts = parse_expr()
        rules.append((head, alts))

    # ----------------------------
    # 5) EXPANSIÓN EBNF → BNF
    # ----------------------------

    g = Grammar(start or nts[0])
    fresh_i = 0

    def fresh(base: str) -> str:
        nonlocal fresh_i
        fresh_i += 1
        return f"{base}_ebnf{fresh_i}"

    for head, alts in rules:
        expanded: List[List[str]] = []

        for alt in alts:
            seq: List[str] = []
            j = 0
            while j < len(alt):
                tok = alt[j]

                if tok == "__MULT__":
                    # alt estructura: ["__MULT__", op, ...atom... [posible siguiente "__MULT__" o fin]]
                    op = alt[j + 1]
                    k = j + 2
                    atom: List[str] = []
                    while k < len(alt) and alt[k] != "__MULT__":
                        atom.append(alt[k])
                        k += 1
                    j = k  # saltamos justo detrás del atom

                    if op == "QMARK":
                        # opcional: (seq) | (seq + atom)
                        if seq:
                            expanded.append(seq.copy())
                            expanded.append(seq + atom)
                            seq = []
                        else:
                            expanded.append([EPS])
                            expanded.append(atom)

                    elif op == "STAR":
                        # * → A; A → ε | atom A ; y en la secuencia ponemos A
                        A = fresh("rep")
                        g.add_prod(A, [EPS])
                        g.add_prod(A, atom + [A])
                        seq.append(A)

                    elif op == "PLUS":
                        # + → atom A ; A → ε | atom A
                        A = fresh("rep1")
                        g.add_prod(A, atom + [A])
                        g.add_prod(A, [EPS])
                        seq += atom + [A]
                    else:
                        raise GrammarError("Unknown multiplicity")
                else:
                    seq.append(tok)
                    j += 1

            if seq:
                expanded.append(seq)

        if not expanded:
            expanded = [[EPS]]

        for body in expanded:
            g.add_prod(head, body)

    return g


# ----------------------------
# 6) SALIDA / PRETTY-PRINT
# ----------------------------

def dump_text(g: Grammar) -> str:
    """
    Devuelve un texto con la gramática agrupada por cabeza:
      Head -> sym sym | sym ...
    Nota: los terminales aquí pueden aparecer con comillas si vinieron así del parseo.
    """
    byh = g.by_head()
    lines = []
    for h, prods in byh.items():
        alts = " | ".join(" ".join(p.body) for p in prods)
        lines.append(f"{h} -> {alts}")
    return "\n".join(lines)
