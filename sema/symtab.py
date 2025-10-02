from __future__ import annotations
from typing import List, Dict, Optional, Any

Symbol = Dict[str, Any]

# Stack of scopes for nested symbol tables
_scope_stack: List[Dict[str, Symbol]] = []

def enter_scope() -> None:
    """Enter a new scope level."""
    _scope_stack.append({})

def leave_scope() -> None:
    """Leave the current scope level."""
    if _scope_stack:
        _scope_stack.pop()

def declare(symbol: Symbol, errors: List[str], line: int = 1, col: int = 1) -> None:
    """Declare a symbol in the current scope."""
    if not _scope_stack:
        errors.append(f"Error: No hay ámbito actual para declarar '{symbol['name']}'")
        return
    
    current_scope = _scope_stack[-1]
    name = symbol["name"]
    
    if name in current_scope:
        errors.append(f"Error en línea {line}, columna {col}: '{name}' ya está declarado en este ámbito")
    else:
        current_scope[name] = symbol

def lookup(name: str) -> Optional[Symbol]:
    """Look up a symbol in the scope stack, starting from the innermost scope."""
    for scope in reversed(_scope_stack):
        if name in scope:
            return scope[name]
    return None