from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Union

# Tipos
@dataclass
class TypeSpec:
    base: str          # 'int' | 'char' | 'float' | 'double' | 'void'
    ptr_depth: int = 0 # número de '*'

@dataclass
class ArrayType:
    elem: Optional[TypeSpec]
    size: Optional[int]  # None si [] sin tamaño (p.ej., en params)

# Nodos del AST
@dataclass
class Program:
    decls: List["Decl"]

Decl = Union["FuncDecl", "VarDecl"]

@dataclass
class Param:
    type: TypeSpec
    name: str
    array: Optional[ArrayType] = None

@dataclass
class FuncDecl:
    ret_type: TypeSpec
    name: str
    params: List[Param]
    body: "Block"

@dataclass
class VarInit:
    name: str
    array: Optional[ArrayType]
    init: Optional["Expr"]

@dataclass
class VarDecl:
    type: TypeSpec
    inits: List[VarInit]

@dataclass
class Block:
    items: List[Union["Stmt", "Decl"]]

# Sentencias
@dataclass
class IfStmt:
    cond: "Expr"
    then: "Stmt"
    els: Optional["Stmt"]

@dataclass
class WhileStmt:
    cond: "Expr"
    body: "Stmt"

@dataclass
class ForStmt:
    init: Optional["Expr"]
    cond: Optional["Expr"]
    it: Optional["Expr"]
    body: "Stmt"

@dataclass
class ReturnStmt:
    expr: Optional["Expr"]

@dataclass
class ExprStmt:
    expr: Optional["Expr"]

Stmt = Union[Block, IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt]

# Expresiones
@dataclass
class Assign:
    left: "Expr"   # típicamente Var/Index (lvalue)
    right: "Expr"

@dataclass
class Binary:
    op: str
    left: "Expr"
    right: "Expr"

@dataclass
class Unary:
    op: str
    expr: "Expr"

@dataclass
class Call:
    callee: "Expr"
    args: List["Expr"]

@dataclass
class Index:
    array: "Expr"
    index: "Expr"

@dataclass
class Var:
    name: str

@dataclass
class Number:
    value: Union[int, float]

Expr = Union[Assign, Binary, Unary, Call, Index, Var, Number]
