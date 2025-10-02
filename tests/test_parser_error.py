from lexer.lexer import tokenize
from parser.parser import parse

def test_error_recovery_missing_semi():
    src = """
    int x = 5
    int y = 6; // falta ; en la anterior línea
    """
    ast, errs = parse(tokenize(src))
    assert errs  # al menos un error
    assert len(ast.decls) >= 1
