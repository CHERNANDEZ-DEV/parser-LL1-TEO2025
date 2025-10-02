from __future__ import annotations
from typing import List

class ParseError(Exception):
    pass

def report(errors: List[str], line: int, col: int, msg: str) -> None:
    errors.append(f"[{line}:{col}] Error de sintaxis: {msg}")
