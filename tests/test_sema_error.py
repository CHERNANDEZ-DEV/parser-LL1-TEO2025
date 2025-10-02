from lexer.lexer import tokenize
from parser.parser import parse
from sema.checker import check

def test_undeclared_and_bad_call():
    src = """
    int f(int n){
      int acc = 0;
      acc = acc + x;   // x no declarada
      g(1,2,3);        // g no declarada
      return acc;
    }
    """
    ast, perrs = parse(tokenize(src))
    serrs = check(ast)
    assert any("no declarada" in e or "no-función" in e for e in serrs)

def test_array_index_type_and_assign():
    src = """
    int f(int n){
      int a[10];
      double d;
      a[1.5] = 2;   // índice no entero
      a = 3;        // array no asignable
      d = a;        // incompatible
      return n;
    }
    """
    ast, perrs = parse(tokenize(src))
    serrs = check(ast)
    joined = "\n".join(serrs)
    assert "Índice no entero" in joined
    assert ("no asignable" in joined) or ("incompatibles" in joined)
