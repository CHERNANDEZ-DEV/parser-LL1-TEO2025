from __future__ import annotations
from typing import Dict, List, Set
from .grammar import Grammar, EPS

def _is_term(sym: str, g: Grammar) -> bool:
    """
    Determina si 'sym' es terminal respecto a la gramática 'g'.
    Convención de 'Grammar':
      - Los no terminales están en g.nonterminals.
      - Los terminales en producciones aparecen entre comillas:  'if' , '+' , '(' , etc.
      - EPS es el símbolo especial de epsilon.
    """
    return (sym != EPS) and (sym not in g.nonterminals)


def first_of_sequence(seq: List[str],
                      FIRST: Dict[str, Set[str]],
                      g: Grammar) -> Set[str]:
    """
    Calcula FIRST de una secuencia de símbolos (X1 X2 ... Xn) según la gramática 'g'.

    Reglas:
      - Si el primer símbolo es terminal t → FIRST(seq) = {t} (sin comillas).
      - Si es no terminal, se unen FIRST(X) - {ε}. Si ε ∈ FIRST(X), se continúa con el siguiente.
      - Si todos los símbolos de la secuencia pueden derivar ε, entonces ε ∈ FIRST(seq).

    Importante:
      - Los terminales escritos como "'+'" o "'id'" se devuelven sin comillas: '+' , 'id'.
      - Se usa el diccionario FIRST (de no terminales) ya calculado/incremental.
    """
    out: Set[str] = set()
    for X in seq:
        if _is_term(X, g):
            # Terminal escrito con comillas en la gramática → devolvemos sin comillas
            out.add(X.strip("'"))
            return out
        else:
            # No terminal: agregamos todos sus primeros excepto ε
            out |= {t for t in FIRST[X] if t != EPS}
            # Si X no puede producir ε, paramos
            if EPS not in FIRST[X]:
                return out
    # Si llegamos aquí, todos pueden producir ε
    out.add(EPS)
    return out


def compute_first(g: Grammar) -> Dict[str, Set[str]]:
    """
    Calcula FIRST(A) para cada no terminal A de la gramática 'g'.

    Estrategia:
      - Inicializa FIRST(A) = ∅.
      - Itera hasta alcanzar un punto fijo:
          Para cada producción A → X1 X2 ... Xn
            - Recorre símbolos:
                * Si X1 es terminal t: añade t a FIRST(A) y detén esta producción.
                * Si X1 es no terminal:
                    añade FIRST(X1) - {ε} a FIRST(A).
                    si ε ∈ FIRST(X1), sigue con X2; si no, detén.
            - Si todos los Xi pueden derivar ε, añade ε a FIRST(A).
    """
    FIRST: Dict[str, Set[str]] = {A: set() for A in g.nonterminals}
    changed = True

    while changed:
        changed = False
        for p in g.prods:
            A = p.head
            i = 0
            can_eps = True  # asume que todo el cuerpo podría ser ε hasta que se demuestre lo contrario

            while i < len(p.body):
                X = p.body[i]

                if _is_term(X, g):
                    # Terminal (con comillas en producciones)
                    t = X.strip("'")
                    if t not in FIRST[A]:
                        FIRST[A].add(t)
                        changed = True
                    can_eps = False
                    break  # esta producción ya contribuyó con un terminal

                else:
                    # No terminal: union FIRST(X) - {ε}
                    added = {t for t in FIRST[X] if t != EPS}
                    if not added.issubset(FIRST[A]):
                        FIRST[A] |= added
                        changed = True

                    # Si X no puede producir ε, no seguimos con más símbolos
                    if EPS in FIRST[X]:
                        i += 1
                    else:
                        can_eps = False
                        break

            # Si todo el cuerpo puede desaparecer, ε ∈ FIRST(A)
            if can_eps and EPS not in FIRST[A]:
                FIRST[A].add(EPS)
                changed = True

    return FIRST


def compute_follow(g: Grammar,
                   FIRST: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    """
    Calcula FOLLOW(A) para cada no terminal A, usando FIRST previamente calculado.

    Reglas:
      1) '$' ∈ FOLLOW(S) donde S es el símbolo inicial.
      2) Para cada producción A → α B β:
           - Añadir FIRST(β) - {ε} a FOLLOW(B)
           - Si ε ∈ FIRST(β) (o β es vacío), añadir FOLLOW(A) a FOLLOW(B)

    Algoritmo:
      - Inicializar FOLLOW(A) = ∅, y FOLLOW(S) = {'$'}
      - Iterar hasta punto fijo aplicando las reglas anteriores a todas las producciones.
    """
    FOLLOW: Dict[str, Set[str]] = {A: set() for A in g.nonterminals}
    FOLLOW[g.start].add('$')  # fin de entrada para el símbolo inicial

    changed = True
    while changed:
        changed = False

        for p in g.prods:
            A = p.head
            # Recorremos el cuerpo buscando no terminales B
            for i, B in enumerate(p.body):
                if B in g.nonterminals:
                    beta = p.body[i+1:]  # lo que sigue a B
                    first_beta = first_of_sequence(beta, FIRST, g)

                    # Regla 2a: FIRST(beta) - {ε} ⊆ FOLLOW(B)
                    add_terms = {t for t in first_beta if t != EPS}
                    if not add_terms.issubset(FOLLOW[B]):
                        FOLLOW[B] |= add_terms
                        changed = True

                    # Regla 2b: si ε ∈ FIRST(beta) o beta es vacío → FOLLOW(A) ⊆ FOLLOW(B)
                    if EPS in first_beta or not beta:
                        if not FOLLOW[A].issubset(FOLLOW[B]):
                            FOLLOW[B] |= FOLLOW[A]
                            changed = True

    return FOLLOW
