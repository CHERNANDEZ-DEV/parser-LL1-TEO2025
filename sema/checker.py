from __future__ import annotations
from typing import List, Optional
from ast.nodes import *
from .symtab import enter_scope, leave_scope, declare, lookup, Symbol

# ---- utilidades de tipos ----
def is_integer(t: TypeSpec | ArrayType | None) -> bool:
    return isinstance(t, TypeSpec) and t.ptr_depth == 0 and t.base in {"int", "char"}

def is_arith(t: TypeSpec | ArrayType | None) -> bool:
    return isinstance(t, TypeSpec) and t.ptr_depth == 0 and t.base in {"int", "char", "float", "double"}

def is_pointer(t: TypeSpec | ArrayType | None) -> bool:
    return isinstance(t, TypeSpec) and t.ptr_depth > 0

def array_to_pointer(t: ArrayType | None) -> Optional[TypeSpec]:
    if t is None or t.elem is None:
        return None
    return TypeSpec(base=t.elem.base, ptr_depth=t.elem.ptr_depth + 1)

def assignable(dst: TypeSpec | ArrayType, src: TypeSpec | ArrayType) -> bool:
    if isinstance(dst, ArrayType) or isinstance(src, ArrayType):
        return False
    if dst.base == src.base and dst.ptr_depth == src.ptr_depth:
        return True
    num = {"char", "int", "float", "double"}
    if dst.ptr_depth == 0 and src.ptr_depth == 0 and dst.base in num and src.base in num:
        return True
    if dst.ptr_depth > 0 and src.ptr_depth > 0:
        return True
    return False

# ---- checker principal ----
def check(program: Program) -> List[str]:
    errors: List[str] = []
    enter_scope()

    # declarar globals
    for d in program.decls:
        if isinstance(d, FuncDecl):
            sig = []
            for p in d.params:
                t = p.array.elem if p.array else p.type
                sig.append(t)
            declare({"name": d.name, "kind": "func", "type": d.ret_type, "params": sig, "storage": "global"}, errors, 1, 1)
        elif isinstance(d, VarDecl):
            for vi in d.inits:
                t = vi.array.elem if vi.array else d.type
                declare({"name": vi.name, "kind": "var", "type": t, "storage": "global"}, errors, 1, 1)

    # validar
    for d in program.decls:
        if isinstance(d, FuncDecl):
            check_func(d, errors)
        elif isinstance(d, VarDecl):
            for vi in d.inits:
                if vi.init is not None:
                    t_rhs = type_of_expr(vi.init, errors)
                    t_lhs = vi.array.elem if vi.array else d.type
                    if t_rhs is not None and t_lhs is not None and not assignable(t_lhs, t_rhs):
                        errors.append(f"Asignación incompatible en inicialización de '{vi.name}'")

    leave_scope(); return errors

def check_func(fn: FuncDecl, errors: List[str]) -> None:
    enter_scope()
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
        if t is not None and not (is_arith(t) or is_pointer(t)):
            errors.append("Condición de if no escalar")
        check_stmt(s.then, errors)
        if s.els: check_stmt(s.els, errors)
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

def type_of_expr(e: Expr, errors: List[str]) -> Optional[TypeSpec | ArrayType]:
    if isinstance(e, Number):
        return TypeSpec("double", 0) if isinstance(e.value, float) else TypeSpec("int", 0)
    if isinstance(e, Var):
        sym = lookup(e.name)
        if sym is None:
            errors.append(f"Identificador no declarado: '{e.name}'"); return None
        return sym.get("type")
    if isinstance(e, Assign):
        t_l = type_of_expr(e.left, errors); t_r = type_of_expr(e.right, errors)
        if not isinstance(e.left, (Var, Index)):
            errors.append("El lado izquierdo de una asignación debe ser un lvalue")
        if t_l is not None and t_r is not None and not assignable(t_l, t_r):
            errors.append("Tipos incompatibles en la asignación")
        return t_l
    if isinstance(e, Unary):
        t_e = type_of_expr(e.expr, errors)
        if e.op in ('+', '-', '!','~'):
            if t_e and not (is_arith(t_e) or is_integer(t_e)):
                errors.append(f"Operador unario '{e.op}' sobre tipo no aritmético")
            return t_e
        if e.op == '&':
            if isinstance(e.expr, Var):
                t = type_of_expr(e.expr, errors)
                if isinstance(t, TypeSpec):
                    return TypeSpec(t.base, t.ptr_depth + 1)
                if isinstance(t, ArrayType):
                    return array_to_pointer(t)
            return TypeSpec("void", 1)
        if e.op == '*':
            if isinstance(t_e, TypeSpec) and t_e.ptr_depth > 0:
                return TypeSpec(t_e.base, t_e.ptr_depth - 1)
            errors.append("Desreferencia de un no-puntero"); return None
        return t_e
    if isinstance(e, Binary):
        t_l = type_of_expr(e.left, errors); t_r = type_of_expr(e.right, errors)
        if e.op in {"+","-","*","/","%"}:
            if (t_l and not is_arith(t_l)) or (t_r and not is_arith(t_r)):
                errors.append(f"Operador '{e.op}' requiere tipos aritméticos")
            return TypeSpec("double", 0) if (t_l and t_r) and (not is_integer(t_l) or not is_integer(t_r)) else TypeSpec("int", 0)
        if e.op in {"<","<=",">",">=","==","!="}:
            return TypeSpec("int", 0)
        if e.op in {"&&","||"}:
            return TypeSpec("int", 0)
        return t_l
    if isinstance(e, Call):
        if isinstance(e.callee, Var):
            sym = lookup(e.callee.name)
            if sym is None or sym.get("kind") != "func":
                errors.append(f"Llamada a identificador no-función: '{e.callee.name}'"); return None
            params = sym.get("params", [])
            if len(params) != len(e.args):
                errors.append(f"Aridad incompatible en llamada a '{e.callee.name}'")
            for (pt, arg) in zip(params, e.args):
                at = type_of_expr(arg, errors)
                if at is not None and pt is not None and not assignable(pt, at):
                    errors.append(f"Argumento incompatible en llamada a '{e.callee.name}'")
            return sym.get("type")
        errors.append("Callee no es un identificador de función"); return None
    if isinstance(e, Index):
        t_arr = type_of_expr(e.array, errors); t_idx = type_of_expr(e.index, errors)
        if t_idx is not None and not is_integer(t_idx):
            errors.append("Índice no entero en acceso de arreglo")
        if isinstance(t_arr, ArrayType):
            return t_arr.elem
        if isinstance(t_arr, TypeSpec) and t_arr.ptr_depth > 0:
            return TypeSpec(t_arr.base, t_arr.ptr_depth - 1)
        errors.append("Indexación de un no-arreglo"); return None
    return None
