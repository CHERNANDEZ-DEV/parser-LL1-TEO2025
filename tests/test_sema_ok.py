from lexer.lexer import tokenize
from parser.parser import parse
from sema.checker import check

def test_sema_ok_sum():
    src = """
    int sum(int n){
      int acc = 0;
      for(acc = 0; acc < n; acc = acc + 1){}
      return acc;
    }
    """
    ast, perrs = parse(tokenize(src))
    assert not perrs
    serrs = check(ast)
    assert not serrs
