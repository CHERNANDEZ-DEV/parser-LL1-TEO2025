from lexer.lexer import tokenize
from parser.parser import parse
from ast.nodes import Program, FuncDecl

def test_parse_function_sum():
    src = """
    int sum(int n){
      int i = 0, acc = 0;
      for(i = 0; i < n; i = i + 1){
        acc = acc + i;
      }
      return acc;
    }
    """
    ast, errs = parse(tokenize(src))
    assert isinstance(ast, Program)
    assert not errs
    assert isinstance(ast.decls[0], FuncDecl)
