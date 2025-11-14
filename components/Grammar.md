S           -> STMT_LIST
STMT_LIST   -> STMT STMT_LIST | ''

STMT        -> DECL | ASSIGN | IF_STMT | WHILE_STMT | FOR_STMT | BLOCK | EMPTY
EMPTY       -> ;

# --- Declaraciones (con inicialización) ---
DECL        -> TYPE INIT_LIST ;
TYPE        -> int | float | double | char
INIT_LIST   -> INIT INIT_TAIL
INIT_TAIL   -> , INIT INIT_TAIL | ''
INIT        -> id INIT_OPT
INIT_OPT    -> = EXPR | ''

# --- Asignaciones y bloque ---
ASSIGN      -> ASSIGN_CORE ;
ASSIGN_CORE -> id = EXPR
BLOCK       -> { STMT_LIST }

# --- if / while ---
IF_STMT     -> if ( EXPR ) STMT IF_TAIL
IF_TAIL     -> else STMT | ''
WHILE_STMT  -> while ( EXPR ) STMT

# --- for con declaración en el init ---
FOR_STMT    -> for ( FOR_INIT ; EXPR_OPT ; POST_OPT ) STMT
FOR_INIT    -> DECL_NO_SEMI | ASSIGN_CORE | ''
DECL_NO_SEMI-> TYPE INIT_LIST               # como DECL pero sin ';'
EXPR_OPT    -> EXPR | ''
POST_OPT    -> ASSIGN_CORE | ''

# --- Expresiones (precedencia: || < && < rel < + - < * / < unarios) ---
EXPR        -> OR_EXPR
OR_EXPR     -> AND_EXPR OR_EXPR_P
OR_EXPR_P   -> || AND_EXPR OR_EXPR_P | ''
AND_EXPR    -> REL_EXPR AND_EXPR_P
AND_EXPR_P  -> && REL_EXPR AND_EXPR_P | ''
REL_EXPR    -> ADD_EXPR REL_TAIL
REL_TAIL    -> == ADD_EXPR REL_TAIL
             | != ADD_EXPR REL_TAIL
             | <  ADD_EXPR REL_TAIL
             | <= ADD_EXPR REL_TAIL
             | >  ADD_EXPR REL_TAIL
             | >= ADD_EXPR REL_TAIL
             | ''
ADD_EXPR    -> MUL_EXPR ADD_TAIL
ADD_TAIL    -> + MUL_EXPR ADD_TAIL
             | - MUL_EXPR ADD_TAIL
             | ''
MUL_EXPR    -> UNARY MUL_TAIL
MUL_TAIL    -> * UNARY MUL_TAIL
             | / UNARY MUL_TAIL
             | ''
UNARY       -> ! UNARY
             | - UNARY
             | PRIMARY
PRIMARY     -> ( EXPR ) | id | num | str
