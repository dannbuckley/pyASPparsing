"""Base AST types"""

import enum
import inspect

__all__ = [
    "AccessModifierType",
    "CompareExprType",
    "Expr",
    "Value",
    "GlobalStmt",
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


class Expr:
    """Defined on grammar line 664

    &lt;ImpExpr&gt;
    """


class Value(Expr):
    """Defined on grammar line 720

    &lt;ConstExpr&gt; | &lt;LeftExpr&gt; | { '(' &lt;Expr&gt; ')' }
    """


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

    @classmethod
    def generate_global_stmt(cls):
        # get signature of derived class constructor
        sig: inspect.Signature = inspect.signature(cls)

        # iteratively receive constructor arguments
        init_kw = {}
        for param_name in sig.parameters.keys():
            init_kw[param_name] = yield

        # wait until caller is ready before returning
        yield

        # construct and return final class
        return cls(**init_kw)


class MethodStmt:
    """Defined on grammar line 365

    &lt;ConstDecl&gt; | &lt;BlockStmt&gt;
    """


class BlockStmt(GlobalStmt, MethodStmt):
    """Defined on grammar line 368

    If InlineStmt, must be:
    &lt;InlineStmt&gt; &lt;NEWLINE&gt;
    """


class InlineStmt(BlockStmt):
    """Defined on grammar line 377"""


class MemberDecl:
    """Defined on grammar line 278"""
