"""Base AST types"""

import enum
import typing

import attrs

from ..token_types import Token

__all__ = [
    "AccessModifierType",
    "CompareExprType",
    "ExtendedID",
    "Expr",
    "Value",
    "GlobalStmt",
    "Program",
    "MethodStmt",
    "BlockStmt",
    "InlineStmt",
    "MemberDecl",
]


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class AccessModifierType(enum.Enum):
    """Enumeration of valid access modifiers"""

    PRIVATE = 0
    PUBLIC = 1
    # using an enum because PUBLIC DEFAULT is two tokens
    PUBLIC_DEFAULT = 2


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class CompareExprType(enum.Enum):
    """Enumeration of valid operators that can appear
    in a comparison expresssion (CompareExpr)"""

    COMPARE_IS = 0
    COMPARE_ISNOT = 1
    COMPARE_GTEQ = 2
    COMPARE_EQGT = 3
    COMPARE_LTEQ = 4
    COMPARE_EQLT = 5
    COMPARE_GT = 6
    COMPARE_LT = 7
    COMPARE_LTGT = 8
    COMPARE_EQ = 9


@attrs.define(slots=False)
class ExtendedID:
    """Defined on grammar line 513"""

    id_token: Token


@attrs.define(slots=False)
class Expr:
    """Defined on grammar line 664

    &lt;ImpExpr&gt;
    """


@attrs.define(slots=False)
class Value(Expr):
    """Defined on grammar line 720

    &lt;ConstExpr&gt; | &lt;LeftExpr&gt; | { '(' &lt;Expr&gt; ')' }
    """


@attrs.define(slots=False)
class GlobalStmt:
    """Defined on grammar line 357

    Could be one of:
    - OptionExplicit
    - ClassDecl
    - FieldDecl
    - ConstDecl
    - SubDecl
    - FunctionDecl
    - BlockStmt
    """


@attrs.define
class Program:
    """The starting symbol for the VBScript grammar.
    Defined on grammar line 267

    Attributes
    ----------
    global_stmt_list : List[GlobalStmt], default=[]
    """

    global_stmt_list: typing.List[GlobalStmt] = attrs.field(default=attrs.Factory(list))


@attrs.define(slots=False)
class MethodStmt:
    """Defined on grammar line 365

    &lt;ConstDecl&gt; | &lt;BlockStmt&gt;
    """


@attrs.define(slots=False)
class BlockStmt(GlobalStmt, MethodStmt):
    """Defined on grammar line 368

    If InlineStmt, must be:
    &lt;InlineStmt&gt; &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class InlineStmt(BlockStmt):
    """Defined on grammar line 377"""


@attrs.define(slots=False)
class MemberDecl:
    """Defined on grammar line 278"""
