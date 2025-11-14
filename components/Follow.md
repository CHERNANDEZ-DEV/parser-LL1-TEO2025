S: { $ }
STMT_LIST: { }, $ }
STMT: { int, float, double, char, id, if, while, for, {, ;, }, $, else }
EMPTY: { int, float, double, char, id, if, while, for, {, ;, }, $, else }

DECL: { int, float, double, char, id, if, while, for, {, ;, }, $, else }
TYPE: { id }
INIT_LIST: { ; }
INIT_TAIL: { ; }
INIT: { ,, ; }
INIT_OPT: { ,, ; }

ASSIGN: { int, float, double, char, id, if, while, for, {, ;, }, $, else }
ASSIGN_CORE: { ;, ) }
BLOCK: { int, float, double, char, id, if, while, for, {, ;, }, $, else }

IF_STMT: { int, float, double, char, id, if, while, for, {, ;, }, $, else }
IF_TAIL: { int, float, double, char, id, if, while, for, {, ;, }, $, else }
WHILE_STMT: { int, float, double, char, id, if, while, for, {, ;, }, $, else }

FOR_STMT: { int, float, double, char, id, if, while, for, {, ;, }, $, else }
FOR_INIT: { ; }
DECL_NO_SEMI: { ; }
EXPR_OPT: { ; }
POST_OPT: { ) }

EXPR: { ), ; }
OR_EXPR: { ), ; }
OR_EXPR_P: { ), ; }
AND_EXPR: { ||, ), ; }
AND_EXPR_P: { ||, ), ; }
REL_EXPR: { &&, ||, ), ; }
REL_TAIL: { &&, ||, ), ; }
ADD_EXPR: { ==, !=, <, <=, >, >=, &&, ||, ), ; }
ADD_TAIL: { ==, !=, <, <=, >, >=, &&, ||, ), ; }
MUL_EXPR: { +, -, ==, !=, <, <=, >, >=, &&, ||, ), ; }
MUL_TAIL: { +, -, ==, !=, <, <=, >, >=, &&, ||, ), ; }
UNARY: { *, /, +, -, ==, !=, <, <=, >, >=, &&, ||, ), ; }
PRIMARY: { *, /, +, -, ==, !=, <, <=, >, >=, &&, ||, ), ; }
