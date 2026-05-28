"""Noeuds de l'arbre syntaxique (AST) pour le transpileur WLangage -> C#."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any


# ---- Expressions ----------------------------------------------------------

@dataclass
class Literal:
    value: Any          # valeur Python (int, float, str, bool)
    raw: str            # texte source d'origine
    kind: str           # 'int' | 'real' | 'string' | 'bool'


@dataclass
class Ident:
    name: str


@dataclass
class Unary:
    op: str
    operand: Any


@dataclass
class Binary:
    op: str
    left: Any
    right: Any


@dataclass
class Call:
    name: str
    args: List[Any] = field(default_factory=list)


@dataclass
class Member:
    target: Any
    name: str


@dataclass
class Index:
    target: Any
    index: Any


# ---- Instructions ---------------------------------------------------------

@dataclass
class VarDecl:
    name: str
    wl_type: Optional[str]
    init: Optional[Any]


@dataclass
class Assign:
    target: Any
    expr: Any


@dataclass
class ExprStmt:
    expr: Any


@dataclass
class If:
    cond: Any
    then_body: List[Any]
    else_body: Optional[List[Any]]


@dataclass
class For:
    var: str
    start: Any
    end: Any
    step: Optional[Any]
    body: List[Any]


@dataclass
class ForEach:
    var: str
    collection: Any
    body: List[Any]


@dataclass
class While:
    cond: Any
    body: List[Any]


@dataclass
class Loop:
    body: List[Any]


@dataclass
class Case:
    values: List[Any]
    body: List[Any]


@dataclass
class Switch:
    expr: Any
    cases: List[Case]
    default: Optional[List[Any]]


@dataclass
class Return:
    expr: Optional[Any]


@dataclass
class Break:
    pass


@dataclass
class Continue:
    pass


@dataclass
class Procedure:
    name: str
    params: List[Tuple[str, Optional[str]]]  # (nom, type WL)
    body: List[Any]
    return_type: Optional[str] = None        # type WL si annoté


@dataclass
class Comment:
    text: str


@dataclass
class Program:
    body: List[Any]
