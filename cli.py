from __future__ import annotations
import sys
from lexer.lexer import tokenize
from parser.parser import parse
from ast.pretty import _p
from sema.checker import check

EXAMPLE = r"""
int sum(int n){
  int i = 0, acc = 0;
  for(i = 0; i < n; i = i + 1){
    acc = acc + i;
  }
  return acc;
}
"""

def main(argv):
    if len(argv) > 1:
        with open(argv[1], 'r', encoding='utf-8') as f:
            src = f.read()
    else:
        src = EXAMPLE
    toks = tokenize(src)
    ast, parse_errs = parse(toks)
    sema_errs = check(ast)
    errs = parse_errs + sema_errs
    if errs:
        print("\n".join(errs), file=sys.stderr)
    print(_p(ast))

if __name__ == "__main__":
    main(sys.argv)
