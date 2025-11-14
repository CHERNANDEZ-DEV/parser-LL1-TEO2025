from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from shutil import get_terminal_size
import os, sys, glob, argparse

from c_lexer import tokens, lexer            
from ll1_parser import tabla_ll1            

INDEX: Dict[Tuple[str, str], List[str]] = {(A, a): prod for (A, a, prod) in tabla_ll1}

def _clip(s: str, w: int) -> str:
    if s is None:
        s = ""
    if len(s) <= w:
        return s
    if w <= 1:
        return s[:w]
    return s[:max(0, w - 1)] + "…"

def _format_row(buf: str, stack: str, action: str, W: Tuple[int, int, int]) -> str:
    b = _clip(buf, W[0]).ljust(W[0])
    s = _clip(stack, W[1]).ljust(W[1])
    a = _clip(action, W[2]).ljust(W[2])
    return f"{b}  {s}  {a}"

@dataclass
class Node:
    label: str                                  
    token_type: Optional[str] = None             
    lexeme: Optional[Any] = None                 
    children: List["Node"] = field(default_factory=list)

    def add(self, child: "Node"):
        self.children.append(child)
        return child

def _tokenize(src: str):
    lexer.lineno = 1
    lexer.input(src)
    out = []
    while True:
        t = lexer.token()
        if not t:
            break
        out.append(t)
    if not out or out[-1].type != 'eof':
        class _E: pass
        e = _E(); e.type = 'eof'; e.value = None; e.lexpos = -1
        out.append(e)
    return out

def print_tree(root: Node):
    """Imprime el árbol en ASCII (preorden)."""
    def rec(n: Node, prefix: str, is_last: bool):
        connector = "└─ " if is_last else "├─ "
        extra = ""
        if n.token_type and n.lexeme is not None:
            extra = f"  [{n.token_type}:{n.lexeme}]"
        print(prefix + connector + n.label + extra)
        new_prefix = prefix + ("   " if is_last else "│  ")
        for i, ch in enumerate(n.children):
            rec(ch, new_prefix, i == len(n.children) - 1)

    # raíz sin conector
    print(root.label)
    for i, ch in enumerate(root.children):
        rec(ch, "", i == len(root.children) - 1)

def to_dot(root: Node) -> str:
    lines = ["digraph ParseTree {", '  node [shape=box, fontname="Menlo"];']
    counter = {"i": 0}
    ids: Dict[Node, str] = {}

    def nid(n: Node) -> str:
        if n in ids:
            return ids[n]
        counter["i"] += 1
        ids[n] = f"n{counter['i']}"
        return ids[n]

    def esc(s: str) -> str:
        return s.replace('"', '\\"')

    def dfs(n: Node):
        label = n.label
        if n.token_type and n.lexeme is not None:
            label += f"\\n[{n.token_type}:{n.lexeme}]"
        lines.append(f'  {nid(n)} [label="{esc(label)}"];')
        for ch in n.children:
            lines.append(f'  {nid(n)} -> {nid(ch)};')
            dfs(ch)

    dfs(root)
    lines.append("}")
    return "\n".join(lines)

# ====== Parser LL(1) con árbol y trace =================================
def parse_with_tree(
    codigo: str,
    trazar_tabla: bool = True,
    widths: Optional[Tuple[int, int, int]] = None
) -> Tuple[bool, Node, List[Dict[str, Any]]]:
    """
    Devuelve: (ok, raiz_arbol, trace)
    trace: lista de eventos {"step","lookahead","stack","action":{...},"bufferIndex":i}
    """
    toks = _tokenize(codigo)
    stack: List[str] = ['eof', 'S']           
    root = Node('S')
    node_stack: List[Optional[Node]] = [None, root]  

    i = 0
    step = 1
    trace: List[Dict[str, Any]] = []

    if widths is None:
        total = max(get_terminal_size((140, 40)).columns - 4, 100)
        W = (int(total * 0.30), int(total * 0.50), total - int(total * 0.30) - int(total * 0.50))
        W = (max(W[0], 28), max(W[1], 50), max(W[2], 22))
    else:
        W = widths

    def emit(action: Dict[str, Any]):
        nonlocal step
        evt = {
            "step": step,
            "lookahead": toks[i].type if i < len(toks) else 'eof',
            "stack": list(stack),
            "action": action,
            "bufferIndex": i
        }
        trace.append(evt)
        step += 1

    def show_stack() -> str:
        return ' '.join(stack)

    if trazar_tabla:
        print(_format_row("Buffer", "Stack", "Acción", W))
        print(_format_row("-" * 6, "-" * 5, "-" * 6, W))

    while True:
        a = toks[i].type
        X = stack[-1]
        Xnode = node_stack[-1]

        # Aceptación
        if X == a == 'eof':
            if trazar_tabla:
                print(_format_row(a, show_stack(), "Aceptar", W))
            emit({"type": "accept"})
            return True, root, trace

        # Caso: X es terminal
        if X in tokens:
            if X == a:
                if trazar_tabla:
                    print(_format_row(a, show_stack(), f"match {X}", W))
                # Adjunta lexema/valor al nodo hoja
                if Xnode is not None:
                    Xnode.token_type = a
                    Xnode.lexeme = getattr(toks[i], "value", None)
                    if Xnode.lexeme is None:
                        Xnode.lexeme = toks[i].type
                emit({"type": "match", "symbol": X, "lexeme": getattr(toks[i], "value", None)})
                stack.pop(); node_stack.pop()
                i += 1
            else:
                msg = f"se esperaba '{X}' y llegó '{a}'"
                if trazar_tabla:
                    print(_format_row(a, show_stack(), f"[ERR] {msg}", W))
                emit({"type": "error", "message": msg})
                return False, root, trace
            continue

        # Caso: X es No Terminal -> buscar producción
        prod = INDEX.get((X, a))
        if prod is None:
            msg = f"no hay regla para M[{X}][{a}]"
            if trazar_tabla:
                print(_format_row(a, show_stack(), f"[ERR] {msg}", W))
            emit({"type": "error", "message": msg, "cell": [X, a]})
            return False, root, trace

        rhs = [] if prod == ['vacia'] else prod
        if trazar_tabla:
            pretty_rhs = 'ε' if not rhs else ' '.join(rhs)
            print(_format_row(a, show_stack(), f"{X} -> {pretty_rhs}", W))
        emit({"type": "expand", "A": X, "prod": rhs})

        # Construcción del árbol:
        parent = root if Xnode is None else Xnode
        children: List[Node] = []
        for sym in rhs:
            child = Node(sym)
            parent.add(child)
            children.append(child)

        # Reemplazar en pila de símbolos y pila de nodos
        stack.pop(); node_stack.pop()
        for k in range(len(rhs) - 1, -1, -1):
            stack.append(rhs[k])
            node_stack.append(children[k])

def _leer(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _expand_targets(targets: List[str]):
    """Admite archivos sueltos y carpetas; busca .c y .txt recursivamente."""
    seen = set()
    for t in targets:
        if os.path.isdir(t):
            for ext in ("*.c", "*.txt"):
                for p in glob.glob(os.path.join(t, "**", ext), recursive=True):
                    q = os.path.normpath(p)
                    if q not in seen:
                        seen.add(q); yield q
        else:
            q = os.path.normpath(t)
            if q not in seen:
                seen.add(q); yield q

if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Parser LL(1) con árbol: lee casos desde archivos/carpetas, imprime traza/árbol y exporta DOT."
    )
    ap.add_argument("targets", nargs="*", help="Archivos .c/.txt o carpetas con casos")
    ap.add_argument("--no-trace", action="store_true", help="Oculta la traza (Buffer/Stack/Acción)")
    ap.add_argument("--tree", action="store_true", help="Imprime el árbol ASCII")
    ap.add_argument("--dot", action="store_true", help="Exporta un .dot junto al archivo de entrada")
    args = ap.parse_args()

    targets = list(_expand_targets(args.targets)) if args.targets else []
    if not targets:
        # Demo mínimo si no se pasan archivos
        demo = "int a, b; a = (b + 3) * -2;"
        print(">> Demo (sin archivos):", demo)
        ok, raiz, _ = parse_with_tree(demo, trazar_tabla=not args.no_trace)
        print("\nResultado:", "OK" if ok else "FALLO")
        if args.tree:
            print("\nÁrbol de derivación (ASCII):")
            print_tree(raiz)
        if args.dot:
            out = "demo_tree.dot"
            with open(out, "w", encoding="utf-8") as f:
                f.write(to_dot(raiz))
            print(f"DOT -> {out}")
        sys.exit(0)

    exit_code = 0
    for path in targets:
        print("\n" + "=" * 80)
        print(f"Archivo: {path}")
        print("=" * 80)
        src = _leer(path)
        ok, raiz, _ = parse_with_tree(src, trazar_tabla=not args.no_trace)
        print("\nResultado:", "OK" if ok else "FALLO")

        if args.tree:
            print("\nÁrbol de derivación (ASCII):")
            print_tree(raiz)

        if args.dot:
            out = os.path.splitext(path)[0] + ".dot"
            with open(out, "w", encoding="utf-8") as f:
                f.write(to_dot(raiz))
            print(f"DOT -> {out}")

        if not ok:
            exit_code = 1

    sys.exit(exit_code)
