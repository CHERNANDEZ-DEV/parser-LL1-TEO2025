from __future__ import annotations
from typing import List

class ParseError(Exception):
    """Exception raised during parsing to indicate an error."""
    pass

def report(errors: List[str], line: int, col: int, message: str) -> None:
    """Report a parsing error at the given location."""
    errors.append(f"Error en línea {line}, columna {col}: {message}")