S: { int, float, double, char, id, if, while, for, {, ;, '' }
STMT_LIST: { int, float, double, char, id, if, while, for, {, ;, '' }
STMT: { int, float, double, char, id, if, while, for, {, ; }
EMPTY: { ; }

DECL: { int, float, double, char }
TYPE: { int, float, double, char }
INIT_LIST: { id }
INIT_TAIL: { ,, '' }
INIT: { id }
INIT_OPT: { =, '' }

ASSIGN: { id }
ASSIGN_CORE: { id }
BLOCK: { { }

IF_STMT: { if }
IF_TAIL: { else, '' }
WHILE_STMT: { while }

FOR_STMT: { for }
FOR_INIT: { int, float, double, char, id, '' }
DECL_NO_SEMI: { int, float, double, char }
EXPR_OPT: { (, id, num, str, !, -, '' }
POST_OPT: { id, '' }

EXPR: { (, id, num, str, !, - }
OR_EXPR: { (, id, num, str, !, - }
OR_EXPR_P: { ||, '' }
AND_EXPR: { (, id, num, str, !, - }
AND_EXPR_P: { &&, '' }
REL_EXPR: { (, id, num, str, !, - }
REL_TAIL: { ==, !=, <, <=, >, >=, '' }
ADD_EXPR: { (, id, num, str, !, - }
ADD_TAIL: { +, -, '' }
MUL_EXPR: { (, id, num, str, !, - }
MUL_TAIL: { *, /, '' }
UNARY: { !, -, (, id, num, str }
PRIMARY: { (, id, num, str }
