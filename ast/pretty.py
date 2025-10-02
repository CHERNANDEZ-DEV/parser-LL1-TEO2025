from __future__ import annotations
from .nodes import *

IND = "  "

def _p(node, lvl=0) -> str:
    sp = IND * lvl
    if isinstance(node, Program):
        return "\n".join(_p(d, lvl) for d in node.decls)
    if isinstance(node, FuncDecl):
        ps = ", ".join(f"{p.type.base}{'*'*p.type.ptr_depth} {p.name}" + ("[]" if p.array else "") for p in node.params)
        return f"{sp}Func {node.ret_type.base}{'*'*node.ret_type.ptr_depth} {node.name}({ps})\n" + _p(node.body, lvl)
    if isinstance(node, VarDecl):
        parts = []
        for init in node.inits:
            arr = f"[{init.array.size}]" if init.array and init.array.size is not None else ("[]" if init.array else "")
            rhs = f" = {expr_to_str(init.init)}" if init.init else ""
            parts.append(f"{init.name}{arr}{rhs}")
        return f"{sp}Var {node.type.base}{'*'*node.type.ptr_depth} " + ", ".join(parts)
    if isinstance(node, Block):
        inner = "\n".join(_p(it, lvl+1) for it in node.items)
        return f"{sp}{{\n{inner}\n{sp}}}"
    if isinstance(node, IfStmt):
        s = f"{sp}If ({expr_to_str(node.cond)})\n" + _p(node.then, lvl+1)
        if node.els:
            s += f"\n{sp}else\n" + _p(node.els, lvl+1)
        return s
    if isinstance(node, WhileStmt):
        return f"{sp}While ({expr_to_str(node.cond)})\n" + _p(node.body, lvl+1)
    if isinstance(node, ForStmt):
        return f"{sp}For (init={expr_to_str(node.init)}, cond={expr_to_str(node.cond)}, it={expr_to_str(node.it)})\n" + _p(node.body, lvl+1)
    if isinstance(node, ReturnStmt):
        return f"{sp}Return {expr_to_str(node.expr)}"
    if isinstance(node, ExprStmt):
        return f"{sp}Expr {expr_to_str(node.expr)}"
    return f"{sp}<node {type(node).__name__}>"

def expr_to_str(e: Expr | None) -> str:
    if e is None:
        return "<empty>"
    if isinstance(e, Number):
        return str(e.value)
    if isinstance(e, Var):
        return e.name
    if isinstance(e, Assign):
        return f"({expr_to_str(e.left)} = {expr_to_str(e.right)})"
    if isinstance(e, Unary):
        return f"({e.op}{expr_to_str(e.expr)})"
    if isinstance(e, Binary):
        return f"({expr_to_str(e.left)} {e.op} {expr_to_str(e.right)})"
    if isinstance(e, Call):
        return f"{expr_to_str(e.callee)}(" + ", ".join(expr_to_str(a) for a in e.args) + ")"
    if isinstance(e, Index):
        return f"{expr_to_str(e.array)}[{expr_to_str(e.index)}]"
    return f"<{type(e).__name__}>"
