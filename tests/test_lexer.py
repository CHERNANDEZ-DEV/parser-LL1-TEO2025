from lexer.lexer import tokenize
from lexer.tokens import TokenKind

def test_keywords_and_ops():
    code = "int x = a + b * 3; // comment\n"
    toks = tokenize(code)
    kinds = [t.kind for t in toks]
    assert TokenKind.KW_INT in kinds
    assert TokenKind.SEMI in kinds
    assert TokenKind.PLUS in kinds and TokenKind.STAR in kinds
