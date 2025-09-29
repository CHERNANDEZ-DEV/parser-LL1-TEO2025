from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# (l1, c1, l2, c2) = (línea inicial, columna inicial, línea final, columna final)
Span = Tuple[int, int, int, int]


@dataclass
class ASTNode:
    """
    Representa un nodo de un Árbol de Sintaxis Abstracta (AST).

    Atributos
    ---------
    type : str
        Nombre o etiqueta del tipo de nodo (p.ej., "BinaryOp", "IfStmt", "Identifier").
    children : List[ASTNode]
        Lista de nodos hijos. Por defecto, lista vacía.
    value : Optional[str]
        Valor atómico asociado (p.ej., texto de un literal o identificador). Puede ser None.
    span : Optional[Span]
        Rango (línea/columna inicial y final) del código fuente que cubre el nodo. Puede ser None.

    Notas
    -----
    - El AST modela la estructura lógica del programa, omitiendo detalles de sintaxis concreta
      (paréntesis, comas, espacios, etc.) salvo que sean semánticamente relevantes.
    - `span` es útil para mensajes de error, resaltado y herramientas de análisis.
    """

    type: str
    children: List['ASTNode'] = field(default_factory=list)
    value: Optional[str] = None
    span: Optional[Span] = None

    def pretty(self, level: int = 0) -> str:
        """
        Devuelve una cadena multilínea con la representación jerárquica del árbol.

        Parámetros
        ----------
        level : int
            Nivel de indentación actual (usado internamente para recursión).

        Retorna
        -------
        str
            Texto con una línea por nodo. Cada nivel agrega dos espacios de indentación.
            Incluye `value` y `span` si están presentes.

        Ejemplo
        -------
        BinaryOp
          Identifier value='x'
          Number value='1'
        """
        pad = "  " * level  # dos espacios por nivel
        meta = f" value={self.value!r}" if self.value is not None else ""
        span = f" span={self.span}" if self.span is not None else ""
        out = [f"{pad}{self.type}{meta}{span}"]
        for ch in self.children:
            out.append(ch.pretty(level + 1))
        return "\n".join(out)


def pretty_print(node: ASTNode) -> None:
    """
    Imprime en consola la representación jerárquica (pretty) de un AST.

    Parámetros
    ----------
    node : ASTNode
        Raíz del árbol a imprimir.
    """
    print(node.pretty())
